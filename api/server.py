import contextlib

import requests
import uvicorn
from requests.exceptions import ConnectionError, Timeout

from executors.logger import logger
from executors.port_handler import is_port_in_use, kill_port_pid
from modules.models import models

env = models.env


class APIServer(uvicorn.Server):
    """Shared servers state that is available between all protocol instances.

    >>> APIServer

    See Also:
        Overrides `uvicorn.server.Server <https://github.com/encode/uvicorn/blob/master/uvicorn/server.py#L48>`__

    References:
        https://github.com/encode/uvicorn/issues/742#issuecomment-674411676
    """

    def install_signal_handlers(self) -> None:
        """Overrides ``install_signal_handlers`` in ``uvicorn.Server`` module."""
        pass

    @contextlib.contextmanager
    def run_in_parallel(self) -> None:
        """Initiates ``Server.run`` in a dedicated process."""
        self.run()


def trigger_api() -> None:
    """Initiates the fast API in a dedicated process using uvicorn server.

    See Also:
        - Checks if the port is being used. If so, makes a ``GET`` request to the endpoint.
        - Attempts to kill the process listening to the port, if the endpoint doesn't respond.
    """
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

        if not kill_port_pid(port=env.offline_port):  # This might terminate Jarvis
            logger.critical('Failed to kill existing PID. Attempting to re-create session.')

    argument_dict = {
        "app": "api.fast:app",
        "host": env.offline_host,
        "port": env.offline_port,
        "reload": True
    }
    if not env.mac:
        del argument_dict['reload']

    config = uvicorn.Config(**argument_dict)
    APIServer(config=config).run_in_parallel()
