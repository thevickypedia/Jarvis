# noinspection PyUnresolvedReferences
"""Module for speech-synthesis running on a docker container.

>>> SpeechSynthesis

"""

import os
import subprocess
import traceback
from typing import NoReturn

import docker
import requests

from jarvis.executors import port_handler
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models

DOCKER_CMD = """echo {PASSWORD} | sudo -S \
docker run \
    -p {PORT}:{PORT} \
    -e "HOME={HOME}" \
    -v "$HOME:{HOME}" \
    -v /usr/share/ca-certificates:/usr/share/ca-certificates \
    -v /etc/ssl/certs:/etc/ssl/certs \
    -w "{CWD}" \
    --user "{UID}:{GID}" \
    --cidfile {DOCKER_CID} \
    thevickypedia/speech-synthesis
"""


def check_existing() -> bool:
    """Checks for existing connection.

    Returns:
        bool:
        A boolean flag whether a valid connection is present.
    """
    if port_handler.is_port_in_use(port=models.env.speech_synthesis_port):
        logger.info("%d is currently in use.", models.env.speech_synthesis_port)
        try:
            res = requests.get(url=f"http://{models.env.speech_synthesis_host}:{models.env.speech_synthesis_port}",
                               timeout=1)
            if res.ok:
                logger.info('http://{host}:{port} is accessible.'.format(host=models.env.speech_synthesis_host,
                                                                         port=models.env.speech_synthesis_port))
                return True
            return False
        except EgressErrors as error:
            logger.error(error)
            if not port_handler.kill_port_pid(port=models.env.speech_synthesis_port):
                logger.critical('ATTENTION::Failed to kill existing PID. Attempting to re-create session.')


def speech_synthesizer() -> NoReturn:
    """Initiates speech synthesizer using docker.

    See Also:
        - Initiates docker container using ``docker-py`` module for Windows and macOS.
        - Initiates container using traditional commandline for Linux.
        - Stores the container ID in a .cid file, to later stop and remove the container.
    """
    config.multiprocessing_logger(filename=models.fileio.speech_synthesis_log)
    if check_existing():
        return

    log_file = open(file=models.fileio.speech_synthesis_log, mode="a", buffering=1)  # 1 line buffer on file
    os.fsync(log_file.fileno())  # Tell os module to write the buffer of the file

    for file in os.listdir(models.fileio.root):
        if file.endswith('.cid'):
            log_file.write(f"Found existing cid file. Removing {file!r}\n")
            os.remove(os.path.join(models.fileio.root, file))

    try:
        # linux requires docker to run as admin and linux is better with commandline
        if models.settings.os == models.supported_platforms.linux:
            cmd = DOCKER_CMD.format(PORT=models.env.speech_synthesis_port, PASSWORD=models.env.root_password,
                                    HOME=models.env.home, CWD=os.getcwd(), UID=os.getuid(), GID=os.getgid(),
                                    DOCKER_CID=models.fileio.speech_synthesis_id)
            log_file.write("Starting speech synthesis in docker container\n")
            subprocess.Popen([cmd], shell=True, bufsize=0, stdout=log_file, stderr=log_file)
        else:
            models.env.home = models.env.home.__str__()
            client = docker.from_env()
            result = client.containers.run(
                image="thevickypedia/speech-synthesis",
                ports={f"{models.env.speech_synthesis_port}/tcp": models.env.speech_synthesis_port},
                environment=[f"HOME={models.env.home}"],
                volumes={models.env.home: {"bind": models.env.home, "mode": "rw"}},
                working_dir=os.getcwd(),
                user=f"{os.getuid()}:{os.getgid()}", detach=True
            )
            log_file.write(f"Started speech synthesis in docker container {result.id!r}\n")
            # Due to lack of a "cidfile" flag, create one manually
            with open(models.fileio.speech_synthesis_id, 'w') as file:
                file.write(result.id)
            logs = client.api.logs(container=result.id, stdout=True, stderr=True, stream=True, timestamps=True,
                                   tail='all', since=None, follow=None, until=None)
            for line in logs:
                log_file.write(line.decode(encoding="UTF-8"))
                log_file.flush()  # Write everything in buffer to file right away
    except Exception as error:
        log_file.write(error.__str__() + '\n')
        log_file.write(traceback.format_exc().__str__() + '\n')
        models.env.speech_synthesis_timeout = 0
    finally:
        log_file.close()
