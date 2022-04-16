# noinspection PyUnresolvedReferences
"""This is a space for custom exceptions and errors masking defaults with meaningful names.

>>> Exceptions

"""

import socket

from fastapi import HTTPException


class UnsupportedOS(OSError):
    """Custom ``OSError`` raised when initiated in an unsupported operating system."""


class CameraError(BlockingIOError):
    """Custom ``BlockingIOError`` to handle missing camera device."""


class BotInUse(OverflowError):
    """Custom ``OverflowError`` to indicate bot token is being used else where."""


class StopSignal(KeyboardInterrupt):
    """Custom ``KeyboardInterrupt`` to handle manual interruption."""


class Response(HTTPException):
    """Custom ``HTTPException`` from ``FastAPI`` to wrap an API response."""


class InvalidEnvVars(ValueError):
    """Custom ``ValueError`` to indicate invalid env vars."""


class MissingEnvVars(ValueError):
    """Custom ``ValueError`` to indicate missing env vars."""


class InvalidArgument(ValueError):
    """Custom ``ValueError`` to indicate invalid args."""


class LightsError(socket.error):
    """Custom ``socket.error`` to indicate lights IP isn't reachable."""
