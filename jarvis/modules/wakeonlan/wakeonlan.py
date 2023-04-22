# noinspection PyUnresolvedReferences
"""Module for powering on supported devices.

>>> WakeOnLan

"""

import socket
from typing import NoReturn

from jarvis.modules.exceptions import InvalidArgument


class WakeOnLan:
    """Initiates WakeOnLan object to create and send bytes to turn on a device.

    >>> WakeOnLan

    """

    BROADCAST_IP = "255.255.255.255"
    DEFAULT_PORT = 9

    @classmethod
    def create_packet(cls, macaddress: str) -> bytes:
        """Create a magic packet.

        A magic packet is a packet that can be used with the for wake on lan
        protocol to wake up a computer. The packet is constructed from the
        mac address given as a parameter.

        Args:
            macaddress: the mac address that should be parsed into a magic packet.

        Raises:
            InvalidArgument:
            If the argument ``macaddress`` is invalid.
        """
        if len(macaddress) == 17:
            macaddress = macaddress.replace(macaddress[2], "")
        elif len(macaddress) != 12:
            raise InvalidArgument(f"invalid mac address: {macaddress}")
        return bytes.fromhex("F" * 12 + macaddress * 16)

    def send_packet(self, *mac_addresses: str, ip_address: str = BROADCAST_IP, port: int = DEFAULT_PORT,
                    interface: str = None) -> NoReturn:
        """Wake up devices using mac addresses.

        Notes:
            Wake on lan must be enabled on the host device.

        Args:
            mac_addresses: One or more mac addresses of machines to wake.
            ip_address: IP address of the host to send the magic packet to.
            port: Port of the host to send the magic packet to.
            interface: IP address of the network adapter to route the packets through.
        """
        packets = [self.create_packet(mac) for mac in mac_addresses]

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            if interface:
                sock.bind((interface, 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.connect((ip_address, port))
            for packet in packets:
                sock.send(packet)
