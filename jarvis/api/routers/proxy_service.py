import re
from http import HTTPStatus

import requests
from fastapi import Request, Response
from pydantic import HttpUrl

from jarvis.api.logger import logger
from jarvis.modules.exceptions import APIResponse, EgressErrors


def is_valid_media_type(media_type: str) -> bool:
    """Regular expression to match valid media types.

    Args:
        media_type: Takes the media type to be validated.

    Returns:
        bool:
        Returns a boolean value to indicate validity.
    """
    media_type_pattern = r"^[a-zA-Z]+/[a-zA-Z0-9\-\.\+]+$"
    return bool(re.match(media_type_pattern, media_type))


async def proxy_service_api(request: Request, origin: HttpUrl, output: str):
    """API endpoint to act as a proxy for GET calls.

    See Also:
        This is primarily to solve the CORS restrictions on web browsers.

    Examples:
        .. code-block:: bash

            curl -X 'GET' 'http://0.0.0.0:{PORT}/proxy?origin=http://example.com&output=application/xml'

    Args:
        request: FastAPI request module.
        origin: Origin URL as query string.
        output: Output media type.
    """
    logger.info(
        "Connection received from %s via %s using %s",
        request.client.host,
        request.headers.get("host"),
        request.headers.get("user-agent"),
    )
    try:
        response = requests.get(url=origin, allow_redirects=True, verify=False)
        if response.ok:
            if is_valid_media_type(output):
                return Response(content=response.text, media_type=output)
            raise APIResponse(
                status_code=HTTPStatus.BAD_REQUEST.real,
                detail=HTTPStatus.BAD_REQUEST.phrase,
            )
        raise APIResponse(status_code=response.status_code, detail=response.text)
    except EgressErrors as error:
        logger.error(error)
        raise APIResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE.real,
            detail=HTTPStatus.SERVICE_UNAVAILABLE.phrase,
        )
