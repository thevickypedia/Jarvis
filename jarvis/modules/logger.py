import importlib
import logging
import os
from datetime import datetime
from logging import Formatter
from logging.config import dictConfig

from pydantic import BaseModel

from jarvis.modules.builtin_overrides import AddProcessName
from jarvis.modules.models import models

if not os.path.isdir("logs"):
    os.mkdir("logs")

DEFAULT_LOG_FORM = "%(asctime)s - %(levelname)s - [%(processName)s:%(module)s:%(lineno)d] - %(funcName)s - %(message)s"
DEFAULT_FORMATTER = logging.Formatter(
    datefmt="%b-%d-%Y %I:%M:%S %p", fmt=DEFAULT_LOG_FORM
)

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
    }
)
logging.getLogger("_code_cache").propagate = False

logger = logging.getLogger("JARVIS")
if models.env.debug:
    logger.setLevel(level=logging.DEBUG)
else:
    logger.setLevel(level=logging.INFO)


def multiprocessing_logger(
    filename: str, log_format: Formatter = DEFAULT_FORMATTER
) -> str:
    """Remove existing handlers and adds a new handler when a child process kicks in.

    Args:
        filename: Filename where the subprocess should log.
        log_format: Custom log format dedicated for each process.

    See Also:
        This will override the main logger and add a new logger pointing to the given filename.

    Returns:
        str:
        Actual log filename with datetime converted.
    """
    importlib.reload(logging)
    logger.propagate = False
    # Remove existing handlers
    for _handler in logger.handlers:
        logger.removeHandler(hdlr=_handler)
    log_handler = custom_handler(filename=filename, log_format=log_format)
    logger.addHandler(hdlr=log_handler)
    # Remove existing filters from the new log handler
    for _filter in logger.filters:
        logger.removeFilter(_filter)
    logger.addFilter(filter=AddProcessName(process_name=models.settings.pname))
    return log_handler.baseFilename


class APIConfig(BaseModel):
    """Custom log configuration to redirect all uvicorn logs to individual log files.

    >>> APIConfig

    """

    DEFAULT_LOG_LEVEL: str = "INFO"

    ACCESS_LOG_FILENAME: str = datetime.now().strftime(
        os.path.join("logs", "jarvis_api_access_%d-%m-%Y.log")
    )
    DEFAULT_LOG_FILENAME: str = datetime.now().strftime(
        os.path.join("logs", "jarvis_api_%d-%m-%Y.log")
    )

    ACCESS_LOG_FORMAT: str = (
        '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    ERROR_LOG_FORMAT: str = "%(levelname)s\t %(message)s"

    LOG_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": DEFAULT_LOG_FORM,
                "use_colors": False,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": ACCESS_LOG_FORMAT,
                "use_colors": False,
            },
            "error": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": ERROR_LOG_FORMAT,
                "use_colors": False,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": DEFAULT_LOG_FILENAME,
            },
            "access": {
                "formatter": "access",
                "class": "logging.FileHandler",
                "filename": ACCESS_LOG_FILENAME,
            },
            "error": {
                "formatter": "error",
                "class": "logging.FileHandler",
                "filename": DEFAULT_LOG_FILENAME,
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": DEFAULT_LOG_LEVEL},
            "uvicorn.access": {"handlers": ["access"], "level": DEFAULT_LOG_LEVEL},
            "uvicorn.error": {
                "handlers": ["error"],
                "level": DEFAULT_LOG_LEVEL,
                "propagate": True,  # Since FastAPI is threaded
            },
        },
    }


def log_file(filename: str) -> str:
    """Creates a log file and writes the headers into it.

    Returns:
        str:
        Log filename.
    """
    return datetime.now().strftime(filename)


def custom_handler(
    filename: str = None, log_format: logging.Formatter = None
) -> logging.FileHandler:
    """Creates a FileHandler, sets the log format and returns it.

    Returns:
        logging.FileHandler:
        Returns file handler.
    """
    handler = logging.FileHandler(
        filename=log_file(
            filename=filename or os.path.join("logs", "jarvis_%d-%m-%Y.log")
        ),
        mode="a",
    )
    handler.setFormatter(fmt=log_format or DEFAULT_FORMATTER)
    return handler


logger.addHandler(hdlr=custom_handler())
