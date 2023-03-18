# noinspection PyUnresolvedReferences
"""Module to control MyQ garage control devices.

>>> MyQ

"""

from enum import Enum
from logging.config import dictConfig
from typing import Dict

import pymyq
from aiohttp import ClientSession
from pymyq.garagedoor import MyQGaragedoor

from jarvis.modules.exceptions import CoverNotOnline, NoCoversFound
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import util


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


operation = Operation


async def garage_controller(phrase: str) -> str:
    """Create an aiohttp session and run an operation on garage door.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Raises:
        NoCoversFound:
        - If there were no garage doors found in the MyQ account.
        CoverNotOnline:
        - If the requested garage door is not online.

    Returns:
        str:
        Response back to the user.
    """
    dictConfig({'version': 1, 'disable_existing_loggers': True})
    async with ClientSession() as web_session:
        myq = await pymyq.login(username=models.env.myq_username, password=models.env.myq_password,
                                websession=web_session)

        if not myq.covers:
            raise NoCoversFound("No covers found.")

        # Create a new dictionary with names as keys and MyQ object as values to get the object by name during execution
        devices: Dict[str, MyQGaragedoor] = {obj_.device_json.get('name'): obj_ for id_, obj_ in myq.covers.items()}
        logger.debug("Available covers: %s", devices)
        device: str = util.get_closest_match(text=phrase, match_list=list(devices.keys()))
        logger.debug("Chosen cover: '%s'", device)

        if not devices[device].online:
            raise CoverNotOnline(device=device, msg=f"{device!r} not online.")

        status = devices[device].device_json

        if models.env.debug:
            assert device == status['name'], f"{device!r} and {status['name']!r} doesn't match"

        logger.debug(status)
        if operation.OPEN in phrase:
            if status['state']['door_state'] == operation.OPEN:
                return f"Your {device} is already open {models.env.title}!"
            elif status['state']['door_state'] == operation.OPENING:
                return f"Your {device} is currently opening {models.env.title}!"
            elif status['state']['door_state'] == operation.CLOSING:
                return f"Your {device} is currently closing {models.env.title}! " \
                       "You may want to retry after a minute or two!"
            logger.info("Opening %s.", device)
            if devices[device].open_allowed:
                open_result = await devices[device].open()
                logger.debug(open_result)
                return f"Opening your {device} {models.env.title}!"
            else:
                return f"Unattended open is disabled on your {device} {models.env.title}!"
        elif operation.CLOSE in phrase:
            if status['state']['door_state'] == operation.CLOSED:
                return f"Your {device} is already closed {models.env.title}!"
            elif status['state']['door_state'] == operation.CLOSING:
                return f"Your {device} is currently closing {models.env.title}!"
            elif status['state']['door_state'] == operation.OPENING:
                return f"Your {device} is currently opening {models.env.title}! " \
                       "You may want to try to after a minute or two!"
            logger.info("Closing %s.", device)
            if devices[device].close_allowed:
                close_result = await devices[device].close()
                logger.debug(close_result)
                return f"Closing your {device} {models.env.title}!"
            else:
                return f"Unattended close is disabled on your {device} {models.env.title}!"
        else:
            logger.info("%s: %s", device, status['state']['door_state'])
            return f"Your {device} is currently {status['state']['door_state']} {models.env.title}! " \
                   f"What do you want me to do to your {device}?"
