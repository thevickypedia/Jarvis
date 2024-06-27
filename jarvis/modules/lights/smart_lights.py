# noinspection PyUnresolvedReferences
"""Module to control smart lights using MagicHomeAPI.

>>> SmartLights

References:
    - https://github.com/adamkempenich/magichome-python/blob/master/magichome.py
    - https://github.com/SynTexDZN/homebridge-syntex-magichome/blob/master/src/flux_led.py
"""

import socket
import struct
import time

import webcolors

from jarvis.modules.lights import preset_values
from jarvis.modules.logger import logger
from jarvis.modules.utils import support


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
    """Wrapper for ``MagicHome`` lights to initialize device setup via UDP.

    >>> MagicHomeApi

    Args:
        device_ip: Takes device IP address as argument.
        device_type: Specific device type.

    See Also:
        Device types:
            - 0: RGB
            - 1: RGB+WW
            - 2: RGB+WW+CW
            - 3: Bulb (v.4+)
            - 4: Bulb (v.3-)

    **Supports**:
        - Bulbs (Firmware v.4 and greater)
        - Legacy Bulbs (Firmware v.3 and lower)
        - RGB Controllers
        - RGB+WW Controllers
        - RGB+WW+CW Controllers
    """

    API_PORT = 5577

    def __init__(self, device_ip: str, device_type: int):
        """Initialize device setup via UDP."""
        self.device_ip = str(device_ip)
        self.device_type = device_type
        self.latest_connection = time.time()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3)
        try:
            # Establishing connection with the device.
            self.sock.connect((self.device_ip, self.API_PORT))
        except socket.error as error:
            self.sock.close()
            raise socket.error(error)

    def turn_on(self) -> None:
        """Turn a device on."""
        self.send_bytes(
            0x71, 0x23, 0x0F, 0xA3
        ) if self.device_type < 4 else self.send_bytes(0xCC, 0x23, 0x33)

    def turn_off(self) -> None:
        """Turn a device off."""
        self.send_bytes(
            0x71, 0x24, 0x0F, 0xA4
        ) if self.device_type < 4 else self.send_bytes(0xCC, 0x24, 0x33)

    @staticmethod
    def byte_to_percent(byte: int) -> int:
        """Converts byte integer into a percentile."""
        if byte > 255:
            byte = 255
        if byte < 0:
            byte = 0
        return int((byte * 100) / 255)

    def get_status(self) -> str | None:
        """Get the current status of a device.

        Returns:
            str:
            Status of the light as string.
        """
        msg = bytearray([0x81, 0x8A, 0x8B])
        csum = sum(msg) & 0xFF
        msg.append(csum)
        try:
            self.sock.send(msg)
        except OSError as error:
            logger.error(error)
            return
        remaining = 14
        rx = bytearray()
        while remaining > 0:
            chunk = self.sock.recv(1024)
            remaining -= len(chunk)
            rx.extend(chunk)
        if rx[2] == 0x23:
            power_str = "ON"
        elif rx[2] == 0x24:
            power_str = "OFF"
        else:
            power_str = "Unknown power state"
        pattern = rx[3]
        ww_level = rx[9]
        if pattern in [0x61, 0x62]:
            mode = "color"
        elif pattern == 0x60:
            mode = "custom"
        elif pattern in preset_values.PRESET_VALUES.values():
            mode = "preset"
        else:
            mode = "unknown"
        delay = rx[5]
        delay = delay - 1
        if delay > 0x1F - 1:
            delay = 0x1F - 1
        if delay < 0:
            delay = 0
        inv_speed = int((delay * 100) / (0x1F - 1))
        speed = 100 - inv_speed
        if mode == "color":
            red = rx[6]
            green = rx[7]
            blue = rx[8]
            color_name = webcolors.rgb_to_name((red, green, blue))
            mode_str = f"Color: {color_name}"
        elif mode == "ww":
            mode_str = f"Warm White: {self.byte_to_percent(ww_level)}%"
        elif mode == "cw":
            mode_str = f"Cold White: {self.byte_to_percent(ww_level)}%"
        elif mode == "preset":
            for key, value in preset_values.PRESET_VALUES.items():
                if pattern == value:
                    pat = key
                    break
            else:
                pat = "unknown"
            mode_str = f"Pattern: {pat} (Speed {speed}%)"
        elif mode == "custom":
            mode_str = f"Custom pattern (Speed {speed}%)"
        else:
            mode_str = "Unknown mode 0x{:x}".format(pattern)
        if pattern == 0x62:
            mode_str += " (tmp)"
        return f"{power_str} [{mode_str}]"

    def update_device(
        self,
        r: int = 0,
        g: int = 0,
        b: int = 0,
        warm_white: int = None,
        cool_white: int = None,
    ) -> None:
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
            message = [0x31, r, g, b, warm_white, 0x00, 0x0F]
            self.send_bytes(*(message + [calculate_checksum(message)]))

        elif self.device_type == 2:
            # Update an RGB + WW + CW device
            message = [
                0x31,
                check_number_range(r),
                check_number_range(g),
                check_number_range(b),
                check_number_range(warm_white),
                check_number_range(cool_white),
                0x0F,
                0x0F,
            ]
            self.send_bytes(*(message + [calculate_checksum(message)]))

        elif self.device_type == 3:
            # Update the white, or color, of a bulb
            if warm_white:
                message = [
                    0x31,
                    0x00,
                    0x00,
                    0x00,
                    check_number_range(warm_white),
                    0x0F,
                    0x0F,
                ]
                self.send_bytes(*(message + [calculate_checksum(message)]))
            else:
                message = [
                    0x31,
                    check_number_range(r),
                    check_number_range(g),
                    check_number_range(b),
                    0x00,
                    0xF0,
                    0x0F,
                ]
                self.send_bytes(*(message + [calculate_checksum(message)]))

        elif self.device_type == 4:
            # Update the white, or color, of a legacy bulb
            if warm_white:
                message = [
                    0x56,
                    0x00,
                    0x00,
                    0x00,
                    check_number_range(warm_white),
                    0x0F,
                    0xAA,
                    0x56,
                    0x00,
                    0x00,
                    0x00,
                    check_number_range(warm_white),
                    0x0F,
                    0xAA,
                ]
                self.send_bytes(*(message + [calculate_checksum(message)]))
            else:
                message = [
                    0x56,
                    check_number_range(r),
                    check_number_range(g),
                    check_number_range(b),
                    0x00,
                    0xF0,
                    0xAA,
                ]
                self.send_bytes(*(message + [calculate_checksum(message)]))
        else:
            support.write_screen(text="Incompatible device type received.")

    def send_preset_function(self, preset_number: int, speed: int) -> None:
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

    def send_bytes(self, *bytes_) -> None:
        """Send commands to the device.

        If the device hasn't been communicated to in 5 minutes, reestablish the connection.

        Args:
            *bytes_: Takes a tuple value as argument.
        """
        check_connection_time = time.time() - self.latest_connection
        try:
            if check_connection_time >= 290:
                support.write_screen(text="Connection timed out, re-establishing.")
                self.sock.connect((self.device_ip, self.API_PORT))
            message_length = len(bytes_)
            self.sock.send(struct.pack("B" * message_length, *bytes_))
        except socket.error as error:
            logger.error("[%s]: %s", self.device_ip, error)
        self.sock.close()
