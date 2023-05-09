import os
from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from jarvis.api.modals.authenticator import OFFLINE_PROTECTOR
from jarvis.api.squire import logger
from jarvis.modules.conditions import keywords as keywords_mod
from jarvis.modules.exceptions import APIResponse

router = APIRouter()


@router.get(path="/", response_class=RedirectResponse, include_in_schema=False)
async def redirect_index():
    """Redirect to docs in read-only mode.

    Returns:

        str:
        Redirects the root endpoint / url to read-only doc location.
    """
    return "/redoc"


@router.get(path="/health", include_in_schema=False)
async def health():
    """Health Check for OfflineCommunicator.

    Raises:

        - 200: For a successful health check.
    """
    raise APIResponse(status_code=HTTPStatus.OK, detail=HTTPStatus.OK.phrase)


@router.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon():
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:

        FileResponse:
        Returns the favicon.ico file as FileResponse to support the front-end.
    """
    # This logger import should not be changed to make sure the path is detected using it
    filepath = os.path.join(os.path.dirname(logger.__file__), 'favicon.ico')
    if os.path.exists(filepath):
        return FileResponse(filename=os.path.basename(filepath), path=filepath, status_code=HTTPStatus.OK.real)
    logger.logger.warning("'favicon.ico' is missing or the path is messed up. Fix this to avoid errors on front-end")


@router.get(path="/keywords", dependencies=OFFLINE_PROTECTOR)
async def keywords():
    """Converts the keywords and conversations into a dictionary of key-value pairs.

    Returns:

        Dict[str, List[str]]:
        Key-value pairs of the keywords file.
    """
    return {k: v for k, v in keywords_mod.keywords.items() if isinstance(v, list)}
