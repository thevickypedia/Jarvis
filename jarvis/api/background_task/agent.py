import time
import traceback
from datetime import datetime
from multiprocessing import Process
from threading import Thread
from typing import Dict
from typing import List

import requests

from jarvis.executors import (
    background_task,
    files,
    alarm,
    crontab,
    remind,
    offline,
    resource_tracker,
    weather_monitor,
)
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.meetings import events, ics_meetings
from jarvis.modules.models import classes, models


async def init_meetings() -> None:
    if models.env.ics_url:
        try:
            if requests.get(url=models.env.ics_url).status_code == 503:
                models.env.sync_meetings = 21_600  # Set to 6 hours if unable to connect to the meetings URL
        except EgressErrors as error:
            logger.error(error)
            # NEVER RUNs, as env vars are loaded only during start up
            models.env.sync_meetings = None


async def background_executor(tasks: List[classes.BackgroundTask], task_dict: Dict[int, float], now: datetime) -> None:
    # MARK: Trigger background tasks
    for i, task in enumerate(tasks):
        # Checks a particular tasks' elapsed time
        if task_dict[i] + task.seconds <= time.time():
            # Updates that particular tasks' start time
            task_dict[i] = time.time()
            if now.hour in task.ignore_hours:
                logger.debug("'%s' skipped honoring ignore hours", task)
            else:
                logger.debug("Executing: '%s'", task.task)
                try:
                    response = (
                            offline.communicator(task.task, True)
                            or "No response for background task"
                    )
                    logger.debug("Response: '%s'", response)
                except Exception as error:
                    logger.error(error)
                    logger.warning("Removing %s from background tasks.", task)
                    background_task.remove_corrupted(task=task)


async def crontab_executor(cron_jobs: List[crontab.expression.CronExpression]) -> None:
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


async def automation_executor(exec_task: str):
    # Check and trigger weather alert monitoring system
    if "weather" in exec_task.lower():
        # run as daemon and not store in children table as this won't take long
        logger.debug("Initiating weather alert monitor")
        resource_tracker.semaphores(weather_monitor.monitor)
    else:
        logger.debug("Executing: '%s'", exec_task)
        try:
            response = (
                    offline.communicator(command=exec_task)
                    or "No response for automated task"
            )
            logger.debug("Response: '%s'", response)
        except Exception as error:
            logger.error(error)
            logger.error(traceback.format_exc())


async def db_writer(picker: str, dry_run: bool) -> None:
    if picker == "events":
        process_target = events.events_writer
        logger.info("Getting events from %s.", models.env.event_app) if dry_run else None
    else:
        logger.info("Getting meetings from ICS.") if dry_run else None
        process_target = ics_meetings.meetings_writer
    process = Process(target=process_target)
    process.start()
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute(f"UPDATE children SET {picker}=null")
        cursor.execute(
            f"INSERT or REPLACE INTO children ({picker}) VALUES (?);",
            (process.pid,),
        )
        connection.commit()


async def alarm_executor(now: datetime):
    if alarms := files.get_alarms():
        copied_alarms = alarms.copy()
        for alarmer in alarms:
            # alarms match 'time' and 'day' of alarm
            if (
                    alarmer["alarm_time"] == now.strftime("%I:%M %p") and
                    alarmer.get("day", now.strftime("%A")) == now.strftime("%A")
            ):
                logger.info("Executing alarm: %s", alarmer)
                resource_tracker.semaphores(alarm.executor)
                if not alarmer["repeat"]:
                    copied_alarms.remove(alarmer)
        if copied_alarms != alarms:
            files.put_alarms(data=copied_alarms)


async def reminder_executor(now: datetime):
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
