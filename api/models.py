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


class GetPasscode(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetData``.

    >>> GetPasscode

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

    LOGGER_NAME: str = "jarvis"
    LOG_FORMAT: str = '%(levelname)s:\t  %(message)s'
    LOG_LEVEL: str = "DEBUG"

    if not environ.get('COMMIT'):  # Disable details in docs
        version = 1
        disable_existing_loggers = False
        formatters = {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": LOG_FORMAT,
                "datefmt": None,
            },
        }
        handlers = {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        }
        loggers = {
            "jarvis": {"handlers": ["default"], "level": LOG_LEVEL},
        }
