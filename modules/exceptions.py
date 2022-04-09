# noinspection PyUnresolvedReferences
"""This is a space for custom exceptions and errors masking defaults with meaningful names.

>>> Exceptions

"""

from fastapi import HTTPException


class UnsupportedOS(OSError):
    """Custom ``OSError`` raised when initiated in an unsupported operating system."""
    pass


class MissingEnvVars(ValueError):
    """Custom ``ValueError`` to indicate missing env vars."""
    pass


class CameraError(BlockingIOError):
    """Custom ``BlockingIOError`` to handle missing camera device."""
    pass


class BotInUse(OverflowError):
    """Custom ``OverflowError`` to indicate bot token is being used else where."""
    pass


class StopSignal(KeyboardInterrupt):
    """Custom ``KeyboardInterrupt`` to handle manual interruption."""
    pass


class Response(HTTPException):
    """Custom ``HTTPException`` from ``FastAPI`` to wrap an API response."""
    pass


class InvalidEnvVars(ValueError):
    """Custom ``ValueError`` to indicate invalid env vars."""
    pass


class InvalidArgument(ValueError):
    """Custom ``ValueError`` to indicate invalid args."""
    pass
