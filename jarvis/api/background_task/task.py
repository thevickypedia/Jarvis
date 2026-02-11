import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

from deepdiff import DeepDiff

from jarvis.api.background_task import agent, bot
from jarvis.executors import automation, background_task, connectivity, crontab
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import classes, models


@dataclass
class StartTimes:
    """Dataclass to store each agent's start time.

    >>> StartTimes

    """

    events: float
    meetings: float
    pulse: float
    telegram: float


# TODO: Rename to pulse or beat
#   TRACK ALL SPAWNS WITH ``.add_done_callback`` to a task and restart as needed
async def background_tasks() -> None:
    """Trigger for background tasks, cron jobs, automation, alarms, reminders, events and meetings sync."""
    multiprocessing_logger(filename=os.path.join("logs", "background_tasks_%d-%m-%Y.log"))

    # Env vars are loaded only during startup, so run validations beforehand
    await automation.validate_weather_alert()
    await agent.init_meetings()
    if not all((models.env.wifi_ssid, models.env.wifi_password)):
        classes.wifi_connection = None

    tasks: List[classes.BackgroundTask] = list(background_task.validate_tasks())
    cron_jobs: List[crontab.expression.CronExpression] = list(crontab.validate_jobs())

    t_now = time.time()
    start_times = StartTimes(t_now, t_now, t_now, t_now)

    # Creates a start time for each task
    task_dict = {i: time.time() for i in range(len(tasks))}

    asyncio.create_task(bot.init())
    while True:
        now = datetime.now()

        # PULSE: Once during start up (regardless of schedule) and 1m after that
        if start_times.pulse + 60 <= time.time():
            start_times.pulse = time.time()

            # MARK: Trigger background tasks
            asyncio.create_task(agent.background_executor(tasks=tasks, task_dict=task_dict, now=now))

            # MARK: Trigger cron jobs
            asyncio.create_task(agent.crontab_executor(cron_jobs=cron_jobs))

            # MARK: Trigger automation
            if exec_task := automation.auto_helper():
                asyncio.create_task(agent.automation_executor(exec_task=exec_task))

            # MARK: Trigger Wi-Fi checker
            if classes.wifi_connection:
                asyncio.create_task(connectivity.wifi())

            # MARK: Sync events from the event app specified (calendar/outlook)
            if (
                models.env.event_app
                and models.env.sync_events
                and start_times.events + models.env.sync_events <= time.time()
            ):
                start_times.events = time.time()
                asyncio.create_task(agent.db_writer(picker="events"))

            # MARK: Sync meetings from the ICS url provided
            if (
                models.env.ics_url
                and models.env.sync_meetings
                and start_times.meetings + models.env.sync_meetings <= time.time()
            ):
                start_times.meetings = time.time()
                asyncio.create_task(agent.db_writer(picker="meetings"))

            # MARK: Trigger alarms
            asyncio.create_task(agent.alarm_executor(now))

            # MARK: Trigger reminders
            asyncio.create_task(agent.reminder_executor(now))

        # MARK: Poll for telegram messages
        if bot.telegram_beat.poll_for_messages:
            asyncio.create_task(bot.telegram_executor())
        if bot.telegram_beat.restart_loop:
            # Avoid being called again when init is in progress
            bot.telegram_beat.restart_loop = False
            asyncio.create_task(bot.init(3))

        # MARK: Re-check for any newly added tasks with logger disabled
        new_tasks: List[classes.BackgroundTask] = list(background_task.validate_tasks(log=False))
        if new_tasks != tasks:
            logger.warning("Tasks list has been updated.")
            logger.info(DeepDiff(tasks, new_tasks, ignore_order=True))
            tasks = new_tasks
            # Re-create start time for each task
            task_dict = {i: time.time() for i in range(len(tasks))}

        # MARK: Re-check for any newly added cron_jobs with logger disabled
        new_cron_jobs: List[crontab.expression.CronExpression] = list(crontab.validate_jobs(log=False))
        if new_cron_jobs != cron_jobs:
            # Don't log updated jobs since there will always be a difference when run on author mode
            cron_jobs = new_cron_jobs

        # MARK: Pause and yield control back to the event loop
        await asyncio.sleep(3)
