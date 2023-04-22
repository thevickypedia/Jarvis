# noinspection PyUnresolvedReferences
"""Module to control smart lights using MagicHomeAPI.

>>> SmartLights

"""

import socket
import struct
import time
from typing import NoReturn

from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.utils import util


def check_number_range(number: int) -> int:
    """Check if the given number is in the allowed range.

    Args:
        number: Takes integer value for RGB value [0-255] check.

    Returns:
        int:
        An accepted number between 0 and 255.
    """
    if number < 0:
        return 0
    elif number > 255:
        return 255
    else:
        return number


def calculate_checksum(bytes_: list) -> int:
    """Calculate the checksum from an array of bytes.

    Args:
        bytes_: Takes a list value as argument.

    Returns:
        int:
        Checksum value for the given list value.
    """
    return sum(bytes_) & 0xFF


class MagicHomeApi:
    """Wrapper for ``MagicHome`` lights.

    >>> MagicHomeApi

    Supports:
        - Bulbs (Firmware v.4 and greater)
        - Legacy Bulbs (Firmware v.3 and lower)
        - RGB Controllers
        - RGB+WW Controllers
        - RGB+WW+CW Controllers
    """

    API_PORT = 5577

    def __init__(self, device_ip: str, device_type: int, operation: str):
        """Initialize device setup via UDP.

        Args:
            device_ip: Takes device IP address as argument.
            device_type: Specific device type.
            operation: Takes the operation that the calling function is trying to perform and logs it.

        See Also:
            Device types:
                - 0: RGB
                - 1: RGB+WW
                - 2: RGB+WW+CW
                - 3: Bulb (v.4+)
                - 4: Bulb (v.3-)
        """
        self.device_ip = device_ip
        self.device_type = device_type
        self.operation = operation
        self.latest_connection = time.time()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3)
        try:
            # Establishing connection with the device.
            self.sock.connect((self.device_ip, self.API_PORT))
        except socket.error as error:
            self.sock.close()
            error_msg = f"\rSocket error on {device_ip}: {error}"
            logger.error("%s while performing '%s'", error_msg, self.operation)
            raise socket.error(error)

    def turn_on(self) -> NoReturn:
        """Turn a device on."""
        self.send_bytes(0x71, 0x23, 0x0F, 0xA3) if self.device_type < 4 else self.send_bytes(0xCC, 0x23, 0x33)

    def turn_off(self) -> NoReturn:
        """Turn a device off."""
        self.send_bytes(0x71, 0x24, 0x0F, 0xA4) if self.device_type < 4 else self.send_bytes(0xCC, 0x24, 0x33)

    def get_status(self) -> bytes:
        """Get the current status of a device.

        Returns:
            bytes:
            A signal to socket.
        """
        if self.device_type == 2:
            self.send_bytes(0x81, 0x8A, 0x8B, 0x96)
            return self.sock.recv(15)
        else:
            self.send_bytes(0x81, 0x8A, 0x8B, 0x96)
            return self.sock.recv(14)

    def update_device(self, r: int = 0, g: int = 0, b: int = 0, warm_white: int = None, cool_white: int = None) -> None:
        """Updates a device based upon what we're sending to it.

        Values are excepted as integers between 0-255.
        Whites can have a value of None.

        Args:
            r: Values for the color Red. [0-255]
            g: Values for the color Green. [0-255]
            b: Values for the color Blue. [0-255]
            warm_white: RGB values for the warm white color.
            cool_white: RGB values for the cool white color.
        """
        if self.device_type <= 1:
            # Update an RGB or an RGB + WW device
            warm_white = check_number_range(warm_white)
            message = [0x31, r, g, b, warm_white, 0x00, 0x0f]
            self.send_bytes(*(message + [calculate_checksum(message)]))

        elif self.device_type == 2:
            # Update an RGB + WW + CW device
            message = [0x31,
                       check_number_range(r),
                       check_number_range(g),
                       check_number_range(b),
                       check_number_range(warm_white),
                       check_number_range(cool_white),
                       0x0f, 0x0f]
            self.send_bytes(*(message + [calculate_checksum(message)]))

        elif self.device_type == 3:
            # Update the white, or color, of a bulb
            if warm_white:
                message = [0x31, 0x00, 0x00, 0x00,
                           check_number_range(warm_white),
                           0x0f, 0x0f]
                self.send_bytes(*(message + [calculate_checksum(message)]))
            else:
                message = [0x31,
                           check_number_range(r),
                           check_number_range(g),
                           check_number_range(b),
                           0x00, 0xf0, 0x0f]
                self.send_bytes(*(message + [calculate_checksum(message)]))

        elif self.device_type == 4:
            # Update the white, or color, of a legacy bulb
            if warm_white:
                message = [0x56, 0x00, 0x00, 0x00,
                           check_number_range(warm_white),
                           0x0f, 0xaa, 0x56, 0x00, 0x00, 0x00,
                           check_number_range(warm_white),
                           0x0f, 0xaa]
                self.send_bytes(*(message + [calculate_checksum(message)]))
            else:
                message = [0x56,
                           check_number_range(r),
                           check_number_range(g),
                           check_number_range(b),
                           0x00, 0xf0, 0xaa]
                self.send_bytes(*(message + [calculate_checksum(message)]))
        else:
            util.write_screen(text="Incompatible device type received.")

    def send_preset_function(self, preset_number: int, speed: int) -> NoReturn:
        """Send a preset command to a device.

        Args:
            preset_number: Takes preset value as argument.
            speed: Rate at which the colors should change. Integer in rage 0-100.

        See Also:
            Presets can range from 0x25 (int 37) to 0x38 (int 56)
        """
        if preset_number < 37:
            preset_number = 37
        if preset_number > 56:
            preset_number = 56
        if speed < 0:
            speed = 0
        if speed > 100:
            speed = 100

        if self.device_type == 4:
            self.send_bytes(0xBB, preset_number, speed, 0x44)
        else:
            message = [0x61, preset_number, speed, 0x0F]
            self.send_bytes(*(message + [calculate_checksum(message)]))

    def send_bytes(self, *bytes_) -> NoReturn:
        """Send commands to the device.

        If the device hasn't been communicated to in 5 minutes, reestablish the connection.

        Args:
            *bytes_: Takes a tuple value as argument.
        """
        check_connection_time = time.time() - self.latest_connection
        try:
            if check_connection_time >= 290:
                util.write_screen(text="Connection timed out, re-establishing.")
                self.sock.connect((self.device_ip, self.API_PORT))
            message_length = len(bytes_)
            self.sock.send(struct.pack("B" * message_length, *bytes_))
        except socket.error as error:
            error_msg = f"Socket error on {self.device_ip}: {error}"
            logger.error("%s while performing '%s'", error_msg, self.operation)
        self.sock.close()
