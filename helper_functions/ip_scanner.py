from pynetgear import Netgear


class LocalIPScan:
    def __init__(self, router_pass):
        """
        Gets local host devices connected to the same network range
        hallway() - Given device names for hallway lights, yields bulbs' IPs
        kitchen() - Given device names for kitchen lights, yields bulbs' IPs
        tv() - Given device name for TV, yields TV IP
        """
        self.attached_devices = Netgear(password=router_pass).get_attached_devices()

    def hallway(self):
        """
        Host names of light bulbs stored in a list.
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

    def kitchen(self):
        """
        Host names of light bulbs stored in a list.
        """
        kitchen_1 = 'ZENGGE_35_239190'
        kitchen_2 = 'ZENGGE_35_22E6FD'
        kitchen_all = [kitchen_1, kitchen_2]
        if attached_devices := self.attached_devices:
            for device in attached_devices:
                if device.name in kitchen_all:
                    yield device.ip

    def tv(self):
        """
        Host name of the TV for string match.
        """
        if attached_devices := self.attached_devices:
            for device in attached_devices:
                if device.name == 'LGWEBOSTV':
                    yield device.ip.strip("'")
