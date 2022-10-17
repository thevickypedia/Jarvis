import os
from datetime import datetime
from logging import Formatter

from pydantic import BaseModel

from modules.logger.custom_logger import custom_handler, logger


def multiprocessing_logger(filename: str, log_format: Formatter = None) -> str:
    """Remove existing handlers and adds a new handler when a subprocess kicks in.

    Args:
        filename: Filename where the subprocess should log.
        log_format: Custom log format dedicated for each process.
    """
    logger.propagate = False
    for _handler in logger.handlers:
        logger.removeHandler(hdlr=_handler)
    log_handler = custom_handler(filename=filename, log_format=log_format)
    logger.addHandler(hdlr=log_handler)
    return log_handler.baseFilename


class APIConfig(BaseModel):
    """Custom log configuration to redirect uvicorn logs to a log file.

    >>> APIConfig

    """

    DEFAULT_LOG_LEVEL = "INFO"

    ACCESS_LOG_FILENAME = datetime.now().strftime(os.path.join('logs', 'api', 'access_%d-%m-%Y.log'))
    DEFAULT_LOG_FILENAME = datetime.now().strftime(os.path.join('logs', 'api', 'default_%d-%m-%Y.log'))

    DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s"
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
