from enum import Enum
from logging.config import dictConfig
from typing import Dict, NoReturn, Union

import pymyq
from aiohttp import ClientSession

from modules.exceptions import NoCoversFound
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import support


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


async def garage_controller(operation: str, phrase: str) -> Union[Dict, NoReturn]:
    """Create an aiohttp session and run an operation on garage door.

    Args:
        phrase: Takes the recognized phrase as an argument.
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
            raise NoCoversFound("No covers found.")

        device_names = [device_obj.device_json.get('name') for device_id, device_obj in myq.covers.items()]
        logger.debug(f"Available covers: {device_names}")
        device = support.get_closest_match(text=phrase, match_list=device_names)
        logger.debug(f"Chosen cover: {device!r}")
        for device_id, device_obj in myq.covers.items():
            if device_obj.device_json.get('name') != device:
                logger.debug(f"{device_obj.device_json.get('name')!r} does not match {device!r}.")
                continue
            if operation == Operation.OPEN:
                open_result = await device_obj.open()
                logger.debug(open_result)
            elif operation == Operation.CLOSE:
                close_result = await device_obj.close()
                logger.debug(close_result)
            elif operation == Operation.STATE:
                return device_obj.device_json
