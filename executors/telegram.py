import importlib
import logging
import time
from logging.config import dictConfig
from typing import NoReturn

import requests

from executors.controls import restart_control
from modules.models import config, models
from modules.telegram.bot import TelegramBot

env = models.env

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
    if not env.bot_token:
        logger.info("Bot token is required to start the Telegram Bot")
        return
    try:
        TelegramBot().poll_for_messages()
    except OverflowError as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        handler()
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as error:
        logger.critical(error)
        FAILED_CONNECTIONS['calls'] += 1
        if FAILED_CONNECTIONS['calls'] > 3:
            logger.critical("Couldn't recover from connection error. Restarting main module..")
            restart_control(quiet=True)
        else:
            logger.info(f"Restarting in {FAILED_CONNECTIONS['calls'] * 10} seconds..")
            time.sleep(FAILED_CONNECTIONS['calls'] * 10)
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
