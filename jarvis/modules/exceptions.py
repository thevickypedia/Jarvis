# noinspection PyUnresolvedReferences
"""This is a space for custom exceptions and errors masking defaults with meaningful names.

>>> Exceptions

"""

import ctypes
from collections.abc import Generator
from contextlib import contextmanager
from typing import ByteString, NoReturn

import requests
from fastapi import HTTPException

EgressErrors = (ConnectionError, TimeoutError, requests.RequestException, requests.Timeout)

ALSA_ERROR_HANDLER = ctypes.CFUNCTYPE(None,
                                      ctypes.c_char_p,
                                      ctypes.c_int,
                                      ctypes.c_char_p,
                                      ctypes.c_int,
                                      ctypes.c_char_p)


def py_error_handler(filename: ByteString, line: int, function: ByteString, err: int, fmt: ByteString) -> NoReturn:
    """Handles errors from pyaudio module especially for Linux based operating systems."""
    pass


c_error_handler = ALSA_ERROR_HANDLER(py_error_handler)


@contextmanager
def no_alsa_err() -> Generator:
    """Wrapper to suppress ALSA error messages when ``PyAudio`` module is called.

    Notes:
        - This happens specifically for Linux based operating systems.
        - There are usually multiple sound APIs to choose from but not all of them might be configured correctly.
        - PyAudio goes through "ALSA", "PulseAudio" and "Jack" looking for audio hardware and that triggers warnings.
        - None of the options below seemed to work in all given conditions, so the approach taken was to hide them.

    Options:
        - Comment off the ALSA devices where the error is triggered.
        - Set energy threshold to the output from ``python -m speech_recognition``
        - Setting dynamic energy threshold to ``True``

    References:
        - https://github.com/Uberi/speech_recognition/issues/100
        - https://github.com/Uberi/speech_recognition/issues/182
        - https://github.com/Uberi/speech_recognition/issues/191
        - https://forums.raspberrypi.com/viewtopic.php?t=136974
    """
    sound = ctypes.cdll.LoadLibrary('libasound.so')
    sound.snd_lib_error_set_handler(c_error_handler)
    yield
    sound.snd_lib_error_set_handler(None)


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


class SegmentationError(EnvironmentError):
    """Custom ``SegmentationError`` raised when the code exits with SIGSEGV.

    >>> SegmentationError

    """
