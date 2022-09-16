# noinspection PyUnresolvedReferences
"""Module to change volume in WindowsOS, using windows binaries.

>>> WindowsVolume

"""

import ctypes
from typing import NoReturn

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


class KeyBoardInput(ctypes.Structure):
    """Inherits ``Structure`` from ``ctypes`` for operations using keyboard.

    >>> KeyBoardInput

    """

    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class HardwareInput(ctypes.Structure):
    """Inherits ``Structure`` from ``ctypes`` for operations using external hardware.

    >>> HardwareInput

    """

    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort)
    ]


class MouseInput(ctypes.Structure):
    """Inherits ``Structure`` from ``ctypes`` for operations using a mouse.

    >>> MouseInput

    """

    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class InputI(ctypes.Union):
    """Inherits ``Union`` from ``ctypes`` for input operations.

    >>> MouseInput

    """

    _fields_ = [
        ("ki", KeyBoardInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]


class Input(ctypes.Structure):
    """Inherits ``Structure`` from ``ctypes`` to set type fields.

    >>> MouseInput

    """

    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", InputI)
    ]


def key_down(key_code: int) -> NoReturn:
    """Function for key down.

    Args:
        key_code: Key code.
    """
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.ki = KeyBoardInput(key_code, 0x48, 0, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def key_up(key_code: int) -> NoReturn:
    """Function for key up.

    Args:
        key_code: Key code.
    """
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.ki = KeyBoardInput(key_code, 0x48, 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def key(key_code: int) -> NoReturn:
    """Operator for the key function with time interval.

    Args:
        key_code: Key code.
    """
    key_down(key_code)
    key_up(key_code)


def volume_up() -> NoReturn:
    """Controller for increase volume."""
    key(VK_VOLUME_UP)


def volume_down() -> NoReturn:
    """Controller for decrease volume."""
    key(VK_VOLUME_DOWN)


def mute() -> NoReturn:
    """Controller for mute."""
    key(VK_VOLUME_MUTE)


def set_volume(level: int = 50) -> NoReturn:
    """Set volume to a custom level.

    Args:
        level: Level to which the volume has to be set.
    """
    for _ in range(0, 50):
        volume_down()
    for _ in range(int(level / 2)):
        volume_up()
