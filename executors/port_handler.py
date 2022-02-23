import contextlib
import os
import signal
import subprocess
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from typing import Union

from executors.logger import logger
from modules.utils import globals

env = globals.ENV


def get_port() -> int:
    """Chooses a PORT number dynamically that is not being used to ensure we don't rely on a single port.

    Instead of binding to a specific port, ``sock.bind(('', 0))`` is used to bind to 0.

    See Also:
        - The port number chosen can be found using ``sock.getsockname()[1]``
        - Passing it on to the slaves so that they can connect back.
        - ``sock`` is the socket that was created, returned by socket.socket.

    Notes:
        - Well-Known ports: 0 to 1023
        - Registered ports: 1024 to 49151
        - Dynamically available: 49152 to 65535
        - The OS will then pick an available port.

    Returns:
        int:
        Randomly chosen port number that is not in use.
    """
    with contextlib.closing(socket(AF_INET, SOCK_STREAM)) as sock:
        sock.bind(('', 0))
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def is_port_in_use(port: int) -> bool:
    """Connect to a remote socket at address.

    Args:
        port: Takes the port number as an argument.

    Returns:
        bool:
        A boolean flag to indicate whether a port is open.
    """
    with socket(AF_INET, SOCK_STREAM) as sock:
        return sock.connect_ex(('localhost', port)) == 0


def kill_existing(port: int, protocol: str = 'tcp') -> Union[bool, None]:
    """Uses List all open files ``lsof`` to get the PID of the process that is listening on the given port.

    Args:
        port: Port number on which the running process has to be stopped.
        protocol: Protocol that has to be used to list. Defaults to ``TCP``

    Returns:
        bool:
        Flag to indicate whether the process was killed successfully.
    """
    try:
        active_sessions = subprocess.check_output(f"lsof -i {protocol}:{port}", shell=True).decode('utf-8').splitlines()
        for each in active_sessions:
            each_split = each.split()
            if each_split[0].strip() == 'Python':
                ip_port = [d for d in each_split if ':' in d]
                logger.warning(f'Port number is being served on multiple IPs.\n{ip_port}')
                pid = int(each_split[1])
                os.kill(pid, signal.SIGTERM)
                logger.info(f'Killed PID: {pid}')
                return True
        logger.info(f'No active process running on {port}')
        return False
    except (subprocess.SubprocessError, subprocess.CalledProcessError) as error:
        logger.error(error)
