from datetime import datetime
from os import environ

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


class LogConfig(BaseModel):
    """Custom log configuration.

    >>> LogConfig

    See Also:
        - ``LOGGER_NAME`` should match the name passed to ``getLogger`` when this class is used for ``dictConfig``
        - ``LOG_FORMAT`` is set to match the format of ``uvicorn.access`` logs.
    """

    if not environ.get('COMMIT'):  # Disable code in docs
        LOGGER_NAME: str = "jarvis"
        LOG_FORMAT: str = '%(levelname)s:\t  %(message)s'
        LOG_LEVEL: str = "DEBUG"
        FILE_LOG: str = datetime.now().strftime('logs/%Y-%m-%d.log')
        FILE_LOG_FORMAT: str = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'

        version = 1
        disable_existing_loggers = False
        formatters = {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": LOG_FORMAT,
                "datefmt": None,
            },
            "investment": {
                "format": FILE_LOG_FORMAT,
                "filename": FILE_LOG,
                "datefmt": "%b %d, %Y %H:%M:%S"
            },
        }
        handlers = {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "investment": {
                "formatter": "investment",
                "class": "logging.FileHandler",
                "filename": FILE_LOG,
            }
        }
        loggers = {
            "jarvis": {"handlers": ["default"], "level": LOG_LEVEL},
            "investment": {"handlers": ["investment"], "level": LOG_LEVEL, "filename": FILE_LOG}
        }
