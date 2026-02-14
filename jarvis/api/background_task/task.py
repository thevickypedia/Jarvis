import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List

from deepdiff import DeepDiff

from jarvis.api.background_task import agent, bot
from jarvis.executors import (
    automation,
    background_task,
    communicator,
    connectivity,
    crontab,
)
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import classes, models

MAX_TOLERANCE = 10
FAIL_SAFE = {}


def error_handler(task: asyncio.Task) -> None:
    """Callback function for asynchronous tasks.

    Args:
        task: Takes the task as an argument.

    See Also:
        - Notifies the user and kills the specific task after 10 failures.
        - Restarts the background task after 3 repeated failures.
        - Logs a warning for any failures with less than 3 occurrences.
    """
    task_name = task.get_name()
    try:
        task.result()
        logger.debug("Execution completed for the task: %s", task_name)
    except Exception as error:
        FAIL_SAFE[task_name] = FAIL_SAFE.get(task_name, 0) + 1
        attempt = FAIL_SAFE[task_name]
        if attempt > MAX_TOLERANCE:
            logger.exception(
                "Background task %s crashed %d times, future tasks will be ignored",
                task_name,
                MAX_TOLERANCE,
                exc_info=error,
            )
            try:
                communicator.notify(
                    subject="JARVIS: BackgroundTask",
                    body=f"Background task {task_name!r} crashed {attempt}: {type(error).__name__}",
                )
            except Exception as error:
                logger.error("Failed to send crash notification: %s", error)
        elif attempt > 3:
            logger.error("Background task %s crashed (%d)", task_name, attempt)
        else:
            logger.warning("Background task %s crashed (%d)", task_name, attempt)


def create_task(func: Callable, *args, **kwargs) -> None:
    """Creates an asynchronous task with a done callback attached to handle errors, restarts and notifications.

    Args:
        func: Callable object to create a task for.
    """
    if hasattr(func, "__module__") and hasattr(func, "__qualname__"):
        task_name = f"{func.__module__}.{func.__qualname__}".replace("jarvis.", "")
    else:
        task_name = func.__name__
    if FAIL_SAFE.get(task_name, 0) > 10:
        logger.debug("Background task %s could not be recovered, ignoring task creation", task_name)
        return
    logger.debug("Creating a task for the coroutine: %s", task_name)
    task = asyncio.create_task(func(*args, **kwargs), name=task_name)
    task.add_done_callback(error_handler)


@dataclass
class StartTimes:
    """Dataclass to store each agent's start time.

    >>> StartTimes

    """

    events: float
    meetings: float
    pulse: float
    telegram: float


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

    # Load start up times
    t_now = time.time()
    start_times = StartTimes(t_now, t_now, t_now, t_now)

    # Creates a start time for each task
    task_dict = {i: time.time() for i in range(len(tasks))}

    # Instantiate telegram bot - webhook vs long polling
    create_task(bot.init)
    while True:
        now = datetime.now()

        # PULSE: Once during start up (regardless of schedule) and 1m after that
        if start_times.pulse + 60 <= time.time():
            start_times.pulse = time.time()

            # MARK: Trigger background tasks
            create_task(agent.background_executor, tasks=tasks, task_dict=task_dict, now=now)

            # MARK: Trigger cron jobs
            create_task(agent.crontab_executor, cron_jobs=cron_jobs)

            # MARK: Trigger automation
            if exec_task := automation.auto_helper():
                create_task(agent.automation_executor, exec_task=exec_task)

            # MARK: Trigger Wi-Fi checker
            if classes.wifi_connection:
                create_task(connectivity.wifi)

            # MARK: Sync events from the event app specified (calendar/outlook)
            if (
                models.env.event_app
                and models.env.sync_events
                and start_times.events + models.env.sync_events <= time.time()
            ):
                start_times.events = time.time()
                create_task(agent.db_writer, picker="events")

            # MARK: Sync meetings from the ICS url provided
            if (
                models.env.ics_url
                and models.env.sync_meetings
                and start_times.meetings + models.env.sync_meetings <= time.time()
            ):
                start_times.meetings = time.time()
                create_task(agent.db_writer, picker="meetings")

            # MARK: Trigger alarms
            create_task(agent.alarm_executor, now)

            # MARK: Trigger reminders
            create_task(agent.reminder_executor, now)

        # MARK: Poll for telegram messages
        if bot.telegram_beat.poll_for_messages:
            create_task(bot.telegram_executor)
        if bot.telegram_beat.restart_loop:
            # Avoid being called again when init is in progress
            bot.telegram_beat.restart_loop = False
            create_task(bot.init, 3)

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
