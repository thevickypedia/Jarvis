import secrets
from http import HTTPStatus
from json.decoder import JSONDecodeError

from fastapi.exceptions import HTTPException
from fastapi.requests import Request

from jarvis.api.logger import logger
from jarvis.modules.models import models
from jarvis.modules.telegram import bot


def two_factor(request: Request) -> bool:
    """Two factor verification for messages coming via webhook.

    Args:
        request: Request object from FastAPI.

    Returns:
        bool:
        Flag to indicate the calling function if the auth was successful.
    """
    if models.env.bot_secret:
        if secrets.compare_digest(
            request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""),
            models.env.bot_secret,
        ):
            return True
    else:
        logger.warning("Use the env var bot_secret to secure the webhook interaction")
        return True


async def telegram_webhook(request: Request):
    """Invoked when a new message is received from Telegram API.

    Args:
        request: Request instance.

    Raises:

        HTTPException:
            - 406: If the request payload is not JSON format-able.
    """
    logger.debug(
        "Connection received from %s via %s",
        request.client.host,
        request.headers.get("host"),
    )
    try:
        response = await request.json()
    except JSONDecodeError as error:
        logger.error(error)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.real,
            detail=HTTPStatus.BAD_REQUEST.phrase,
        )
    # Ensure only the owner who set the webhook can interact with the Bot
    if not two_factor(request):
        logger.error("Request received from a non-webhook source")
        logger.error(response)
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN.real, detail=HTTPStatus.FORBIDDEN.phrase
        )
    if payload := response.get("message"):
        logger.debug(response)
        bot.process_request(payload)
    else:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
            detail=HTTPStatus.UNPROCESSABLE_ENTITY.phrase,
        )
