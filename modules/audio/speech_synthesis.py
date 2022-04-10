import os.path
import pathlib
import subprocess
from typing import NoReturn

import requests.exceptions

from executors.logger import logger
from executors.port_handler import is_port_in_use, kill_port_pid
from modules.models import models

fileio = models.fileio
env = models.env


class SpeechSynthesizer:
    """Initiates the docker container to process text-to-speech requests.

    >>> SpeechSynthesizer

    """

    def __init__(self):
        """Creates log file and initiates port number and docker command to run."""
        self.port = 5002
        self.docker = f"""docker run \
            -p {self.port}:{self.port} \
            -e "HOME={env.home}" \
            -v "$HOME:{env.home}" \
            -v /usr/share/ca-certificates:/usr/share/ca-certificates \
            -v /etc/ssl/certs:/etc/ssl/certs \
            -w "{os.getcwd()}" \
            --user "$(id -u):$(id -g)" \
            rhasspy/larynx"""

    def check_existing(self) -> bool:
        """Checks for existing connection.

        Returns:
            bool:
            A boolean flag whether a valid connection is present.
        """
        if is_port_in_use(port=self.port):
            logger.info(f'{self.port} is currently in use.')
            try:
                res = requests.get(url=f"http://localhost:{self.port}", timeout=1)
                if res.ok:
                    logger.info(f'http://localhost:{self.port} is accessible.')
                    return True
                return False
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                logger.error('Unable to connect to existing container.')
                if not kill_port_pid(port=self.port):
                    logger.critical('Failed to kill existing PID. Attempting to re-create session.')
                return False

    def synthesizer(self) -> NoReturn:
        """Initiates speech synthesizer using docker."""
        if not env.speech_synthesis_timeout:
            logger.warning("Speech synthesis disabled since the env var DOCKER_TIMEOUT is set to 0")
            return
        if self.check_existing():
            return
        if not os.path.isfile(fileio.speech_synthesis_log):
            pathlib.Path(fileio.speech_synthesis_log).touch()
        with open(fileio.speech_synthesis_log, "a") as output:
            try:
                subprocess.call(self.docker, shell=True, stdout=output, stderr=output)
            except (subprocess.CalledProcessError, subprocess.SubprocessError, Exception) as error:
                logger.error(error)
                env.speech_synthesis_timeout = 0
                return
