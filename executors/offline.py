import json
import os
import subprocess
import time
from datetime import datetime
from multiprocessing import Process
from threading import Thread

import requests
from appscript import app as apple_script

from executors.alarm import alarm_executor
from executors.automation import auto_helper
from executors.conditions import conditions
from executors.logger import logger
from executors.meetings import meeting_file_writer
from executors.remind import reminder_executor
from modules.audio.speaker import audio_driver
from modules.audio.voices import voice_default
from modules.database import database
from modules.models import models
from modules.utils import globals, support

env = models.env
db = database.Database(table_name='offline', columns=['key', 'value'])


def automator() -> None:
    """Place for long-running background threads.

    See Also:
        - Initiates ``meeting_file_writer`` and ``scan_smart_devices`` every hour in a dedicated process.
        - Keeps waiting for the record ``request`` in the database table ``offline`` to invoke ``offline_communicator``
        - The ``automation.yaml`` should be a dictionary within a dictionary that looks like the below:

            .. code-block:: yaml

                6:00 AM:
                  task: set my bedroom lights to 50%
                9:00 PM:
                  task: set my bedroom lights to 5%

        - Jarvis creates/swaps a ``status`` flag upon execution, so that it doesn't execute a task repeatedly.
    """
    start = time.time()
    dry_run = True
    while True:
        if cmd := db.cursor.execute("SELECT value from offline WHERE key=?", ('request',)).fetchone():
            db.cursor.execute("DELETE FROM offline WHERE key=:key OR value=:value ",
                              {'key': 'request', 'value': cmd[0]})
            db.connection.commit()
            offline_communicator(command=cmd[0])
            support.flush_screen()

        if os.path.isfile('automation.yaml'):
            if exec_task := auto_helper():
                offline_communicator(command=exec_task, respond=False)

        if dry_run or start + 3_600 <= time.time():  # Executes every hour
            start = time.time()
            Process(target=meeting_file_writer).start()
            Process(target=support.scan_smart_devices).start()

        if alarm_state := support.lock_files(alarm_files=True):
            for each_alarm in alarm_state:
                if each_alarm == datetime.now().strftime("%I_%M_%p.lock"):
                    Process(target=alarm_executor).start()
                    os.remove(f'alarm/{each_alarm}')
        if reminder_state := support.lock_files(reminder_files=True):
            for each_reminder in reminder_state:
                remind_time, remind_msg = each_reminder.split('-')
                remind_msg = remind_msg.rstrip('.lock')
                if remind_time == datetime.now().strftime("%I_%M_%p"):
                    Thread(target=reminder_executor, args=[remind_msg]).start()
                    os.remove(f'reminder/{each_reminder}')

        if globals.STOPPER['status']:
            logger.info('Exiting automator since the STOPPER flag was set.')
            break

        dry_run = False


def initiate_tunneling(offline_host: str, offline_port: int, home: str) -> None:
    """Initiates Ngrok to tunnel requests from external sources if they aren't running already.

    Notes:
        - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the port ``4483``.
        - The connection is tunneled through a public facing URL used to make ``POST`` requests to Jarvis API.
    """
    ngrok_status = False
    target_script = 'forever_ngrok.py'
    activator = 'source venv/bin/activate'

    pid_check = subprocess.check_output(f"ps -ef | grep {target_script}", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'grep' not in id_ and '/bin/sh' not in id_:
            if target_script == 'forever_ngrok.py':
                ngrok_status = True
                logger.info('An instance of ngrok connection for offline communicator is running already.')
    if not ngrok_status:
        if os.path.exists(f"{home}/JarvisHelper"):
            logger.info('Initiating ngrok connection for offline communicator.')
            initiate = f'cd {home}/JarvisHelper && {activator} && export port={offline_port} && python {target_script}'
            apple_script('Terminal').do_script(initiate)
        else:
            logger.error(f'JarvisHelper is not available to trigger an ngrok tunneling through {offline_port}')
            endpoint = rf'http:\\{offline_host}:{offline_port}'
            logger.error(f'However offline communicator can still be accessed via '
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


def offline_communicator(command: str = None, respond: bool = True) -> None:
    """Initiates a task and writes the spoken text into the record ``response`` in the database table ``offline``.

    Args:
        command: Takes the command that has to be executed as an argument.
        respond: Flag to create a ``response`` record in the database table ``offline``.

    Warnings:
        - Handles ``RuntimeError`` and logs it.
        - Excepted when the ``speaker`` is stopped while another loop of speaker is in progress by regular interaction.
    """
    response = None
    try:
        globals.called_by_offline['status'] = True
        conditions(converted=command)
        globals.called_by_offline['status'] = False
        response = globals.text_spoken.get('text')
        if 'restart' not in command and respond:
            db.cursor.execute(f"INSERT OR REPLACE INTO offline (key, value) VALUES ('response','{response}')")
            db.connection.commit()
        audio_driver.stop()
        voice_default()
    except RuntimeError as error:
        if command and not response:
            db.cursor.execute(f"INSERT OR REPLACE INTO offline (key, value) VALUES ('request','{command}')")
            db.connection.commit()
        logger.fatal(f'Received a RuntimeError while executing offline request.\n{error}')
