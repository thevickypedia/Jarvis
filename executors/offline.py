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
from executors.controls import restart
from executors.logger import logger
from executors.meetings import meeting_file_writer
from executors.remind import reminder_executor
from modules.audio.speaker import audio_driver
from modules.audio.voices import voice_default
from modules.models import models
from modules.utils import globals, support

env = models.env


def automator() -> None:
    """Place for long-running background threads.

    See Also:
        - Initiates ``meeting_file_writer`` and ``scan_smart_devices`` every hour in a dedicated process.
        - Keeps looking for the ``offline_request`` file, and invokes ``offline_communicator`` with content as the arg.
        - The ``automation.yaml`` should be a dictionary within a dictionary that looks like the below:

            .. code-block:: yaml

                6:00 AM:
                  task: set my bedroom lights to 50%
                9:00 PM:
                  task: set my bedroom lights to 5%

        - Jarvis creates/swaps a ``status`` flag upon execution, so that it doesn't execute a task repeatedly.
    """
    # todo: Write and read offline messages from DB
    start = time.time()
    dry_run = True
    while True:
        if os.path.isfile('offline_request'):
            time.sleep(0.1)  # Read file after 0.1 second for the content to be written
            with open('offline_request') as off_request:
                offline_communicator(command=off_request.read())
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
    """Reads ``offline_request`` file generated by `fast.py <https://git.io/JBPFQ>`__ containing request sent via API.

    Args:
        command: Takes the command that has to be executed as an argument.
        respond: Takes the argument to decide whether to create the ``offline_response`` file.

    Env Vars:
        - ``offline_pass`` - Phrase to authenticate the requests to API. Defaults to ``jarvis``

    Notes:
        More cool stuff (Done by ``JarvisHelper``):
            - Run ``ngrok http`` on port 4483 or any desired port set as an env var ``offline_port``.
            - I have linked the ngrok ``public_url`` tunnelling the FastAPI to a JavaScript on my webpage.
            - When a request is submitted, the JavaScript makes a POST call to the API.
            - The API does the authentication and creates the ``offline_request`` file if authenticated.
            - Check it out: `JarvisOffline <https://thevickypedia.com/jarvisoffline>`__

    Warnings:
        - Restarts ``Jarvis`` quietly in case of a ``RuntimeError`` however, the offline request will still be executed.
        - This happens when ``speaker`` is stopped while another loop of speaker is in progress by regular interaction.
    """
    response = None
    try:
        if command:
            os.remove('offline_request') if respond else None  # file will be unavailable when called by automator
            globals.called_by_offline['status'] = True
            conditions(converted=command)
            globals.called_by_offline['status'] = False
            response = globals.text_spoken.get('text')
        else:
            response = 'Received a null request. Please resend it.'
        if 'restart' not in command and respond:  # response will not be written when called by automator
            with open('offline_response', 'w') as off_response:
                off_response.write(response)
        audio_driver.stop()
        voice_default()
    except RuntimeError as error:
        if command and not response:
            with open('offline_request', 'w') as off_request:
                off_request.write(command)
        logger.fatal(f'Received a RuntimeError while executing offline request.\n{error}')
        restart(quiet=True)
