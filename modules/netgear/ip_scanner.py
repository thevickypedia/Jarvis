from pynetgear import Netgear


class LocalIPScan:
    """Connector to scan devices in the same IP range using ``Netgear API``.

    >>> LocalIPScan

    """

    def __init__(self, router_pass: str):
        """Gets local host devices connected to the same network range.

        Args:
            router_pass: Password to authenticate the API client.
        """
        self.attached_devices = Netgear(password=router_pass).get_attached_devices()

    def hallway(self) -> str:
        """Host names of hallway light bulbs stored in a list.

        Yields:
            str:
            IP address of the device.
        """
        hallway_1 = 'ZENGGE_35_011853'
        hallway_2 = 'ZENGGE_35_0171D9'
        hallway_3 = 'ZENGGE_35_065576'
        hallway_4 = 'ZENGGE_35_DDB9B1'
        hallway_5 = 'ZENGGE_35_23343E'
        hallway_all = [hallway_1, hallway_2, hallway_3, hallway_4, hallway_5]
        if attached_devices := self.attached_devices:
            for device in attached_devices:
                if device.name in hallway_all:
                    yield device.ip

    def kitchen(self) -> str:
        """Host names of kitchen light bulbs stored in a list.

        Yields:
            str:
            IP address of the device.
        """
        kitchen_1 = 'ZENGGE_35_239190'
        kitchen_2 = 'ZENGGE_35_22E6FD'
        kitchen_all = [kitchen_1, kitchen_2]
        if attached_devices := self.attached_devices:
            for device in attached_devices:
                if device.name in kitchen_all:
                    yield device.ip

    def bedroom(self) -> str:
        """Host names of bedroom light bulbs stored in a list.

        Yields:
            str:
            IP address of the device.
        """
        bedroom_1 = 'ZENGGE_35_22E43F'
        if attached_devices := self.attached_devices:
            for device in attached_devices:
                if device.name == bedroom_1:
                    yield device.ip

    def tv(self) -> tuple:
        """Host name of TV for string equality comparison.

        Returns:
            tuple:
            A tuple object of IP address and mac address of the TV.
        """
        if attached_devices := self.attached_devices:
            for device in attached_devices:
                if device.name == 'LGWEBOSTV':
                    return device.ip, device.mac
        return None, None


if __name__ == '__main__':
    import os
    from pprint import pprint

    from dotenv import load_dotenv

    env_file_path = '../../.env'
    load_dotenv(dotenv_path=env_file_path)

    pprint(LocalIPScan(router_pass=os.environ.get('ROUTER_PASS')).attached_devices)
