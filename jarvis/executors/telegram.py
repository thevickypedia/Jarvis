import os
import time
from urllib.parse import urljoin

from jarvis.executors import controls, internet, process_map
from jarvis.modules.exceptions import BotInUse, BotWebhookConflict, EgressErrors
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import models
from jarvis.modules.telegram import bot, webhook
from jarvis.modules.utils import support

FAILED_CONNECTIONS = {"count": 0}


def get_webhook_origin(retry: int) -> str:
    """Get the telegram bot webhook origin.

    Args:
        retry: Number of retry attempts to get public URL.

    Returns:
        str:
        Public URL where the telegram webhook is hosted.
    """
    if models.env.bot_webhook:
        return str(models.env.bot_webhook)
    logger.info("Attempting to connect via webhook. ETA: 60 seconds.")
    for i in range(retry):
        if url := internet.get_tunnel(False):
            logger.info(
                "Public URL was fetched on %s attempt", support.ENGINE.ordinal(i + 1)
            )
            return url
        time.sleep(3)


def telegram_api(webhook_trials: int = 20) -> None:
    """Initiates polling for new messages.

    Args:
        webhook_trials: Number of retry attempts to get the public URL for Jarvis (if hosted via Ngrok)

    See Also:
        - ``webhook_trials`` is set to 3 when polling fails (which is already a fallback for webhook retries)

    Handles:
        - BotWebhookConflict: When there's a broken webhook set already.
        - BotInUse: Restarts polling to take control over.
        - EgressErrors: Initiates after 10, 20 or 30 seconds. Depends on retry count. Restarts after 3 attempts.
    """
    multiprocessing_logger(filename=os.path.join("logs", "telegram_api_%d-%m-%Y.log"))
    if not models.env.bot_token:
        logger.info("Bot token is required to start the Telegram Bot")
        return
    if (public_url := get_webhook_origin(webhook_trials)) and (
        response := webhook.set_webhook(
            base_url=bot.BASE_URL,
            webhook=urljoin(public_url, models.env.bot_endpoint),
            logger=logger,
        )
    ):
        logger.info("Telegram API will be hosted via webhook.")
        logger.info(response)
        process_map.remove(telegram_api.__name__)
        return
    try:
        bot.poll_for_messages()
    except BotWebhookConflict as error:
        # At this point, its be safe to remove the dead webhook
        logger.error(error)
        webhook.delete_webhook(base_url=bot.BASE_URL, logger=logger)
        telegram_api(3)
    except BotInUse as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        telegram_api(3)
    except EgressErrors as error:
        logger.error(error)
        FAILED_CONNECTIONS["count"] += 1
        if FAILED_CONNECTIONS["count"] > 3:
            logger.critical(
                "ATTENTION::Couldn't recover from connection error. Restarting current process."
            )
            controls.restart_control(quiet=True)
        else:
            logger.info("Restarting in %d seconds.", FAILED_CONNECTIONS["count"] * 10)
            time.sleep(FAILED_CONNECTIONS["count"] * 10)
            telegram_api(3)
    except Exception as error:
        logger.critical("ATTENTION: %s", error.__str__())
        controls.restart_control(quiet=True)
