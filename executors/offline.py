import json
import os
import subprocess
import time
from datetime import datetime
from multiprocessing import Process
from threading import Thread
from typing import AnyStr, NoReturn

import requests

from executors.alarm import alarm_executor
from executors.automation import auto_helper
from executors.conditions import conditions
from executors.logger import logger
from executors.remind import reminder_executor
from modules.meetings import events, icalendar
from modules.models import models
from modules.utils import shared, support

env = models.env
fileio = models.fileio


def automator() -> NoReturn:
    """Place for long-running background tasks.

    See Also:
        - Initiates ``meeting_file_writer`` and ``scan_smart_devices`` every hour in a dedicated process.
        - Keeps waiting for the record ``request`` in the database table ``offline`` to invoke ``offline_communicator``
        - The automation file should be a dictionary within a dictionary that looks like the below:

            .. code-block:: yaml

                6:00 AM:
                  task: set my bedroom lights to 50%
                9:00 PM:
                  task: set my bedroom lights to 5%

        - Jarvis creates/swaps a ``status`` flag upon execution, so that it doesn't execute a task repeatedly.
    """
    start_events = start_meetings = start_netgear = time.time()
    events.event_app_launcher()
    dry_run = True
    while True:
        if os.path.isfile(fileio.automation):
            if exec_task := auto_helper():
                offline_communicator(command=exec_task)

        if start_events + env.sync_events <= time.time() or dry_run:
            start_events = time.time()
            logger.info(f"Getting calendar events from {env.event_app}") if dry_run else None
            Process(target=events.events_writer).start()

        if start_meetings + env.sync_meetings <= time.time() or dry_run:
            start_meetings = time.time()
            logger.info("Getting calendar schedule from ICS.") if dry_run else None
            Process(target=icalendar.meetings_writer).start()

        if start_netgear + env.sync_netgear <= time.time() or dry_run:
            start_netgear = time.time()
            logger.info("Scanning smart devices using netgear module.") if dry_run and env.router_pass else None
            Process(target=support.scan_smart_devices).start() if env.router_pass else None

        if alarm_state := support.lock_files(alarm_files=True):
            for each_alarm in alarm_state:
                if each_alarm == datetime.now().strftime("%I_%M_%p.lock"):
                    Process(target=alarm_executor).start()
                    os.remove(f'alarm{os.path.sep}{each_alarm}')
        if reminder_state := support.lock_files(reminder_files=True):
            for each_reminder in reminder_state:
                remind_time, remind_msg = each_reminder.split('-')
                remind_msg = remind_msg.rstrip('.lock')
                if remind_time == datetime.now().strftime("%I_%M_%p"):
                    Thread(target=reminder_executor, args=[remind_msg]).start()
                    os.remove(f'reminder{os.path.sep}{each_reminder}')

        dry_run = False


def initiate_tunneling() -> NoReturn:
    """Initiates Ngrok to tunnel requests from external sources if they aren't running already.

    Notes:
        - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the given offline port.
        - The connection is tunneled through a public facing URL used to make ``POST`` requests to Jarvis API.
    """
    if not env.mac:
        return
    pid_check = subprocess.check_output("ps -ef | grep forever_ngrok.py", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'grep' not in id_ and '/bin/sh' not in id_:
            logger.info('An instance of ngrok tunnel for offline communicator is running already.')
            return
    if os.path.exists(f"{env.home}/JarvisHelper/venv/bin/activate"):
        logger.info('Initiating ngrok connection for offline communicator.')
        initiate = f'cd {env.home}/JarvisHelper && ' \
                   f'source venv/bin/activate && export port={env.offline_port} && python forever_ngrok.py'
        os.system(f"""osascript -e 'tell application "Terminal" to do script "{initiate}"' > /dev/null""")
    else:
        logger.info(f'JarvisHelper is not available to trigger an ngrok tunneling through {env.offline_port}')
        endpoint = rf'http:\\{env.offline_host}:{env.offline_port}'
        logger.info('However offline communicator can still be accessed via '
                    f'{endpoint}\\offline-communicator for API calls and {endpoint}\\docs for docs.')


def on_demand_offline_automation(task: str) -> bool:
    """Makes a ``POST`` call to offline-communicator running on ``localhost`` to execute a said task.

    Args:
        task: Takes the command to be executed as an argument.

    Returns:
        bool:
        Returns a boolean ``True`` if the request was successful.
    """
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {
        'phrase': env.offline_pass,
        'command': task
    }

    offline_endpoint = f"http://{env.offline_host}:{env.offline_port}/offline-communicator"
    try:
        response = requests.post(url=offline_endpoint, headers=headers, data=json.dumps(data))
    except ConnectionError:
        return False
    if response.ok:
        return True


def offline_communicator(command: str) -> AnyStr:
    """Initiates conditions after flipping ``status`` flag in ``called_by_offline`` dict which suppresses the speaker.

    Args:
        command: Takes the command that has to be executed as an argument.

    Returns:
        AnyStr:
        Response from Jarvis.
    """
    shared.called_by_offline = True
    conditions(converted=command, should_return=True)
    shared.called_by_offline = False
    if response := shared.text_spoken:
        shared.text_spoken = None
        return response
    else:
        return f"I was unable to process the request: {command}"
