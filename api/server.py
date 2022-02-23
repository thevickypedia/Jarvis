import contextlib
from threading import Thread

import requests
import uvicorn
from requests.exceptions import ConnectionError, Timeout

from executors.logger import logger
from executors.port_handler import is_port_in_use
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

        # # TODO: Un-comment the below when switching from "Thread" to "Process"
        # if not kill_existing(port=env.offline_port):  # This might terminate Jarvis
        #     logger.fatal('Failed to kill existing PID. Attempting to re-create session.')

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
