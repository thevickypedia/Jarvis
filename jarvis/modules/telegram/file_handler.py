# noinspection PyUnresolvedReferences
"""Custom document file IO handler for Telegram API.

>>> FileHandler

"""

import os
from typing import Dict

from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models


def _list_files() -> Dict[str, str]:
    """Get all YAML files from fileio and all log files from logs directory.

    Returns:
        Dict[str, List[str]]:
        Dictionary of files that can be downloaded or uploaded.
    """
    return {**{"logs": [file_ for __path, __directory, __file in os.walk('logs') for file_ in __file]},
            **{"fileio": [f for f in os.listdir(models.fileio.root) if f.endswith('.yaml')]}}


def list_files() -> str:
    """List all downloadable files.

    Returns:
        str:
        Returns response as a string.
    """
    all_files = _list_files()
    joined_logs = '\n'.join(all_files['logs'])
    joined_fileio = '\n'.join(all_files['fileio'])
    return f"{joined_logs}\n\n{joined_fileio}"


def get_file(filename: str) -> Dict:
    """Download a particular YAML file from fileio or log file from logs directory.

    Args:
        filename: Name of the file that has to be downloaded.

    Returns:
        Response:
        Returns the Response object to further process send document via API.
    """
    allowed_files = _list_files()
    if filename not in allowed_files["fileio"] + allowed_files["logs"]:
        return {'ok': False,
                'msg': f"{filename!r} is either unavailable or not allowed. "
                       "Please use the command 'list files' to get a list of downloadable files."}
    if filename.endswith(".log"):
        if path := [__path for __path, __directory, __file in os.walk("logs") if filename in __file]:
            target_file = os.path.join(path[0], filename)
        else:
            logger.critical("ATTENTION::'%s' wasn't found.", filename)
            return {
                "ok": False,
                "msg": f"{filename!r} was not found. "
                       "Please use the command 'list files' to get a list of downloadable files."
            }
    else:
        target_file = os.path.join(models.fileio.root, filename)
    logger.info("Requested file: '%s' for download.", filename)
    return {'ok': True, 'msg': target_file}


def put_file(filename: str, file_content: bytes) -> str:
    """Upload a particular YAML file to the fileio directory.

    Args:
        filename: Name of the file.
        file_content: Content of the file.

    Returns:
        str:
        Response to the user.
    """
    allowed_files = _list_files()
    if filename not in allowed_files["fileio"]:
        return f"{filename!r} is not allowed for an update."
    logger.info("Requested file: '%s' for upload.", filename)
    with open(os.path.join(models.fileio.root, filename), "wb") as f_stream:
        f_stream.write(file_content)
    return f"{filename!r} was uploaded to {os.path.basename(models.fileio.root)}."
