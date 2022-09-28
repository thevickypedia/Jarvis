import os
import time
from datetime import datetime
from multiprocessing import Process
from threading import Thread
from typing import AnyStr, List, NoReturn, Union

import requests
from pydantic import HttpUrl

from executors.alarm import alarm_executor
from executors.automation import auto_helper
from executors.conditions import conditions
from executors.crontab import crontab_executor
from executors.logger import logger
from executors.remind import reminder_executor
from executors.word_match import word_match
from modules.auth_bearer import BearerAuth
from modules.conditions import keywords
from modules.crontab import expression
from modules.database import database
from modules.meetings import events, icalendar
from modules.models import models
from modules.offline import compatibles
from modules.timer.executor import RepeatedTimer
from modules.utils import shared, support

db = database.Database(database=models.fileio.base_db)
offline_compatible = compatibles.offline_compatible()


def repeated_tasks() -> Union[List[RepeatedTimer], List]:
    """Runs tasks on a timed basis.

    Returns:
        list:
        Returns a list of RepeatedTimer object(s).
    """
    tasks = []
    logger.info(f"Background tasks: {len(models.env.tasks)}")
    for task in models.env.tasks:
        if word_match(phrase=task.task, match_list=offline_compatible):
            tasks.append(RepeatedTimer(task.seconds, offline_communicator, task.task))
        else:
            logger.error(f"{task.task} is not a part of offline communication. Removing entry.")
            models.env.tasks.remove(task)
    return tasks


def automator() -> NoReturn:
    """Place for long-running background tasks.

    See Also:
        - The automation file should be a dictionary within a dictionary that looks like the below:

            .. code-block:: yaml

                6:00 AM:
                  task: set my bedroom lights to 50%
                9:00 PM:
                  task: set my bedroom lights to 5%

        - Jarvis creates/swaps a ``status`` flag upon execution, so that it doesn't repeat execution within a minute.
    """
    offline_list = offline_compatible + keywords.restart_control
    start_events = start_meetings = start_cron = time.time()
    events.event_app_launcher() if models.settings.macos else None
    dry_run = True
    while True:
        if os.path.isfile(models.fileio.automation):
            if exec_task := auto_helper(offline_list=offline_list):
                try:
                    offline_communicator(command=exec_task)
                except Exception as error:
                    logger.error(error)

        if start_events + models.env.sync_events <= time.time() or dry_run:
            start_events = time.time()
            event_process = Process(target=events.events_writer)
            logger.info(f"Getting calendar events from {models.env.event_app}") if dry_run else None
            event_process.start()
            with db.connection:
                cursor = db.connection.cursor()
                cursor.execute("UPDATE children SET events=null")
                cursor.execute("INSERT or REPLACE INTO children (events) VALUES (?);", (event_process.pid,))
                db.connection.commit()

        if start_meetings + models.env.sync_meetings <= time.time() or dry_run:
            if dry_run and models.env.ics_url:
                try:
                    if requests.get(url=models.env.ics_url).status_code == 503:
                        models.env.sync_meetings = 21_600  # Set to 6 hours if unable to connect to the meetings URL
                except (ConnectionError, TimeoutError, requests.exceptions.RequestException,
                        requests.exceptions.Timeout) as error:
                    logger.error(error)
                    models.env.sync_meetings = 99_999_999  # NEVER RUNs, as env vars are loaded only during start up
            start_meetings = time.time()
            meeting_process = Process(target=icalendar.meetings_writer)
            logger.info("Getting calendar schedule from ICS.") if dry_run else None
            meeting_process.start()
            with db.connection:
                cursor = db.connection.cursor()
                cursor.execute("UPDATE children SET meetings=null")
                cursor.execute("INSERT or REPLACE INTO children (meetings) VALUES (?);", (meeting_process.pid,))
                db.connection.commit()

        if start_cron + 60 <= time.time():  # Condition passes every minute
            start_cron = time.time()
            for cron in models.env.crontab:
                job = expression.CronExpression(line=cron)
                if job.check_trigger(date_tuple=tuple(map(int, datetime.now().strftime("%Y,%m,%d,%H,%M").split(",")))):
                    cron_process = Process(target=crontab_executor, args=(job.comment,))
                    cron_process.start()
                    with db.connection:
                        cursor = db.connection.cursor()
                        cursor.execute("INSERT or REPLACE INTO children (crontab) VALUES (?);", (cron_process.pid,))
                        db.connection.commit()

        if alarm_state := support.lock_files(alarm_files=True):
            for each_alarm in alarm_state:
                if each_alarm == datetime.now().strftime("%I_%M_%p.lock") or \
                        each_alarm == datetime.now().strftime("%I_%M_%p_repeat.lock") or \
                        each_alarm == datetime.now().strftime("%A_%I_%M_%p_repeat.lock"):
                    Process(target=alarm_executor).start()
                    if each_alarm.endswith("_repeat.lock"):
                        os.rename(os.path.join("alarm", each_alarm), os.path.join("alarm", f"_{each_alarm}"))
                    else:
                        os.remove(os.path.join("alarm", each_alarm))
                elif each_alarm.startswith('_') and not \
                        (each_alarm == datetime.now().strftime("_%I_%M_%p_repeat.lock") or
                         each_alarm == datetime.now().strftime("_%A_%I_%M_%p_repeat.lock")):
                    os.rename(os.path.join("alarm", each_alarm), os.path.join("alarm", each_alarm.lstrip("_")))
        if reminder_state := support.lock_files(reminder_files=True):
            for each_reminder in reminder_state:
                remind_time, remind_msg = each_reminder.split('|')
                remind_msg = remind_msg.rstrip('.lock').replace('_', ' ')
                if remind_time == datetime.now().strftime("%I_%M_%p"):
                    Thread(target=reminder_executor, args=[remind_msg]).start()
                    os.remove(os.path.join("reminder", each_reminder))

        dry_run = False


def get_tunnel() -> Union[HttpUrl, NoReturn]:
    """Checks for any active public URL tunneled using Ngrok.

    Returns:
        HttpUrl:
        Ngrok public URL.
    """
    try:
        response = requests.get(url="http://localhost:4040/api/tunnels")
        if response.ok:
            for each_tunnel in response.json().get('tunnels', {}):
                if hosted := each_tunnel.get('config', {}).get('addr'):
                    if int(hosted.split(':')[-1]) == models.env.offline_port:
                        return each_tunnel.get('public_url')
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, ConnectionError, TimeoutError,
            requests.exceptions.JSONDecodeError) as error:
        logger.error(error)


def initiate_tunneling() -> NoReturn:
    """Initiates Ngrok to tunnel requests from external sources if they aren't running already.

    Notes:
        - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the given offline port.
        - The connection is tunneled through a public facing URL used to make ``POST`` requests to Jarvis API.
    """
    if not models.settings.macos:
        return

    if get_tunnel():
        logger.info('An instance of ngrok tunnel for offline communicator is running already.')
        return

    if os.path.exists(f"{models.env.home}/JarvisHelper/venv/bin/activate"):
        logger.info('Initiating ngrok connection for offline communicator.')
        initiate = f'cd {models.env.home}/JarvisHelper && ' \
                   f'source venv/bin/activate && export host={models.env.offline_host} ' \
                   f'export PORT={models.env.offline_port} && python forever_ngrok.py'
        os.system(f"""osascript -e 'tell application "Terminal" to do script "{initiate}"' > /dev/null""")
    else:
        logger.info(f'JarvisHelper is not available to trigger an ngrok tunneling through {models.env.offline_port}')
        endpoint = rf'http:\\{models.env.offline_host}:{models.env.offline_port}'
        logger.info('However offline communicator can still be accessed via '
                    f'{endpoint}\\offline-communicator for API calls and {endpoint}\\docs for docs.')


def on_demand_offline_automation(task: str) -> Union[str, None]:
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
    except (ConnectionError, TimeoutError, requests.exceptions.RequestException, requests.exceptions.Timeout):
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
    if word_match(phrase=command, match_list=keywords.ngrok):
        if public_url := get_tunnel():
            return public_url
        else:
            raise LookupError("Failed to retrieve the public URL")
    conditions(phrase=command, should_return=True)
    shared.called_by_offline = False
    if response := shared.text_spoken:
        shared.text_spoken = None
        return response
    else:
        logger.error(f"Offline request failed: {shared.text_spoken}")
        return f"I was unable to process the request: {command}"
