import os
from http import HTTPStatus
from typing import NoReturn, Set

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from api.modals.authenticator import OFFLINE_PROTECTOR
from api.squire.logger import logger
from modules.exceptions import APIResponse
from modules.models import models

router = APIRouter()


@router.get(path="/list-files", dependencies=OFFLINE_PROTECTOR)
async def list_files() -> Set[str]:
    """Get all YAML files from fileio directory.

    Returns:

        Set:
        Set of files that can be downloaded or uploaded.
    """
    return {f for f in os.listdir(models.fileio.root) if f.endswith('.yaml')}


@router.get(path="/get-file", response_class=FileResponse, dependencies=OFFLINE_PROTECTOR)
async def get_file(filename: str) -> FileResponse:
    """Download a particular YAML file from fileio directory.

    Args:

        filename: Name of the file that has to be downloaded.

    Returns:

        FileResponse:
        Returns a download-able version of the file.
    """
    allowed_files = await list_files()
    if filename not in allowed_files:
        raise APIResponse(status_code=HTTPStatus.NOT_ACCEPTABLE.real,
                          detail=f"{filename!r} is either unavailable or not allowed.\n"
                                 f"Downloadable files:{allowed_files}")
    target_file = os.path.join(models.fileio.root, filename)
    logger.info(f"Requested file: {filename!r} for download.")
    return FileResponse(status_code=HTTPStatus.OK.real, path=target_file, media_type="text/yaml", filename=filename)


@router.post(path="/put-file", dependencies=OFFLINE_PROTECTOR)
async def put_file(file: UploadFile) -> NoReturn:
    """Upload a particular YAML file to the fileio directory.

    Args:

        file: Takes the UploadFile object as an argument.
    """
    allowed_files = await list_files()
    if file.filename not in allowed_files:
        raise APIResponse(status_code=HTTPStatus.NOT_ACCEPTABLE.real,
                          detail=f"{file.filename!r} is not allowed for an update.\n"
                                 f"Upload-able files:{allowed_files}")
    logger.info(f"Requested file: {file.filename!r} for upload.")
    content = await file.read()
    with open(os.path.join(models.fileio.root, file.filename), "wb") as f_stream:
        f_stream.write(content)
    raise APIResponse(status_code=HTTPStatus.OK.real, detail=f"{file.filename!r} was uploaded to {models.fileio.root}.")
