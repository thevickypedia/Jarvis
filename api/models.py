from datetime import datetime

from pydantic import BaseModel


class GetData(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetData``.

    >>> GetData

    See Also:
        - ``command``: Offline command sent via API which ``Jarvis`` has to perform.
        - ``phrase``: Secret phrase to authenticate the request sent to the API.
    """

    phrase: str = None
    command: str = None


class GetPhrase(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetPhrase``.

    >>> GetPhrase

    See Also:
        - ``phrase``: Secret phrase to authenticate the request sent to the API.
    """

    phrase: str = None


class CronConfig(BaseModel):
    """Custom log configuration for the cron schedule.

    >>> CronConfig

    """

    LOG_LEVEL = "DEBUG"
    FILE_LOG = datetime.now().strftime('logs/cron_%d-%m-%Y.log')
    FILE_LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'

    version = 1
    disable_existing_loggers = True
    formatters = {
        "investment": {
            "format": FILE_LOG_FORMAT,
            "filename": FILE_LOG,
            "datefmt": "%b %d, %Y %H:%M:%S"
        },
    }
    handlers = {
        "investment": {
            "formatter": "investment",
            "class": "logging.FileHandler",
            "filename": FILE_LOG,
        }
    }
    loggers = {
        "investment": {"handlers": ["investment"], "level": LOG_LEVEL, "filename": FILE_LOG}
    }


class LogConfig:
    """Custom log configuration to redirect uvicorn logs to a log file.

    >>> LogConfig

    """

    LOG_LEVEL = "INFO"

    ACCESS_LOG_FILENAME = datetime.now().strftime('logs/api/access_%d-%m-%Y.log')
    DEFAULT_LOG_FILENAME = datetime.now().strftime('logs/api/default_%d-%m-%Y.log')

    DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'
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
                "handlers": ["default"], "level": LOG_LEVEL
            },
            "uvicorn.error": {
                "handlers": ["error"], "level": LOG_LEVEL, "propagate": True  # Since FastAPI is running in a thread
            },
            "uvicorn.access": {
                "handlers": ["access"], "level": LOG_LEVEL
            },
        },
    }
