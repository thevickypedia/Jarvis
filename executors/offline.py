import json
import os
import subprocess

import requests
from appscript import app as apple_script

from executors.logger import logger
from modules.models import models

env = models.env


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
