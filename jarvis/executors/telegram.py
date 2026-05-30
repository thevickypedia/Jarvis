from urllib.parse import urljoin

from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.telegram import bot, webhook


async def telegram_api() -> bool:
    """Initiates polling for new messages.

    Handles:
        - BotWebhookConflict: When there's a broken webhook set already.
        - BotInUse: Restarts polling to take control over.
        - EgressErrors: Initiates after 10, 20 or 30 seconds. Depends on retry count. Restarts after 3 attempts.
    """
    if not models.env.bot_token:
        logger.info("Bot token is required to start the Telegram Bot")
        return False
    if models.env.bot_webhook and webhook.set_webhook(
        base_url=bot.BASE_URL,
        webhook=urljoin(str(models.env.bot_webhook), models.env.bot_endpoint),
        logger=logger,
    ):
        logger.info("Telegram API will be hosted via webhook.")
        return False
    return True
