import contextlib
import subprocess
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread

import psutil
import requests
import uvicorn
from requests.exceptions import ConnectionError, Timeout

from executors.custom_logger import logger
from executors.internet import ip_address
from modules.utils import globals

env = globals.ENV


class APIServer(uvicorn.Server):
    """Shared servers state that is available between all protocol instances.

    >>> APIServer

    See Also:
        Overrides `uvicorn.server.Server <https://github.com/encode/uvicorn/blob/master/uvicorn/server.py#L48>`__

    References:
        https://github.com/encode/uvicorn/issues/742#issuecomment-674411676
    """

    def install_signal_handlers(self):
        """Overrides ``install_signal_handlers`` in ``uvicorn.Server`` module."""
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        """Initiates ``Server.run`` in a thread."""
        thread = Thread(target=self.run, daemon=True)
        thread.start()

        # # Include the block below, to run only when needed.
        # try:
        #     while not self.started:
        #         sleep(1e-3)
        #     yield
        # finally:
        #     self.should_exit = True
        #     thread.join()


def trigger_api() -> None:
    """Initiates the fast API in a thread using uvicorn server."""
    url = f'http://{env.offline_host}:{env.offline_port}'

    if is_port_in_use(port=env.offline_port):
        logger.info(f'{env.offline_port} is currently in use.')

        try:
            res = requests.get(url=url, timeout=1)
            if res.ok:
                logger.info(f'{url} is accessible.')
                return
            raise ConnectionError
        except (ConnectionError, Timeout):  # Catching Timeout catches both ConnectTimeout and ReadTimeout errors
            logger.error('Unable to connect to existing uvicorn server.')

        if not kill_existing(port=env.offline_port):
            logger.fatal('Failed to kill existing PID. Attempting to re-create session.')

    argument_dict = {
        "app": "api.fast:app",
        "host": env.offline_host,
        "port": env.offline_port,
        "reload": True
    }

    config = uvicorn.Config(**argument_dict)
    server = APIServer(config=config)
    server.run_in_thread()

    # # Thread runs only until the action within this block.
    # with server.run_in_thread():
    #     # Server is started.
    #     ...
    #     # Server will be stopped once code put here is completed
    #     ...


def kill_existing(port: int, protocol: str = 'tcp') -> bool:
    """Uses List all open files ``lsof`` to get the PID of the process that is listening on the given port.

    Args:
        port: Port number on which the running process has to be stopped.
        protocol: Protocol that has to be used to list. Defaults to ``TCP``
    """
    try:
        active_sessions = subprocess.check_output(f"lsof -i {protocol}:{port}", shell=True).decode('utf-8').splitlines()
        for each in active_sessions:
            if each.split()[0] == 'Python':
                pid = int(each.split()[1])
                proc = psutil.Process(pid=pid)
                connection = proc.connections()
                if connection[0].laddr.ip == env.offline_host or connection[0].laddr.ip == ip_address():
                    proc.terminate()
                    logger.info(f'Killed inactive process with PID {pid} running on port: {port}')
                    return True
    except (subprocess.SubprocessError, subprocess.CalledProcessError) as error:
        logger.fatal(error)


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


if __name__ == '__main__':
    import importlib
    import logging

    importlib.reload(module=logging)
    main_logger = logging.getLogger(__name__)
    main_logger.addHandler(hdlr=logging.StreamHandler())
    main_logger.setLevel(level=logging.DEBUG)

    main_logger.info(kill_existing(port=4843))
