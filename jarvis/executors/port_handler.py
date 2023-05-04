import os
import signal
import socket
import subprocess
import sys
import warnings
from typing import Union

from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models


def is_port_in_use(port: int) -> bool:
    """Connect to a remote socket at address, to identify if the port is currently being used.

    Args:
        port: Takes the port number as an argument.

    Returns:
        bool:
        A boolean flag to indicate whether a port is open.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(('localhost', port)) == 0


def kill_port_pid(port: int, protocol: str = 'tcp') -> Union[bool, None]:
    """Uses List all open files ``lsof`` to get the PID of the process that is listening on the given port and kills it.

    Args:
        port: Port number which the application is listening on.
        protocol: Protocol serving the port. Defaults to ``TCP``

    Warnings:
        **Use only when the application listening to given port runs as a dedicated/child process with a different PID**

            - This function will kill the process that is using the given port.
            - If the PID is the same as that of ``MainProcess``, triggers a warning without terminating the process.

    Returns:
        bool:
        Flag to indicate whether the process was terminated successfully.
    """
    try:
        active_sessions = subprocess.check_output(f"lsof -i {protocol}:{port}", shell=True).decode('utf-8').splitlines()
        for each in active_sessions:
            each_split = each.split()
            if each_split[0].strip() == 'Python':
                logger.info("Application hosted on %s is listening to port: %d", each_split[-2], port)
                pid = int(each_split[1])
                if pid == models.settings.pid:
                    called_function = sys._getframe(1).f_code.co_name  # noqa
                    called_file = sys._getframe(1).f_code.co_filename.replace(f'{os.getcwd()}/', '')  # noqa
                    logger.warning("%s from %s tried to kill the running process.", called_function, called_file)
                    warnings.warn(
                        f'OPERATION DENIED: {called_function} from {called_file} tried to kill the running process.'
                    )
                    return
                os.kill(pid, signal.SIGTERM)
                logger.info("Killed PID: %d", pid)
                return True
        logger.info("No active process running on %d", port)
        return False
    except (subprocess.SubprocessError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            result = error.output.decode(encoding='UTF-8').strip()
            logger.error("[%d]: %s", error.returncode, result)
        else:
            logger.error(error)
