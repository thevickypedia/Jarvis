import os
from http import HTTPStatus
from typing import Optional

from fastapi import Header, Request

from jarvis.api.logger import logger
from jarvis.executors import ciphertext, files
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models


async def secure_send_api(
    request: Request, key: str, access_token: Optional[str] = Header(None)
):
    """API endpoint to share/retrieve secrets.

    Args:
        request: FastAPI request module.
        key: Secret key to be retrieved.
        access_token: Access token for the secret to be retrieved.

    Raises:

        - 200: For a successful authentication (secret will be returned)
        - 400: For a bad request if headers are passed with underscore
        - 401: For a failed authentication (if the access token doesn't match)
        - 404: If the ``secure_send`` mapping file is unavailable
    """
    if not key:
        raise APIResponse(
            status_code=HTTPStatus.BAD_REQUEST.real,
            detail="key is mandatory to retrieve the secret",
        )
    logger.info(
        "Connection received from %s via %s using %s",
        request.client.host,
        request.headers.get("host"),
        request.headers.get("user-agent"),
    )
    token = access_token or request.headers.get("access-token")
    if not token:
        logger.warning("'access-token' not received in headers")
        raise APIResponse(
            status_code=HTTPStatus.UNAUTHORIZED.real,
            detail=HTTPStatus.UNAUTHORIZED.phrase,
        )
    if token.startswith("\\"):
        token = bytes(token, "utf-8").decode(encoding="unicode_escape")
    if os.path.isfile(models.fileio.secure_send):
        secure_strings = files.get_secure_send()
        if secret_payload := secure_strings.get(token):
            logger.info("secret was accessed using secure token, deleting secret")
            files.delete_secure_send(token)
            if secret_value := secret_payload.get(key):
                decrypted = ciphertext.decrypt(secret_value)
                raise APIResponse(status_code=HTTPStatus.OK.real, detail=decrypted)
            else:
                raise APIResponse(
                    status_code=HTTPStatus.BAD_REQUEST.real,
                    detail=f"Invalid key [{key}] provided",
                )
        else:
            logger.info(
                "secret access was denied for token: %s, available tokens: %s",
                token,
                [*secure_strings.keys()],
            )
            raise APIResponse(
                status_code=HTTPStatus.UNAUTHORIZED.real,
                detail=HTTPStatus.UNAUTHORIZED.phrase,
            )
    else:
        logger.info("'%s' not found", models.fileio.secure_send)
        raise APIResponse(
            status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.phrase
        )
