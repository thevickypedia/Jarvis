import contextlib

import requests
import uvicorn

from executors.port_handler import is_port_in_use, kill_port_pid
from modules.exceptions import EgressErrors
from modules.logger.custom_logger import logger
from modules.models import models


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


def fastapi() -> None:
    """Initiates the fast API in a dedicated process using uvicorn server.

    See Also:
        - Checks if the port is being used. If so, makes a ``GET`` request to the endpoint.
        - Attempts to kill the process listening to the port, if the endpoint doesn't respond.
    """
    url = f'http://{models.env.offline_host}:{models.env.offline_port}'

    if is_port_in_use(port=models.env.offline_port):
        logger.info(f'{models.env.offline_port} is currently in use.')

        try:
            res = requests.get(url=url, timeout=1)
            if res.ok:
                logger.info(f'{url!r} is accessible.')
                return
            raise requests.exceptions.ConnectionError
        except EgressErrors:
            logger.error('Unable to connect to existing uvicorn server.')

        if not kill_port_pid(port=models.env.offline_port):  # This might terminate Jarvis
            logger.critical('Failed to kill existing PID. Attempting to re-create session.')

    argument_dict = {
        "app": "api.fast:app",
        "host": models.env.offline_host,
        "port": models.env.offline_port,
        "ws_ping_interval": 20.0,
        "ws_ping_timeout": 20.0,
        "workers": models.env.workers,
        "reload": True
    }

    config = uvicorn.Config(**argument_dict)
    APIServer(config=config).run_in_parallel()
