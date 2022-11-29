# noinspection PyUnresolvedReferences
"""This is a space for custom exceptions and errors masking defaults with meaningful names.

>>> Exceptions

"""

import requests
from fastapi import HTTPException

EgressErrors = (ConnectionError, TimeoutError, requests.exceptions.RequestException, requests.exceptions.Timeout)


class UnsupportedOS(OSError):
    """Custom ``OSError`` raised when initiated in an unsupported operating system.

    >>> UnsupportedOS

    """


class CameraError(BlockingIOError):
    """Custom ``BlockingIOError`` to handle missing camera device.

    >>> CameraError

    """


class BotInUse(OverflowError):
    """Custom ``OverflowError`` to indicate bot token is being used else where.

    >>> BotInUse

    """


class StopSignal(KeyboardInterrupt):
    """Custom ``KeyboardInterrupt`` to handle manual interruption.

    >>> StopSignal

    """


class APIResponse(HTTPException):
    """Custom ``HTTPException`` from ``FastAPI`` to wrap an API response.

    >>> APIResponse

    """


class InvalidEnvVars(ValueError):
    """Custom ``ValueError`` to indicate invalid env vars.

    >>> InvalidEnvVars

    """


class MissingEnvVars(ValueError):
    """Custom ``ValueError`` to indicate missing env vars.

    >>> MissingEnvVars

    """


class InvalidArgument(ValueError):
    """Custom ``ValueError`` to indicate invalid args.

    >>> InvalidArgument

    """


class TVError(ConnectionResetError):
    """Custom ``ConnectionResetError`` to indicate that the TV is not reachable.

    >>> TVError

    """


class NoCoversFound(NotImplementedError):
    """Custom ``NotImplementedError`` to indicate that no garage doors were found.

    >>> NoCoversFound

    """


class CoverNotOnline(SystemError):
    """Custom ``SystemError`` to indicate that the garage door connector is offline.

    >>> CoverNotOnline

    """

    def __init__(self, device: str, msg: str):
        """Instantiates device and msg attributes.

        Args:
            device: Name of the device.
            msg: Error message.
        """
        self.device = device
        self.msg = msg

    def __str__(self) -> str:
        """Returns a printable representational of the error message."""
        return repr(self.msg)
