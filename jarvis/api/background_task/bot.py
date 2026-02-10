import asyncio
from dataclasses import dataclass

from jarvis.modules.exceptions import BotInUse, BotWebhookConflict, EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.telegram import bot, webhook


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
    retry_webhook: bool = False
    poll_for_messages: bool = False
    restart_loop: bool = False


telegram_beat = TelegramBeat()


async def telegram_executor() -> None:
    """Poll for new Telegram messages."""
    try:
        # TODO: offset is not being rendered right - last message is remembered
        # TODO: polling **must** be a thread/async task - if network disconnects - this will become a blocker
        offset = bot.poll_for_messages(telegram_beat.offset)
        if offset is not None:
            telegram_beat.offset = offset
    except BotWebhookConflict as error:
        # At this point, its be safe to remove the dead webhook
        logger.error(error)
        webhook.delete_webhook(base_url=bot.BASE_URL, logger=logger)
        # TODO: Need to try webhook for 3s, and fall back to polling
        # telegram_api(3)
    except BotInUse as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        # TODO: Need to try webhook for 3s, and fall back to polling
        # telegram_api(3)
    except EgressErrors as error:
        logger.error(error)
        telegram_beat.failed_connections += 1
        if telegram_beat.failed_connections > 3:
            logger.critical("ATTENTION::Couldn't recover from connection error. Restarting current process.")
            # TODO: Implement a restart mechanism
            # controls.restart_control(quiet=True)
        else:
            logger.info(
                "Restarting in %d seconds.",
                telegram_beat.failed_connections * 10,
            )
            await asyncio.sleep(telegram_beat.failed_connections * 10)
            # TODO: Need to try webhook for 3s, and fall back to polling
            # telegram_api(3)
    except Exception as error:
        logger.critical("ATTENTION: %s", error.__str__())
        # TODO: Implement a restart mechanism
        # controls.restart_control(quiet=True)
