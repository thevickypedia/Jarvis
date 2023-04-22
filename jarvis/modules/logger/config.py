# noinspection PyUnresolvedReferences
"""Module for custom logger configurations.

>>> Config

"""

import os
from datetime import datetime
from logging import Filter, Formatter, LogRecord
from multiprocessing import current_process

from pydantic import BaseModel

from jarvis.modules.logger.custom_logger import (DEFAULT_LOG_FORM,
                                                 custom_handler, logger)


class AddProcessName(Filter):
    """Wrapper that overrides ``logging.Filter`` to add ``processName`` to the existing log format.

    >>> AddProcessName

    """

    def __init__(self, process_name: str):
        """Instantiates super class.

        Args:
            process_name: Takes name of the process to be added as argument.
        """
        self.process_name = process_name
        super().__init__()

    def filter(self, record: LogRecord) -> bool:
        """Overrides built-in."""
        record.processName = self.process_name
        return True


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
    logger.propagate = False
    # Remove existing handlers
    for _handler in logger.handlers:
        logger.removeHandler(hdlr=_handler)
    log_handler = custom_handler(filename=filename, log_format=log_format)
    logger.addHandler(hdlr=log_handler)
    # Remove existing filters from the new log handler
    for _filter in logger.filters:
        logger.removeFilter(_filter)
    logger.addFilter(filter=AddProcessName(process_name=current_process().name))
    return log_handler.baseFilename


class APIConfig(BaseModel):
    """Custom log configuration to redirect all uvicorn logs to individual log files.

    >>> APIConfig

    """

    DEFAULT_LOG_LEVEL = "INFO"

    ACCESS_LOG_FILENAME = datetime.now().strftime(os.path.join('logs', 'api', 'access_%d-%m-%Y.log'))
    DEFAULT_LOG_FILENAME = datetime.now().strftime(os.path.join('logs', 'api', 'default_%d-%m-%Y.log'))

    DEFAULT_LOG_FORMAT = DEFAULT_LOG_FORM
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
