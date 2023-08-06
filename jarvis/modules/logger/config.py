# noinspection PyUnresolvedReferences
"""Module for custom logger configurations.

>>> Config

"""

import os
from datetime import datetime
from logging import Formatter

from pydantic import BaseModel

from jarvis.modules.builtin_overrides import AddProcessName
from jarvis.modules.logger import custom_logger
from jarvis.modules.models import models


def multiprocessing_logger(filename: str, log_format: Formatter = None) -> str:
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
    custom_logger.logger.propagate = False
    # Remove existing handlers
    for _handler in custom_logger.logger.handlers:
        custom_logger.logger.removeHandler(hdlr=_handler)
    log_handler = custom_logger.custom_handler(filename=filename, log_format=log_format)
    custom_logger.logger.addHandler(hdlr=log_handler)
    # Remove existing filters from the new log handler
    for _filter in custom_logger.logger.filters:
        custom_logger.logger.removeFilter(_filter)
    custom_logger.logger.addFilter(filter=AddProcessName(process_name=models.settings.pname))
    return log_handler.baseFilename


class APIConfig(BaseModel):
    """Custom log configuration to redirect all uvicorn logs to individual log files.

    >>> APIConfig

    """

    DEFAULT_LOG_LEVEL = "INFO"

    ACCESS_LOG_FILENAME = datetime.now().strftime(os.path.join('logs', 'fast_api_access_%d-%m-%Y.log'))
    DEFAULT_LOG_FILENAME = datetime.now().strftime(os.path.join('logs', 'fast_api_%d-%m-%Y.log'))

    DEFAULT_LOG_FORMAT = custom_logger.DEFAULT_LOG_FORM
    ACCESS_LOG_FORMAT = '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    ERROR_LOG_FORMAT = '%(levelname)s\t %(message)s'

    LOG_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": DEFAULT_LOG_FORMAT,
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
                "filename": DEFAULT_LOG_FILENAME
            },
            "access": {
                "formatter": "access",
                "class": "logging.FileHandler",
                "filename": ACCESS_LOG_FILENAME
            },
            "error": {
                "formatter": "error",
                "class": "logging.FileHandler",
                "filename": DEFAULT_LOG_FILENAME
            }
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"], "level": DEFAULT_LOG_LEVEL
            },
            "uvicorn.access": {
                "handlers": ["access"], "level": DEFAULT_LOG_LEVEL
            },
            "uvicorn.error": {
                "handlers": ["error"], "level": DEFAULT_LOG_LEVEL, "propagate": True  # Since FastAPI is threaded
            }
        }
    }
