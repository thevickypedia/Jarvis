import os
import time
import traceback
from datetime import datetime
from multiprocessing import Process, Queue
from threading import Thread, Timer
from typing import AnyStr, List

import requests
from deepdiff import DeepDiff
from pydantic import HttpUrl

from jarvis.executors import (
    alarm,
    automation,
    background_task,
    conditions,
    controls,
    crontab,
    files,
    internet,
    listener_controls,
    others,
    remind,
    resource_tracker,
    weather_monitor,
    word_match,
)
from jarvis.modules.auth_bearer import BearerAuth
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.meetings import events, ics_meetings
from jarvis.modules.models import classes, enums, models
from jarvis.modules.utils import shared, support, util


def background_tasks() -> None:
    """Initiate the runner function for background tasks."""
    try:
        background_task_runner()
    except Exception as error:
        logger.critical("ATTENTION: %s", error.__str__())
        controls.restart_control(quiet=True)


def background_task_runner() -> None:
    """Trigger for background tasks, cron jobs, automation, alarms, reminders, events and meetings sync."""
    multiprocessing_logger(
        filename=os.path.join("logs", "background_tasks_%d-%m-%Y.log")
    )
    # Since env vars are loaded only during startup, validate weather alert only then
    automation.validate_weather_alert()
    if all((models.env.wifi_ssid, models.env.wifi_password)):
        wifi_checker = classes.WiFiConnection()
    else:
        wifi_checker = None
    tasks: List[classes.BackgroundTask] = list(background_task.validate_tasks())
    cron_jobs: List[crontab.expression.CronExpression] = list(crontab.validate_jobs())
    meeting_muter = []
    start_events = start_meetings = start_cron = start_wifi = time.time()
    task_dict = {
        i: time.time() for i in range(len(tasks))
    }  # Creates a start time for each task
    dry_run = True
    smart_listener = Queue()
    while True:
        now = datetime.now()
        # Trigger background tasks
        for i, task in enumerate(tasks):
            # Checks a particular tasks' elapsed time
            if task_dict[i] + task.seconds <= time.time() or dry_run:
                # Updates that particular tasks' start time
                task_dict[i] = time.time()
                if now.hour in task.ignore_hours:
                    logger.debug("'%s' skipped honoring ignore hours", task)
                else:
                    logger.debug("Executing: '%s'", task.task)
                    try:
                        response = (
                            offline_communicator(task.task, True)
                            or "No response for background task"
                        )
                        logger.debug("Response: '%s'", response)
                    except Exception as error:
                        logger.error(error)
                        logger.warning("Removing %s from background tasks.", task)
                        background_task.remove_corrupted(task=task)

        # Trigger cron jobs once during start up (regardless of schedule) and follow schedule after that
        if start_cron + 60 <= time.time():  # Condition passes every minute
            start_cron = time.time()
            for job in cron_jobs:
                if job.check_trigger():
                    logger.debug("Executing cron job: '%s'", job.comment)
                    cron_process = Process(target=crontab.executor, args=(job.comment,))
                    cron_process.start()
                    with models.db.connection as connection:
                        cursor = connection.cursor()
                        cursor.execute(
                            "INSERT or REPLACE INTO children (crontab) VALUES (?);",
                            (cron_process.pid,),
                        )
                        connection.commit()

        # Trigger wifi checker
        if wifi_checker and (
            start_wifi + models.env.connection_retry <= time.time() or dry_run
        ):
            start_wifi = time.time()
            logger.debug("Initiating WiFi connection checker")
            wifi_checker = connection.wifi(wifi_checker)

        # Trigger automation
        if exec_task := automation.auto_helper():
            # Check and trigger weather alert monitoring system
            if "weather" in exec_task.lower():
                # run as daemon and not store in children table as this won't take long
                logger.debug("Initiating weather alert monitor")
                resource_tracker.semaphores(weather_monitor.monitor)
            else:
                logger.debug("Executing: '%s'", exec_task)
                try:
                    response = (
                        offline_communicator(command=exec_task)
                        or "No response for automated task"
                    )
                    logger.debug("Response: '%s'", response)
                except Exception as error:
                    logger.error(error)
                    logger.error(traceback.format_exc())

        # Sync events from the event app specified (calendar/outlook)
        # Run either for macOS or during the initial run so the response gets stored in the DB
        if dry_run or models.settings.os == enums.SupportedPlatforms.macOS:
            if (
                models.env.sync_events
                and start_events + models.env.sync_events <= time.time()
            ) or dry_run:
                start_events = time.time()
                event_process = Process(target=events.events_writer)
                logger.info(
                    "Getting events from %s.", models.env.event_app
                ) if dry_run else None
                event_process.start()
                with models.db.connection as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE children SET events=null")
                    cursor.execute(
                        "INSERT or REPLACE INTO children (events) VALUES (?);",
                        (event_process.pid,),
                    )
                    connection.commit()

        # Sync meetings from the ICS url provided
        # Run either when an ICS url is present or during the initial run so the response gets stored in the DB
        if dry_run or models.env.ics_url:
            if dry_run and models.env.ics_url:
                try:
                    if requests.get(url=models.env.ics_url).status_code == 503:
                        models.env.sync_meetings = 21_600  # Set to 6 hours if unable to connect to the meetings URL
                except EgressErrors as error:
                    logger.error(error)
                    models.env.sync_meetings = (
                        None  # NEVER RUNs, as env vars are loaded only during start up
                    )
            if (
                models.env.sync_meetings
                and start_meetings + models.env.sync_meetings <= time.time()
            ) or dry_run:
                start_meetings = time.time()
                meeting_process = Process(
                    target=ics_meetings.meetings_writer, args=(smart_listener,)
                )
                logger.info("Getting meetings from ICS.") if dry_run else None
                meeting_process.start()
                with models.db.connection as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE children SET meetings=null")
                    cursor.execute(
                        "INSERT or REPLACE INTO children (meetings) VALUES (?);",
                        (meeting_process.pid,),
                    )
                    connection.commit()

        # Mute during meetings
        if models.env.mute_for_meetings and models.env.ics_url:
            while not smart_listener.empty():
                mutes = smart_listener.get(timeout=2)
                logger.debug(mutes)
                # Write to a new list as queue will be empty after executing .get
                meeting_muter.append(mutes)
            if meeting_muter := util.remove_duplicates(input_=meeting_muter):
                for each_muter in meeting_muter:
                    for meeting_name, timing_info in each_muter.items():
                        meeting_time = timing_info[0]
                        duration = timing_info[1]
                        if meeting_time == now.strftime("%I:%M %p"):
                            logger.info(
                                "Disabling listener for the meeting '%s'. Will be enabled after %s",
                                meeting_name,
                                support.time_converter(second=duration),
                            )
                            # Remove event from new list to avoid repetition
                            meeting_muter.remove(each_muter)
                            listener_controls.put_listener_state(state=False)
                            Timer(
                                function=listener_controls.put_listener_state,
                                interval=duration,
                                kwargs=dict(state=True),
                            ).start()

        # Trigger alarms
        if alarms := files.get_alarms():
            copied_alarms = alarms.copy()
            for alarmer in alarms:
                # alarms match 'time' and 'day' of alarm
                if alarmer["alarm_time"] == now.strftime("%I:%M %p") and alarmer.get(
                    "day", datetime.now().strftime("%A")
                ) == datetime.now().strftime("%A"):
                    logger.info("Executing alarm: %s", alarmer)
                    resource_tracker.semaphores(alarm.executor)
                    if not alarmer["repeat"]:
                        copied_alarms.remove(alarmer)
            if copied_alarms != alarms:
                files.put_alarms(data=copied_alarms)

        # Trigger reminders
        if reminders := files.get_reminders():
            copied_reminders = reminders.copy()
            for reminder in reminders:
                # reminders match the 'time' and 'date' of reminder
                if (
                    reminder["reminder_time"] == now.strftime("%I:%M %p")
                    and reminder["date"] == datetime.now().date()
                ):
                    logger.info("Executing reminder: %s", reminder)
                    Thread(
                        target=remind.executor,
                        kwargs={
                            "message": reminder["message"],
                            "contact": reminder["name"],
                        },
                    ).start()
                    copied_reminders.remove(reminder)
            if copied_reminders != reminders:
                files.put_reminders(data=copied_reminders)

        # Re-check for any newly added tasks with logger disabled
        new_tasks: List[classes.BackgroundTask] = list(
            background_task.validate_tasks(log=False)
        )
        if new_tasks != tasks:
            logger.warning("Tasks list has been updated.")
            logger.info(DeepDiff(tasks, new_tasks, ignore_order=True))
            tasks = new_tasks
            # Re-create start time for each task
            task_dict = {i: time.time() for i in range(len(tasks))}

        # Re-check for any newly added cron_jobs with logger disabled
        new_cron_jobs: List[crontab.expression.CronExpression] = list(
            crontab.validate_jobs(log=False)
        )
        if new_cron_jobs != cron_jobs:
            # Don't log updated jobs since there will always be a difference when run on author mode
            cron_jobs = new_cron_jobs
        dry_run = False
        # Reduces CPU utilization as constant fileIO operations spike CPU %
        time.sleep(1)


def ondemand_offline_automation(task: str) -> str | None:
    """Makes a ``POST`` call to offline-communicator to execute a said task.

    Args:
        task: Takes the command to be executed as an argument.

    Returns:
        str:
        Returns the response if request was successful.
    """
    try:
        response = requests.post(
            url=f"http://{models.env.offline_host}:{models.env.offline_port}/offline-communicator",
            json={"command": task},
            auth=BearerAuth(token=models.env.offline_pass),
        )
    except EgressErrors:
        return
    if response.ok:
        return response.json()["detail"].split("\n")[-1]


def offline_communicator(command: str, bg_flag: bool = False) -> AnyStr | HttpUrl:
    """Initiates conditions after flipping ``status`` flag in ``called_by_offline`` dict which suppresses the speaker.

    Args:
        command: Takes the command that has to be executed as an argument.
        bg_flag: Takes the background flag caller as an argument.

    Returns:
        AnyStr:
        Response from Jarvis.
    """
    shared.called_by_offline = True
    shared.called_by_bg_tasks = bg_flag
    # Specific for offline communication and not needed for live conversations
    if word_match.word_match(phrase=command, match_list=keywords.keywords["ngrok"]):
        if public_url := internet.get_tunnel():
            return public_url
        else:
            raise LookupError("Failed to retrieve the public URL")
    if word_match.word_match(phrase=command, match_list=keywords.keywords["photo"]):
        return others.photo()
    # Call condition instead of split_phrase as the 'and' and 'also' filter will overwrite the first response
    conditions.conditions(phrase=command)
    shared.called_by_offline = False
    shared.called_by_bg_tasks = False
    if response := shared.text_spoken:
        shared.text_spoken = None
        return response
    else:
        logger.error("Offline request failed for '%s'", command)
        return f"I was unable to process the request: {command}"
