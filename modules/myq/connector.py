from enum import Enum
from logging.config import dictConfig
from typing import Dict, NoReturn, Union

import pymyq
from aiohttp import ClientSession

from executors.logger import logger
from modules.models import models


class Operation(str, Enum):
    """Operations allowed on garage door.

    >>> Operation

    """

    # States of the door
    OPENING: str = "opening"
    CLOSED: str = "closed"
    CLOSING: str = "closing"

    # State of the door as well as operations to be performed
    OPEN: str = "open"
    CLOSE: str = "close"
    STATE: str = "state"


async def garage_controller(operation: str) -> Union[Dict, NoReturn]:
    """Create an aiohttp session and run an operation on garage door.

    Args:
        operation: Takes the operation to be performed as an argument.

    Returns:
        dict:
        Device state information as a dictionary.
    """
    dictConfig({'version': 1, 'disable_existing_loggers': True})
    async with ClientSession() as web_session:
        myq = await pymyq.login(username=models.env.myq_username, password=models.env.myq_password,
                                websession=web_session)

        if not myq.covers:
            logger.warning("No covers found.")
            return

        for device_id, device_obj in myq.covers.items():
            if operation == Operation.OPEN:
                await device_obj.open()
            elif operation == Operation.CLOSE:
                await device_obj.close()
            elif operation == Operation.STATE:
                return device_obj.device_json
