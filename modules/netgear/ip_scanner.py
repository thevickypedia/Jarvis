import os

import yaml
from pynetgear import Netgear

from executors.logger import logger
from modules.exceptions import MissingEnvVars
from modules.models import models

fileio = models.fileio


def _get_hostnames() -> dict:
    """Loads the hostnames source file.

    Returns:
        dict:
        Category and hostnames.
    """
    if os.path.isfile(fileio.hostnames):
        try:
            with open(fileio.hostnames) as file:
                return yaml.load(stream=file, Loader=yaml.FullLoader)
        except yaml.YAMLError as error:
            logger.error(error)
    else:
        logger.warning(f"{fileio.hostnames} was not found.")
    return {}


class LocalIPScan:
    """Connector to scan devices in the same IP range using ``Netgear API``.

    >>> LocalIPScan

    """

    def __init__(self, router_pass: str):
        """Gets local host devices connected to the same network range.

        Args:
            router_pass: Password to authenticate the API client.
        """
        if not router_pass:
            raise MissingEnvVars(
                "Router password is required to scan for devices."
            )
        self.attached_devices = Netgear(password=router_pass).get_attached_devices()
        self._hostnames = _get_hostnames()

    def hallway(self) -> str:
        """Host names of hallway light bulbs stored in a list.

        Yields:
            str:
            IP address of the device.
        """
        if self.attached_devices and self._hostnames.get('hallway'):
            for device in self.attached_devices:
                if device.name in self._hostnames.get('hallway'):
                    yield device.ip

    def kitchen(self) -> str:
        """Host names of kitchen light bulbs stored in a list.

        Yields:
            str:
            IP address of the device.
        """
        if self.attached_devices and self._hostnames.get('kitchen'):
            for device in self.attached_devices:
                if device.name in self._hostnames.get('kitchen'):
                    yield device.ip

    def bedroom(self) -> str:
        """Host names of bedroom light bulbs stored in a list.

        Yields:
            str:
            IP address of the device.
        """
        if self.attached_devices and self._hostnames.get('bedroom'):
            for device in self.attached_devices:
                if device.name in self._hostnames.get('bedroom'):
                    yield device.ip

    def tv(self) -> tuple:
        """Host name of TV for string equality comparison.

        Returns:
            tuple:
            A tuple object of IP address and mac address of the TV.
        """
        if self.attached_devices and self._hostnames.get('tv'):
            for device in self.attached_devices:
                if device.name == self._hostnames.get('tv'):
                    return device.ip, device.mac
        return None, None


if __name__ == '__main__':
    from pprint import pprint

    from dotenv import load_dotenv

    env_path = '../../.env'
    load_dotenv(dotenv_path=env_path)
    fileio.hostnames = f'../../{fileio.hostnames}'

    pprint(LocalIPScan(router_pass=os.environ.get('ROUTER_PASS')).attached_devices)
