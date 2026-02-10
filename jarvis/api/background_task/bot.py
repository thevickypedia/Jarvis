import asyncio
from dataclasses import dataclass

import requests

from jarvis.executors import telegram
from jarvis.modules.exceptions import BotInUse, BotWebhookConflict, EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.telegram import bot, webhook

MAX_FAILED_CONNECTIONS = 30
EXPONENTIAL_BACKOFF_FACTOR = 3


@dataclass
class TelegramBeat:
    """Telegram beat class.

    >>> TelegramBeat

    """

    offset: int = 0
    failed_connections: int = 0

    # Loop sequence:
    #   1. Try telegram webhook for 60s (default)
    #   2. Start polling for new messages
    poll_for_messages: bool = False
    restart_loop: bool = False


telegram_beat = TelegramBeat()


async def init(ct: int = 20):
    _flag = await telegram.telegram_api(webhook_trials=ct)
    if _flag:
        logger.info("Polling for incoming messages...")
    telegram_beat.poll_for_messages = _flag


async def restart_loop(after: int):
    # Stop polling immediately in the main loop
    telegram_beat.poll_for_messages = False
    # Sleep for the # of seconds after which the loop should be restarted
    await asyncio.sleep(after)
    # Set restart loop to True, which will re-trigger init with 3s trials
    telegram_beat.restart_loop = True


async def telegram_executor() -> None:
    """Poll for new Telegram messages."""
    try:
        # TODO: offset is not being rendered right - last message is remembered
        #   Not fully back-tested
        offset = bot.poll_for_messages(telegram_beat.offset)
        if offset is not None:
            telegram_beat.offset = offset
    except BotWebhookConflict as error:
        # At this point, its be safe to remove the dead webhook
        logger.error(error)
        webhook.delete_webhook(base_url=bot.BASE_URL, logger=logger)
        await restart_loop(after=1)
    except BotInUse as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        await restart_loop(after=1)
    except EgressErrors as error:
        # ReadTimeout is just saying that there were no messages to read within the time specified
        if isinstance(error, requests.exceptions.ReadTimeout):
            return
        logger.error(error)
        telegram_beat.failed_connections += 1
        if telegram_beat.failed_connections > MAX_FAILED_CONNECTIONS:
            logger.critical("ATTENTION::Couldn't recover from connection error. Restarting current process.")
            delay = telegram_beat.failed_connections * EXPONENTIAL_BACKOFF_FACTOR
            logger.info("Restarting in %d seconds.", delay)
            await restart_loop(after=delay)
    except Exception as error:
        logger.critical("ATTENTION: %s", error.__str__())
        # TODO: Implement notification for un-recoverable errors
