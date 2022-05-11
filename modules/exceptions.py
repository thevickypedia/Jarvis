# noinspection PyUnresolvedReferences
"""This is a space for custom exceptions and errors masking defaults with meaningful names.

>>> Exceptions

"""

import socket

from fastapi import HTTPException


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


class LightsError(socket.error):
    """Custom ``socket.error`` to indicate lights IP isn't reachable.

    >>> LightsError

    """


class TVError(ConnectionResetError):
    """Custom ``ConnectionResetError`` to indicate that the TV is not reachable.

    >>> TVError

    """


class NoInternetError(ConnectionError):
    """Custom ``ConnectionError`` to indicate a connection issue.

    >>> NoInternetError

    """
