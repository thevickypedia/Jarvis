import asyncio
from dataclasses import dataclass

import requests

from jarvis.executors import communicator, telegram
from jarvis.modules.exceptions import (
    BotInUse,
    BotTokenInvalid,
    BotWebhookConflict,
    EgressErrors,
)
from jarvis.modules.logger import logger
from jarvis.modules.telegram import bot, webhook

MAX_FAILED_CONNECTIONS = 10
EXPONENTIAL_BACKOFF_FACTOR = 3


@dataclass
class TelegramBeat:
    """Telegram beat class.

    >>> TelegramBeat

    """

    offset: int = 0
    failed_connections: int = 0

    poll_for_messages: bool = False
    restart_loop: bool = False


telegram_beat = TelegramBeat()


async def init(max_webhook_attempts: int = 20) -> None:
    """Initialize telegram API and decide to choose webhook vs long polling.

    Args:
        max_webhook_attempts: Maximum number of attempts to try webhook connection before starting long polling.
    """
    _flag = await telegram.telegram_api(webhook_trials=max_webhook_attempts)
    if _flag:
        logger.info("Polling for incoming messages...")
    telegram_beat.poll_for_messages = _flag


async def restart_loop(after: int) -> None:
    """Restart telegram polling.

    Args:
        after: Delay in seconds.

    See Also:
        - Stops telegram polling immediately.
        - Sleeps for the mentioned delay.
        - Sets the restart_loop flag to true.
    """
    # Stop polling immediately in the main loop
    telegram_beat.poll_for_messages = False
    # Sleep for the # of seconds after which the loop should be restarted
    await asyncio.sleep(after)
    # Set restart loop to True, which will re-trigger init with 3s trials
    telegram_beat.restart_loop = True


async def terminate(reason: str) -> None:
    """Terminate telegram polling.

    Args:
        reason: Reason for termination.
    """
    logger.info("Terminating telegram polling due to %s", reason)
    telegram_beat.poll_for_messages = False
    telegram_beat.restart_loop = False


async def telegram_executor() -> None:
    """Poll for new Telegram messages.

    Handles:
        - BotWebhookConflict: Handles dead webhook connection and restarts loop.
        - BotInUse: Conflicting bot usage on webhook vs long polling.
        - BotTokenInvalid: Handles invalid auth token by terminating session.
        - EgressErrors: Dynamically handles failed connections.
        - Exception: Broad exception handler to terminate loop for unknown errors.
    """
    try:
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
        logger.info("Restarting for webhook to take over...")
        await restart_loop(after=1)
    except BotTokenInvalid as error:
        logger.error("ATTENTION: %s", error)
        communicator.notify(subject="JARVIS: Telegram", body=f"Telegram task failed due to {type(error).__name__}")
        await terminate(reason=type(error).__name__)
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
        logger.critical("ATTENTION: %s", error)
        communicator.notify(subject="JARVIS: Telegram", body=f"Telegram task failed due to {type(error).__name__}")
        await terminate(reason=type(error).__name__)
