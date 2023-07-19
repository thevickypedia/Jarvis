import os
import time
import traceback
from datetime import datetime
from multiprocessing import Process, Queue
from threading import Thread, Timer
from typing import AnyStr, List, NoReturn, Union

import requests
from deepdiff import DeepDiff
from pydantic import HttpUrl

from jarvis.executors import (alarm, automation, background_task, conditions,
                              controls, crontab, listener_controls, others,
                              remind, weather_monitor, word_match)
from jarvis.modules.auth_bearer import BearerAuth
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.meetings import events, ics_meetings
from jarvis.modules.models import classes, models
from jarvis.modules.utils import shared, support, util

db = database.Database(database=models.fileio.base_db)


def background_tasks() -> NoReturn:
    """Initiate the runner function for background tasks."""
    try:
        background_task_runner()
    except Exception as error:
        logger.critical("ATTENTION: %s", error.__str__())
        controls.restart_control(quiet=True)


def background_task_runner() -> NoReturn:
    """Trigger for background tasks, cron jobs, automation, alarms, reminders, events and meetings sync."""
    config.multiprocessing_logger(filename=os.path.join('logs', 'background_tasks_%d-%m-%Y.log'))
    # Since env vars are loaded only during startup, validate weather alert only then
    automation.validate_weather_alert()
    tasks: List[classes.BackgroundTask] = list(background_task.validate_tasks())
    meeting_muter = []
    if models.settings.os == models.supported_platforms.macOS:
        events.event_app_launcher()
    start_events = start_meetings = start_cron = time.time()
    task_dict = {i: time.time() for i in range(len(tasks))}  # Creates a start time for each task
    dry_run = True
    smart_listener = Queue()
    while True:
        now = datetime.now()
        # Trigger background tasks
        for i, task in enumerate(tasks):
            if task_dict[i] + task.seconds <= time.time() or dry_run:  # Checks a particular tasks' elapsed time
                task_dict[i] = time.time()  # Updates that particular tasks' start time
                if now.hour in task.ignore_hours:
                    logger.debug("'%s' skipped honoring ignore hours", task)
                else:
                    logger.debug("Executing: '%s'", task.task)
                    try:
                        response = offline_communicator(command=task.task) or "No response for background task"
                        logger.debug("Response: '%s'", response)
                    except Exception as error:
                        logger.error(error)
                        logger.warning("Removing %s from background tasks.", task)
                        background_task.remove_corrupted(task=task)

        # Trigger cron jobs once during start up (regardless of schedule) and follow schedule after that
        if start_cron + 60 <= time.time() or dry_run:  # Condition passes every minute
            start_cron = time.time()
            for job in models.env.crontab:
                if job.check_trigger() or dry_run:
                    if dry_run:
                        logger.info("Executing cron job: '%s' during startup", job.comment)
                    else:
                        logger.debug("Executing cron job: '%s'", job.comment)
                    cron_process = Process(target=crontab.crontab_executor, args=(job.comment,))
                    cron_process.start()
                    with db.connection:
                        cursor = db.connection.cursor()
                        cursor.execute("INSERT or REPLACE INTO children (crontab) VALUES (?);", (cron_process.pid,))
                        db.connection.commit()

        # Trigger automation
        if os.path.isfile(models.fileio.automation):
            if exec_task := automation.auto_helper():
                # Check and trigger weather alert monitoring system
                if "weather" in exec_task.lower():
                    # run as daemon and not store in children table as this won't take long
                    logger.debug("Initiating weather alert monitor")
                    Process(target=weather_monitor.monitor, daemon=True).start()
                else:
                    logger.debug("Executing: '%s'", exec_task)
                    try:
                        response = offline_communicator(command=exec_task) or "No response for automated task"
                        logger.debug("Response: '%s'", response)
                    except Exception as error:
                        logger.error(error)
                        logger.error(traceback.format_exc())

        # Sync events from the event app specified (calendar/outlook)
        # Run either for macOS or during the initial run so the response gets stored in the DB
        if dry_run or models.settings.os == models.supported_platforms.macOS:
            if (models.env.sync_events and start_events + models.env.sync_events <= time.time()) or dry_run:
                start_events = time.time()
                event_process = Process(target=events.events_writer)
                logger.info("Getting events from %s.", models.env.event_app) if dry_run else None
                event_process.start()
                with db.connection:
                    cursor = db.connection.cursor()
                    cursor.execute("UPDATE children SET events=null")
                    cursor.execute("INSERT or REPLACE INTO children (events) VALUES (?);", (event_process.pid,))
                    db.connection.commit()

        # Sync meetings from the ICS url provided
        # Run either when an ICS url is present or during the initial run so the response gets stored in the DB
        if dry_run or models.env.ics_url:
            if dry_run and models.env.ics_url:
                try:
                    if requests.get(url=models.env.ics_url).status_code == 503:
                        models.env.sync_meetings = 21_600  # Set to 6 hours if unable to connect to the meetings URL
                except EgressErrors as error:
                    logger.error(error)
                    models.env.sync_meetings = None  # NEVER RUNs, as env vars are loaded only during start up
            if (models.env.sync_meetings and start_meetings + models.env.sync_meetings <= time.time()) or dry_run:
                start_meetings = time.time()
                meeting_process = Process(target=ics_meetings.meetings_writer, args=(smart_listener,))
                logger.info("Getting meetings from ICS.") if dry_run else None
                meeting_process.start()
                with db.connection:
                    cursor = db.connection.cursor()
                    cursor.execute("UPDATE children SET meetings=null")
                    cursor.execute("INSERT or REPLACE INTO children (meetings) VALUES (?);", (meeting_process.pid,))
                    db.connection.commit()

        # Mute during meetings
        if models.env.mute_for_meetings and models.env.ics_url:
            while not smart_listener.empty():
                mutes = smart_listener.get(timeout=2)
                logger.debug(mutes)
                meeting_muter.append(mutes)  # Write to a new list as queue will be empty after executing .get
            if meeting_muter := util.remove_duplicates(input_=meeting_muter):
                for each_muter in meeting_muter:
                    for meeting_name, timing_info in each_muter.items():
                        meeting_time = timing_info[0]
                        duration = timing_info[1]
                        if meeting_time == now.strftime("%I:%M %p"):
                            logger.info("Disabling listener for the meeting '%s'. Will be enabled after %s",
                                        meeting_name, support.time_converter(second=duration))
                            meeting_muter.remove(each_muter)  # Remove event from new list to avoid repetition
                            listener_controls.put_listener_state(state=False)
                            Timer(function=listener_controls.put_listener_state, interval=duration,
                                  kwargs=dict(state=True)).start()

        # Trigger alarms
        if alarm_state := support.lock_files(alarm_files=True):
            for each_alarm in alarm_state:
                if each_alarm == now.strftime("%I_%M_%p.lock") or \
                        each_alarm == now.strftime("%I_%M_%p_repeat.lock") or \
                        each_alarm == now.strftime("%A_%I_%M_%p_repeat.lock"):
                    Process(target=alarm.executor).start()
                    if each_alarm.endswith("_repeat.lock"):
                        os.rename(os.path.join("alarm", each_alarm), os.path.join("alarm", f"_{each_alarm}"))
                    else:
                        os.remove(os.path.join("alarm", each_alarm))
                elif each_alarm.startswith('_') and not \
                        (each_alarm == now.strftime("_%I_%M_%p_repeat.lock") or
                         each_alarm == now.strftime("_%A_%I_%M_%p_repeat.lock")):
                    os.rename(os.path.join("alarm", each_alarm), os.path.join("alarm", each_alarm.lstrip("_")))

        # Trigger reminders
        if reminder_files := support.lock_files(reminder_files=True):
            for reminder_file in reminder_files:
                each_reminder = reminder_file.split('|')
                if len(each_reminder) == 3:
                    remind_time, remind_msg, name = each_reminder
                else:
                    remind_time, remind_msg = each_reminder
                    name = None
                if name:
                    name = name.replace('.lock', '').replace('_', ' ')
                else:
                    remind_msg = remind_msg.replace('.lock', '')
                remind_msg = remind_msg.replace('_', ' ')
                if remind_time == now.strftime("%I_%M_%p"):
                    logger.info("Executing reminder: %s", each_reminder)
                    Thread(target=remind.executor, kwargs={'message': remind_msg, 'contact': name}).start()
                    os.remove(os.path.join("reminder", reminder_file))

        # Re-check for any newly added tasks with logger disabled
        new_tasks: List[classes.BackgroundTask] = list(background_task.validate_tasks(log=False))
        if new_tasks != tasks:
            logger.warning("Tasks list has been updated.")
            logger.info(DeepDiff(tasks, new_tasks, ignore_order=True))
            tasks = new_tasks
            task_dict = {i: time.time() for i in range(len(tasks))}  # Re-create start time for each task

        dry_run = False
        time.sleep(0.5)  # Reduces CPU utilization as constant fileIO operations spike CPU %


def get_tunnel() -> Union[HttpUrl, NoReturn]:
    """Checks for any active public URL tunneled using Ngrok.

    Returns:
        HttpUrl:
        Ngrok public URL.
    """
    try:
        response = requests.get(url="http://localhost:4040/api/tunnels")
        if response.ok:
            tunnels = response.json().get('tunnels', [])
            protocols = list(filter(None, [tunnel.get('proto') for tunnel in tunnels]))
            for tunnel in tunnels:
                if 'https' in protocols and tunnel.get('proto') != 'https':
                    continue
                if hosted := tunnel.get('config', {}).get('addr'):
                    if int(hosted.split(':')[-1]) == models.env.offline_port:
                        return tunnel.get('public_url')
    except EgressErrors + (requests.JSONDecodeError,) as error:
        logger.error(error)


def tunneling() -> NoReturn:
    """Initiates Ngrok to tunnel requests from external sources if they aren't running already.

    Notes:
        - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the given offline port.
        - The connection is tunneled through a public facing URL used to make ``POST`` requests to Jarvis API.
    """
    # processName filter is not added since process runs on a single function that is covered by funcName
    config.multiprocessing_logger(filename=os.path.join('logs', 'tunnel_%d-%m-%Y.log'))
    if models.settings.os != models.supported_platforms.macOS:
        return

    if get_tunnel():
        logger.info('An instance of ngrok tunnel for offline communicator is running already.')
        return

    if os.path.exists(f"{models.env.home}/JarvisHelper/venv/bin/activate"):
        logger.info("Initiating ngrok connection for offline communicator.")
        initiate = f'cd {models.env.home}/JarvisHelper && ' \
                   f'source venv/bin/activate && export HOST={models.env.offline_host} ' \
                   f'export PORT={models.env.offline_port} && python forever_ngrok.py'
        os.system(f"""osascript -e 'tell application "Terminal" to do script "{initiate}"' > /dev/null""")
    else:
        logger.info("JarvisHelper is not available to trigger an ngrok tunneling through %d", models.env.offline_port)
        endpoint = rf'http://{models.env.offline_host}:{models.env.offline_port}'
        logger.info('However offline communicator can still be accessed via '
                    '%s/offline-communicator for API calls and %s/docs for docs.', endpoint, endpoint)


def ondemand_offline_automation(task: str) -> Union[str, None]:
    """Makes a ``POST`` call to offline-communicator to execute a said task.

    Args:
        task: Takes the command to be executed as an argument.

    Returns:
        str:
        Returns the response if request was successful.
    """
    try:
        response = requests.post(url=f'http://{models.env.offline_host}:{models.env.offline_port}/offline-communicator',
                                 json={'command': task}, auth=BearerAuth(token=models.env.offline_pass))
    except EgressErrors:
        return
    if response.ok:
        return response.json()['detail'].split('\n')[-1]


def offline_communicator(command: str) -> Union[AnyStr, HttpUrl]:
    """Initiates conditions after flipping ``status`` flag in ``called_by_offline`` dict which suppresses the speaker.

    Args:
        command: Takes the command that has to be executed as an argument.

    Returns:
        AnyStr:
        Response from Jarvis.
    """
    shared.called_by_offline = True
    # Specific for offline communication and not needed for live conversations
    if word_match.word_match(phrase=command, match_list=keywords.keywords['ngrok']):
        if public_url := get_tunnel():
            return public_url
        else:
            raise LookupError("Failed to retrieve the public URL")
    if word_match.word_match(phrase=command, match_list=keywords.keywords['photo']):
        return others.photo()
    # Call condition instead of split_phrase as the 'and' and 'also' filter will overwrite the first response
    conditions.conditions(phrase=command)
    shared.called_by_offline = False
    if response := shared.text_spoken:
        shared.text_spoken = None
        return response
    else:
        logger.error("Offline request failed for '%s'", command)
        return f"I was unable to process the request: {command}"
