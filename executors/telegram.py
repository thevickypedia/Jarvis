import importlib
import logging
import time
from logging.config import dictConfig
from typing import NoReturn

import requests

from modules.models import config
from modules.telegram.bot import TelegramBot

importlib.reload(module=logging)
dictConfig(config.BotConfig().dict())
logger = logging.getLogger('telegram')

FAILED_CONNECTIONS = {'calls': 0}


def handler() -> NoReturn:
    """Initiates polling for new messages.

    Handles:
        - OverflowError: Restarts polling to take control over.
        - ConnectionError: Initiates after 10, 20 or 30 seconds. Depends on retry count. Shuts off after 3 attempts.
    """
    try:
        TelegramBot().poll_for_messages()
    except OverflowError as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        handler()
    except (requests.exceptions.ReadTimeout, ConnectionError) as error:
        FAILED_CONNECTIONS['calls'] += 1
        logger.critical(error)
        logger.info("Restarting after 10 seconds..")
        time.sleep(FAILED_CONNECTIONS['calls'] * 10)
        if FAILED_CONNECTIONS['calls'] > 3:
            logger.fatal("Couldn't recover from connection error.")
        else:
            handler()
    # Expected exceptions
    # except socket.timeout as error:
    #     logger.fatal(error)
    # except urllib3.exceptions.ConnectTimeoutError as error:
    #     logger.fatal(error)
    # except urllib3.exceptions.MaxRetryError as error:
    #     logger.fatal(error)
    # except requests.exceptions.ConnectTimeout as error:
    #     logger.fatal(error)
