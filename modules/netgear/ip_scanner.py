import os

import yaml
from pynetgear import Netgear

from executors.logger import logger
from modules.exceptions import MissingEnvVars
from modules.models import models

env = models.env
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

    def __init__(self):
        """Gets local host devices connected to the same network range."""
        if not env.router_pass:
            raise MissingEnvVars(
                "Router password is required to scan the local host."
            )
        self.attached_devices = Netgear(password=env.router_pass).get_attached_devices()

    def smart_devices(self) -> dict:
        """Gets the IP addresses of the smart devices listed in hostnames.yaml.

        Returns:
            dict:
            A dictionary of device category as key and list of IPs as value.
        """
        smart_devices_dict = {}
        for device in self.attached_devices:
            for category, hostnames in _get_hostnames().items():
                if category.upper() == "TV":
                    smart_devices_dict["tv_ip"] = device.ip
                    smart_devices_dict["tv_mac"] = device.mac
                elif device.name in hostnames:
                    if category in list(smart_devices_dict.keys()):
                        smart_devices_dict[category].append(device.ip)
                    else:
                        smart_devices_dict[category] = [device.ip]
        return smart_devices_dict
