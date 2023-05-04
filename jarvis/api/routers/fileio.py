import os
from http import HTTPStatus

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from jarvis.api.modals.authenticator import OFFLINE_PROTECTOR
from jarvis.api.squire.logger import logger
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models

router = APIRouter()


@router.get(path="/list-files", dependencies=OFFLINE_PROTECTOR)
async def list_files():
    """Get all YAML files from fileio and all log files from logs directory.

    Returns:

        Dict[str, List[str]]:
        Dictionary of files that can be downloaded or uploaded.
    """
    return {**{"logs": [file_ for __path, __directory, __file in os.walk('logs') for file_ in __file]},
            **{"fileio": [f for f in os.listdir(models.fileio.root) if f.endswith('.yaml')]}}


@router.get(path="/get-file", response_class=FileResponse, dependencies=OFFLINE_PROTECTOR)
async def get_file(filename: str):
    """Download a particular YAML file from fileio or log file from logs directory.

    Args:

        filename: Name of the file that has to be downloaded.

    Returns:

        FileResponse:
        Returns the FileResponse object of the file.
    """
    allowed_files = await list_files()
    if filename not in allowed_files["fileio"] + allowed_files["logs"]:
        raise APIResponse(status_code=HTTPStatus.NOT_ACCEPTABLE.real,
                          detail=f"{filename!r} is either unavailable or not allowed.\n"
                                 f"Downloadable files:{allowed_files}")
    if filename.endswith(".log"):
        if path := [__path for __path, __directory, __file in os.walk("logs") if filename in __file]:
            target_file = os.path.join(path[0], filename)
        else:
            logger.critical("ATTENTION::'%s' wasn't found.", filename)
            raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.phrase)
    else:
        target_file = os.path.join(models.fileio.root, filename)
    logger.info("Requested file: '%s' for download.", filename)
    return FileResponse(status_code=HTTPStatus.OK.real, path=target_file, media_type="text/yaml", filename=filename)


@router.post(path="/put-file", dependencies=OFFLINE_PROTECTOR)
async def put_file(file: UploadFile):
    """Upload a particular YAML file to the fileio directory.

    Args:

        file: Takes the UploadFile object as an argument.
    """
    allowed_files = await list_files()
    if file.filename not in allowed_files["fileio"]:
        raise APIResponse(status_code=HTTPStatus.NOT_ACCEPTABLE.real,
                          detail=f"{file.filename!r} is not allowed for an update.\n"
                                 f"Upload-able files:{allowed_files['fileio']}")
    logger.info("Requested file: '%s' for upload.", file.filename)
    content = await file.read()
    with open(os.path.join(models.fileio.root, file.filename), "wb") as f_stream:
        f_stream.write(content)
    raise APIResponse(status_code=HTTPStatus.OK.real, detail=f"{file.filename!r} was uploaded to {models.fileio.root}.")
