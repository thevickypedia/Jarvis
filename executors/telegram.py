import importlib
import logging
import sys
import time
from logging.config import dictConfig
from typing import NoReturn

import requests

from executors.controls import restart_control
from modules.exceptions import BotInUse
from modules.models import config, models
from modules.telegram.bot import TelegramBot

importlib.reload(module=logging)
dictConfig(config.BotConfig().dict())
logger = logging.getLogger('telegram')

FAILED_CONNECTIONS = {'count': 0}


def handler() -> NoReturn:
    """Initiates polling for new messages.

    Handles:
        - BotInUse: Restarts polling to take control over.
        - ConnectionError: Initiates after 10, 20 or 30 seconds. Depends on retry count. Shuts off after 3 attempts.
    """
    if not models.env.bot_token:
        logger.info("Bot token is required to start the Telegram Bot")
        return
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 10)  # increases the recursion limit by 10 times
    try:
        TelegramBot().poll_for_messages()
    except BotInUse as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        handler()
    except (ConnectionError, TimeoutError, requests.exceptions.RequestException, requests.exceptions.Timeout) as error:
        logger.critical(error)
        FAILED_CONNECTIONS['count'] += 1
        if FAILED_CONNECTIONS['count'] > 3:
            logger.critical("Couldn't recover from connection error. Restarting current process.")
            restart_control(quiet=True)
        else:
            logger.info(f"Restarting in {FAILED_CONNECTIONS['count'] * 10} seconds.")
            time.sleep(FAILED_CONNECTIONS['count'] * 10)
            handler()
    except RecursionError as error:
        logger.error(error)
        restart_control(quiet=True)
