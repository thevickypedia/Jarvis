from datetime import datetime
from socket import AF_INET, SOCK_STREAM
from socket import error as sock_error
from socket import socket
from struct import pack
from sys import stdout

from helper_functions.logger import logger


class MagicHomeApi:
    """Controller for MagicHome smart devices.

    >>> MagicHomeApi

    """

    def __init__(self, device_ip: str, device_type: int, operation: str):
        """Initialize a device.

        Args:
            device_ip: Takes device IP address as argument.
            device_type: Specific device type. Commonly 1 or 2.
            operation: Takes the operation that the calling function is trying to perform for logging.
        """
        self.device_ip = device_ip
        self.device_type = device_type
        self.operation = operation
        self.API_PORT = 5577
        self.latest_connection = datetime.now()
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.settimeout(3)
        try:
            # Establishing connection with the device.
            self.s.connect((self.device_ip, self.API_PORT))
        except sock_error as error:
            self.s.close()
            error_msg = f"\rSocket error on {device_ip}: {error}"
            stdout.write(error_msg)
            logger.fatal(f'{error_msg} while performing "{self.operation}"')

    def turn_on(self):
        """Turn a device on."""
        self.send_bytes(0x71, 0x23, 0x0F, 0xA3) if self.device_type < 4 else self.send_bytes(0xCC, 0x23, 0x33)

    def turn_off(self):
        """Turn a device off."""
        self.send_bytes(0x71, 0x24, 0x0F, 0xA4) if self.device_type < 4 else self.send_bytes(0xCC, 0x24, 0x33)

    def get_status(self):
        """Get the current status of a device.

        Returns:
            A signal to socket.

        """
        if self.device_type == 2:
            self.send_bytes(0x81, 0x8A, 0x8B, 0x96)
            return self.s.recv(15)
        else:
            self.send_bytes(0x81, 0x8A, 0x8B, 0x96)
            return self.s.recv(14)

    def update_device(self, r: int = 0, g: int = 0, b: int = 0, warm_white: int = None, cool_white: int = None):
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
            warm_white = self.check_number_range(warm_white)
            message = [0x31, r, g, b, warm_white, 0x00, 0x0f]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

        elif self.device_type == 2:
            # Update an RGB + WW + CW device
            message = [0x31,
                       self.check_number_range(r),
                       self.check_number_range(g),
                       self.check_number_range(b),
                       self.check_number_range(warm_white),
                       self.check_number_range(cool_white),
                       0x0f, 0x0f]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

        elif self.device_type == 3:
            # Update the white, or color, of a bulb
            if warm_white:
                message = [0x31, 0x00, 0x00, 0x00,
                           self.check_number_range(warm_white),
                           0x0f, 0x0f]
                self.send_bytes(*(message + [self.calculate_checksum(message)]))
            else:
                message = [0x31,
                           self.check_number_range(r),
                           self.check_number_range(g),
                           self.check_number_range(b),
                           0x00, 0xf0, 0x0f]
                self.send_bytes(*(message + [self.calculate_checksum(message)]))

        elif self.device_type == 4:
            # Update the white, or color, of a legacy bulb
            if warm_white:
                message = [0x56, 0x00, 0x00, 0x00,
                           self.check_number_range(warm_white),
                           0x0f, 0xaa, 0x56, 0x00, 0x00, 0x00,
                           self.check_number_range(warm_white),
                           0x0f, 0xaa]
                self.send_bytes(*(message + [self.calculate_checksum(message)]))
            else:
                message = [0x56,
                           self.check_number_range(r),
                           self.check_number_range(g),
                           self.check_number_range(b),
                           0x00, 0xf0, 0xaa]
                self.send_bytes(*(message + [self.calculate_checksum(message)]))
        else:
            stdout.write("\rIncompatible device type received.")

    @staticmethod
    def check_number_range(number: int):
        """Check if the given number is in the allowed range.

        Args:
            number: Takes integer value for RGB value [0-255] check.

        Returns:
            An accepted number between 0 and 255.

        """
        if number < 0:
            return 0
        elif number > 255:
            return 255
        else:
            return number

    def send_preset_function(self, preset_number: int, speed: int):
        """Send a preset command to a device.

        Args:
            preset_number: Takes preset value as argument.
            speed: Rate at which the colors should change.

        """
        # Presets can range from 0x25 (int 37) to 0x38 (int 56)
        if preset_number < 37:
            preset_number = 37
        if preset_number > 56:
            preset_number = 56
        if speed < 0:
            speed = 0
        if speed > 100:
            speed = 100

        if type == 4:
            self.send_bytes(0xBB, preset_number, speed, 0x44)
        else:
            message = [0x61, preset_number, speed, 0x0F]
            self.send_bytes(*(message + [self.calculate_checksum(message)]))

    @staticmethod
    def calculate_checksum(bytes_: list):
        """Calculate the checksum from an array of bytes.

        Args:
            bytes_: Takes a list value as argument.

        Returns:
            Checksum value for the given list value.

        """
        return sum(bytes_) & 0xFF

    def send_bytes(self, *bytes_):
        """Send commands to the device.

        If the device hasn't been communicated to in 5 minutes, reestablish the connection.

        Args:
            *bytes_: Takes a tuple value as argument.

        """
        check_connection_time = (datetime.now() - self.latest_connection).total_seconds()
        try:
            if check_connection_time >= 290:
                stdout.write("\rConnection timed out, reestablishing.")
                self.s.connect((self.device_ip, self.API_PORT))
            message_length = len(bytes_)
            self.s.send(pack("B" * message_length, *bytes_))
        except sock_error as error:
            error_msg = f"\rSocket error on {self.device_ip}: {error}"
            stdout.write(error_msg)
            logger.fatal(f'{error_msg} while performing "{self.operation}"')
        self.s.close()
