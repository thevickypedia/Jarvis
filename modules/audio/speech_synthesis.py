# noinspection PyUnresolvedReferences
"""Module for speech-synthesis running on a docker container.

>>> SpeechSynthesis

"""

import os
import pathlib
import traceback
from typing import NoReturn

import docker
import requests

from executors.port_handler import is_port_in_use, kill_port_pid
from modules.logger.custom_logger import logger
from modules.models import models


def check_existing() -> bool:
    """Checks for existing connection.

    Returns:
        bool:
        A boolean flag whether a valid connection is present.
    """
    if is_port_in_use(port=models.env.speech_synthesis_port):
        logger.info(f'{models.env.speech_synthesis_port} is currently in use.')
        try:
            res = requests.get(url=f"http://{models.env.speech_synthesis_host}:{models.env.speech_synthesis_port}",
                               timeout=1)
            if res.ok:
                logger.info(f'http://{models.env.speech_synthesis_host}:{models.env.speech_synthesis_port} '
                            'is accessible.')
                return True
            return False
        except (ConnectionError, TimeoutError, requests.exceptions.RequestException, requests.exceptions.Timeout) as \
                error:
            logger.error(error)
            if not kill_port_pid(port=models.env.speech_synthesis_port):
                logger.critical('Failed to kill existing PID. Attempting to re-create session.')


def synthesizer() -> NoReturn:
    """Initiates speech synthesizer using docker."""
    if check_existing():
        return
    if not os.path.isfile(models.fileio.speech_synthesis_log):
        pathlib.Path(models.fileio.speech_synthesis_log).touch()
    with open(models.fileio.speech_synthesis_log, "a") as log_file:
        try:
            client = docker.from_env()
            result = client.containers.run(
                image="rhasspy/larynx",
                ports={f"{models.env.speech_synthesis_port}/tcp": models.env.speech_synthesis_port},
                environment=[f"HOME={models.env.home}"],
                volumes={models.env.home: {"bind": models.env.home, "mode": "rw"}},
                working_dir=os.getcwd(),
                user=f"{os.getuid()}:{os.getgid()}", detach=True
            )
            container = client.containers.get(container_id=result.short_id)
            for line in container.logs(stream=True):
                log_file.write(str(line).strip())
        except Exception as error:
            log_file.write(str(error))
            log_file.write(str(traceback.format_exc()))
            models.env.speech_synthesis_timeout = 0
            return
