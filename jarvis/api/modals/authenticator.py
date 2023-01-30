import secrets
from http import HTTPStatus

from fastapi import Depends
from fastapi.security import HTTPBasicCredentials, HTTPBearer

from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models

security = HTTPBearer()


async def offline_has_access(token: HTTPBasicCredentials = Depends(security)) -> None:
    """Validates the token if mentioned as a dependency.

    Args:
        token: Takes the authorization header token as an argument.

    Raises:
        APIResponse:
        - 401: If authorization is invalid.
    """
    auth = token.dict().get('credentials', '')
    if auth.startswith('\\'):
        auth = bytes(auth, "utf-8").decode(encoding="unicode_escape")
    if secrets.compare_digest(auth, models.env.offline_pass):
        return
    raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])


async def robinhood_has_access(token: HTTPBasicCredentials = Depends(security)) -> None:
    """Validates the token if mentioned as a dependency.

    Args:
        token: Takes the authorization header token as an argument.

    Raises:
        APIResponse:
        - 401: If authorization is invalid.
    """
    auth = token.dict().get('credentials')
    if auth.startswith('\\'):
        auth = bytes(auth, "utf-8").decode(encoding="unicode_escape")
    if secrets.compare_digest(auth, models.env.robinhood_endpoint_auth):
        return
    raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])


async def surveillance_has_access(token: HTTPBasicCredentials = Depends(security)) -> None:
    """Validates the token if mentioned as a dependency.

    Args:
        token: Takes the authorization header token as an argument.

    Raises:
        APIResponse:
        - 401: If authorization is invalid.
    """
    auth = token.dict().get('credentials')
    if auth.startswith('\\'):
        auth = bytes(auth, "utf-8").decode(encoding="unicode_escape")
    if secrets.compare_digest(auth, models.env.surveillance_endpoint_auth):
        return
    raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])


OFFLINE_PROTECTOR = [Depends(dependency=offline_has_access)]
ROBINHOOD_PROTECTOR = [Depends(dependency=robinhood_has_access)]
SURVEILLANCE_PROTECTOR = [Depends(dependency=surveillance_has_access)]
