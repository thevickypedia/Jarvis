import os
import pathlib
import subprocess
from typing import NoReturn

import requests

from executors.logger import logger
from executors.port_handler import is_port_in_use, kill_port_pid
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


class SpeechSynthesizer:
    """Initiates the docker container to process text-to-speech requests.

    >>> SpeechSynthesizer

    """

    def __init__(self):
        """Creates log file and initiates port number and docker command to run."""
        self.docker = f"""docker run \
            -p {models.env.speech_synthesis_port}:{models.env.speech_synthesis_port} \
            -e "HOME={models.env.home}" \
            -v "$HOME:{models.env.home}" \
            -v /usr/share/ca-certificates:/usr/share/ca-certificates \
            -v /etc/ssl/certs:/etc/ssl/certs \
            -w "{os.getcwd()}" \
            --user "$(id -u):$(id -g)" \
            rhasspy/larynx"""
        if models.env.speech_synthesis_port != 5002:
            self.docker += f" --port {models.env.speech_synthesis_port}"

    def synthesizer(self) -> NoReturn:
        """Initiates speech synthesizer using docker."""
        if check_existing():
            return
        if not os.path.isfile(models.fileio.speech_synthesis_log):
            pathlib.Path(models.fileio.speech_synthesis_log).touch()
        with open(models.fileio.speech_synthesis_log, "a") as output:
            try:
                subprocess.call(self.docker, shell=True, stdout=output, stderr=output)
            except (subprocess.CalledProcessError, subprocess.SubprocessError, Exception) as error:
                logger.error(error)
                return
