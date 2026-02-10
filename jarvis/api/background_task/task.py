import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime
from multiprocessing.pool import ThreadPool
from typing import List

from deepdiff import DeepDiff

from jarvis.api.background_task import agent
from jarvis.executors import (
    automation,
    background_task,
    connectivity,
    crontab,
    telegram,
)
from jarvis.modules.exceptions import BotInUse, BotWebhookConflict, EgressErrors
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import classes, models
from jarvis.modules.telegram import bot, webhook


@dataclass
class StartTimes:
    """Dataclass to store each agent's start time.

    >>> StartTimes

    """

    events: float
    meetings: float
    pulse: float
    telegram: float
    wifi: float


async def background_tasks() -> None:
    """Trigger for background tasks, cron jobs, automation, alarms, reminders, events and meetings sync."""
    multiprocessing_logger(
        filename=os.path.join("logs", "background_tasks_%d-%m-%Y.log")
    )

    # Env vars are loaded only during startup, so run validations beforehand
    await automation.validate_weather_alert()
    await agent.init_meetings()

    if all((models.env.wifi_ssid, models.env.wifi_password)):
        wifi_checker = classes.WiFiConnection()
    else:
        wifi_checker = None

    tasks: List[classes.BackgroundTask] = list(background_task.validate_tasks())
    cron_jobs: List[crontab.expression.CronExpression] = list(crontab.validate_jobs())

    t_now = time.time()
    start_times = StartTimes(t_now, t_now, t_now, t_now, t_now)

    # Creates a start time for each task
    task_dict = {i: time.time() for i in range(len(tasks))}

    telegram_thread = ThreadPool(processes=1).apply_async(func=telegram.telegram_api)
    poll_telegram = False
    telegram_offset = 0
    failed_telegram_connections = {"count": 0}

    dry_run = True
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
            if wifi_checker and models.env.connection_retry and start_times.wifi + models.env.connection_retry <= time.time():
                # TODO: Shouldn't block
                wifi_checker = await connectivity.wifi(wifi_checker)

            # MARK: Sync events from the event app specified (calendar/outlook)
            if models.env.event_app and models.env.sync_events and start_times.events + models.env.sync_events <= time.time():
                start_times.events = time.time()
                asyncio.create_task(agent.db_writer(picker="events", dry_run=dry_run))

            # MARK: Sync meetings from the ICS url provided
            if models.env.ics_url and models.env.sync_meetings and start_times.meetings + models.env.sync_meetings <= time.time():
                start_times.meetings = time.time()
                asyncio.create_task(agent.db_writer(picker="meetings", dry_run=dry_run))

            # MARK: Trigger alarms
            asyncio.create_task(agent.alarm_executor(now))

            # MARK: Trigger reminders
            asyncio.create_task(agent.reminder_executor(now))

        # MARK: Poll for telegram messages
        if not poll_telegram and start_times.telegram + 30 <= time.time():
            # TODO:
            #  Easy way implement telegram_api(3) would be create the `telegram_thread` in a func and call it on-demand
            #  Best way would be to create an external even loop to control which segments require a restart (incl self)
            if telegram_thread.ready():
                poll_telegram = telegram_thread.get()
            else:
                logger.info("Telegram thread is still looking for a webhook.")

        if poll_telegram:
            try:
                offset = bot.poll_for_messages(telegram_offset)
                if offset is not None:
                    telegram_offset = offset
            except BotWebhookConflict as error:
                # At this point, its be safe to remove the dead webhook
                logger.error(error)
                webhook.delete_webhook(base_url=bot.BASE_URL, logger=logger)
                # TODO: Need to try webhook for 3 times, and fall back to polling
                # telegram_api(3)
            except BotInUse as error:
                logger.error(error)
                logger.info("Restarting message poll to take over..")
                # TODO: Need to try webhook for 3 times, and fall back to polling
                # telegram_api(3)
            except EgressErrors as error:
                logger.error(error)
                failed_telegram_connections["count"] += 1
                if failed_telegram_connections["count"] > 3:
                    logger.critical(
                        "ATTENTION::Couldn't recover from connection error. Restarting current process."
                    )
                    # TODO: Implement a restart mechanism
                    # controls.restart_control(quiet=True)
                else:
                    logger.info(
                        "Restarting in %d seconds.",
                        failed_telegram_connections["count"] * 10,
                    )
                    await asyncio.sleep(failed_telegram_connections["count"] * 10)
                    # TODO: Need to try webhook for 3 times, and fall back to polling
                    # telegram_api(3)
            except Exception as error:
                logger.critical("ATTENTION: %s", error.__str__())
                # TODO: Implement a restart mechanism
                # controls.restart_control(quiet=True)

        # MARK: Re-check for any newly added tasks with logger disabled
        new_tasks: List[classes.BackgroundTask] = list(
            background_task.validate_tasks(log=False)
        )
        if new_tasks != tasks:
            logger.warning("Tasks list has been updated.")
            logger.info(DeepDiff(tasks, new_tasks, ignore_order=True))
            tasks = new_tasks
            # Re-create start time for each task
            task_dict = {i: time.time() for i in range(len(tasks))}

        # MARK: Re-check for any newly added cron_jobs with logger disabled
        new_cron_jobs: List[crontab.expression.CronExpression] = list(
            crontab.validate_jobs(log=False)
        )
        if new_cron_jobs != cron_jobs:
            # Don't log updated jobs since there will always be a difference when run on author mode
            cron_jobs = new_cron_jobs
        dry_run = False

        # MARK: Pause and yield control back to the event loop
        await asyncio.sleep(1)
