import importlib
import logging
import os
import sys
import time
from typing import NoReturn

from jarvis.executors.controls import restart_control
from jarvis.modules.exceptions import BotInUse, EgressErrors
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.telegram.bot import TelegramBot

importlib.reload(module=logging)

FAILED_CONNECTIONS = {'count': 0}


def telegram_api() -> NoReturn:
    """Initiates polling for new messages.

    Handles:
        - BotInUse: Restarts polling to take control over.
        - ConnectionError: Initiates after 10, 20 or 30 seconds. Depends on retry count. Shuts off after 3 attempts.
    """
    config.multiprocessing_logger(filename=os.path.join('logs', 'telegram_%d-%m-%Y.log'))
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
        telegram_api()
    except EgressErrors as error:
        logger.error(error)
        FAILED_CONNECTIONS['count'] += 1
        if FAILED_CONNECTIONS['count'] > 3:
            logger.critical("ATTENTION::Couldn't recover from connection error. Restarting current process.")
            restart_control(quiet=True)
        else:
            logger.info(f"Restarting in {FAILED_CONNECTIONS['count'] * 10} seconds.")
            time.sleep(FAILED_CONNECTIONS['count'] * 10)
            telegram_api()
    except RecursionError as error:
        logger.error(error)
        restart_control(quiet=True)
