import contextlib
import os
import signal
import subprocess
import sys
import warnings
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from typing import Union

from executors.logger import logger


def get_free_port() -> int:
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
    """Connect to a remote socket at address, to identify if the port is currently being used.

    Args:
        port: Takes the port number as an argument.

    Returns:
        bool:
        A boolean flag to indicate whether a port is open.
    """
    with socket(AF_INET, SOCK_STREAM) as sock:
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
                logger.info(f'Application hosted on {each_split[-2]} is listening to port: {port}')
                pid = int(each_split[1])
                if pid == os.getpid():
                    called_function = sys._getframe(1).f_code.co_name  # noqa
                    called_file = sys._getframe(1).f_code.co_filename.replace(f'{os.getcwd()}/', '')  # noqa
                    logger.warning(f"{called_function} from {called_file} tried to kill the running process.")
                    warnings.warn(
                        f'OPERATION DENIED: {called_function} from {called_file} tried to kill the running process.'
                    )
                    return
                os.kill(pid, signal.SIGTERM)
                logger.info(f'Killed PID: {pid}')
                return True
        logger.info(f'No active process running on {port}')
        return False
    except (subprocess.SubprocessError, subprocess.CalledProcessError) as error:
        logger.error(error)
