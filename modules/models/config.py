import os.path
from datetime import datetime

from pydantic import BaseModel

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'


class CronConfig(BaseModel):
    """Custom log configuration for the cron schedule.

    >>> CronConfig

    """

    LOG_FILE = datetime.now().strftime(f'logs{os.path.sep}cron_%d-%m-%Y.log')

    version = 1
    disable_existing_loggers = True
    formatters = {
        "investment": {
            "format": DEFAULT_LOG_FORMAT,
            "filename": LOG_FILE,
            "datefmt": "%b %d, %Y %H:%M:%S"
        },
    }
    handlers = {
        "investment": {
            "formatter": "investment",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
        }
    }
    loggers = {
        "investment": {"handlers": ["investment"], "level": DEFAULT_LOG_LEVEL, "filename": LOG_FILE}
    }


class APIConfig(BaseModel):
    """Custom log configuration to redirect uvicorn logs to a log file.

    >>> APIConfig

    """

    ACCESS_LOG_FILENAME = datetime.now().strftime(f'logs{os.path.sep}api{os.path.sep}access_%d-%m-%Y.log')
    DEFAULT_LOG_FILENAME = datetime.now().strftime(f'logs{os.path.sep}api{os.path.sep}default_%d-%m-%Y.log')

    ACCESS_LOG_FORMAT = '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    ERROR_LOG_FORMAT = '%(levelname)s\t %(message)s'

    LOGGING_CONFIG = {
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


class BotConfig(BaseModel):
    """Custom log configuration for the telegram bot.

    >>> BotConfig

    """

    LOG_FILE = datetime.now().strftime(f'logs{os.path.sep}telegram_%d-%m-%Y.log')

    version = 1
    disable_existing_loggers = True
    formatters = {
        "default": {
            "format": DEFAULT_LOG_FORMAT,
            "filename": LOG_FILE,
            "datefmt": "%b %d, %Y %H:%M:%S"
        }
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
        }
    }
    loggers = {
        "telegram": {"handlers": ["default"], "level": DEFAULT_LOG_LEVEL, "filename": LOG_FILE}
    }
