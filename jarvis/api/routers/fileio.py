import os
from datetime import datetime
from http import HTTPStatus

from fastapi import UploadFile
from fastapi.responses import FileResponse

from jarvis.api.logger import logger
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models


async def list_files():
    """Get all YAML files from fileio and all log files from logs directory.

    Returns:

        Dict[str, List[str]]:
        Dictionary of files that can be downloaded or uploaded.
    """
    return {
        **{
            "logs": [
                file_
                for __path, __directory, __file in os.walk("logs")
                for file_ in __file
            ]
        },
        **{
            "fileio": [f for f in os.listdir(models.fileio.root) if f.endswith(".yaml")]
        },
        **{
            "uploads": [
                f for f in os.listdir(models.fileio.uploads) if not f.startswith(".")
            ]
        },
    }


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
        raise APIResponse(
            status_code=HTTPStatus.NOT_ACCEPTABLE.real,
            detail=f"{filename!r} is either unavailable or not allowed.\n"
            f"Downloadable files:{allowed_files}",
        )
    if filename.endswith(".log"):
        if path := [
            __path
            for __path, __directory, __file in os.walk("logs")
            if filename in __file
        ]:
            target_file = os.path.join(path[0], filename)
        else:
            logger.critical("ATTENTION::'%s' wasn't found.", filename)
            raise APIResponse(
                status_code=HTTPStatus.NOT_FOUND.real,
                detail=HTTPStatus.NOT_FOUND.phrase,
            )
    else:
        target_file = os.path.join(models.fileio.root, filename)
    logger.info("Requested file: '%s' for download.", filename)
    return FileResponse(
        status_code=HTTPStatus.OK.real,
        path=target_file,
        media_type="text/yaml",
        filename=filename,
    )


async def put_file(file: UploadFile):
    """Upload a particular YAML file to the fileio directory.

    Args:

        file: Takes the UploadFile object as an argument.
    """
    logger.info("Requested file: '%s' for upload.", file.filename)
    content = await file.read()
    allowed_files = await list_files()
    if file.filename not in allowed_files["fileio"]:
        with open(
            os.path.join(
                models.fileio.uploads,
                f"{datetime.now().strftime('%d_%B_%Y-%I_%M_%p')}-{file.filename}",
            ),
            "wb",
        ) as f_stream:
            f_stream.write(content)
        raise APIResponse(
            status_code=HTTPStatus.ACCEPTED.real,
            detail=f"{file.filename!r} is not allowed for an update.\n"
            "Hence storing as a standalone file.",
        )
    with open(os.path.join(models.fileio.root, file.filename), "wb") as f_stream:
        f_stream.write(content)
    raise APIResponse(
        status_code=HTTPStatus.OK.real,
        detail=f"{file.filename!r} was uploaded to {models.fileio.root}.",
    )
