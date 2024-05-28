import logging

import requests
from pydantic import HttpUrl

from jarvis.modules.models import models


def get_webhook(base_url: str, logger: logging.Logger):
    """Get webhook information.

    References:
        https://core.telegram.org/bots/api#getwebhookinfo
    """
    get_info = f"{base_url}/getWebhookInfo"
    response = requests.get(url=get_info)
    if response.ok:
        logger.info(response.json())
        return response.json()
    response.raise_for_status()


def delete_webhook(base_url: str | HttpUrl, logger: logging.Logger):
    """Delete webhook.

    References:
        https://core.telegram.org/bots/api#deletewebhook
    """
    del_info = f"{base_url}/setWebhook"
    response = requests.post(url=del_info, params=dict(url=None))
    if response.ok:
        logger.info("Webhook has been removed.")
        return response.json()
    response.raise_for_status()


def set_webhook(
    base_url: HttpUrl | str, webhook: HttpUrl | str, logger: logging.Logger
):
    """Set webhook.

    References:
        https://core.telegram.org/bots/api#setwebhook
    """
    put_info = f"{base_url}/setWebhook"
    payload = dict(url=webhook, secret_token=models.env.bot_secret)
    if models.env.bot_webhook_ip:
        payload["ip_address"] = models.env.bot_webhook_ip.__str__()
    logger.debug(payload)
    if models.env.bot_certificate:
        response = requests.post(
            url=put_info,
            data=payload,
            files={
                "certificate": (
                    models.env.bot_certificate.stem + models.env.bot_certificate.suffix,
                    models.env.bot_certificate.certificate.open(mode="rb"),
                )
            },
        )
    else:
        response = requests.post(url=put_info, params=payload)
    if response.ok:
        logger.info("Webhook has been set to: %s", webhook)
        return response.json()
    else:
        logger.error(response.text)
