from ipaddress import IPv4Address
from typing import List, Optional

from pydantic import BaseModel


class LightsModel(BaseModel):
    """Data structure for lights.

    >>> LightsModel

    Examples:
        lights:
          bedroom:
            hostnames:
              - ZENGGE_35_22E43F
            category: first floor
          hallway:
            ipaddresses:
              - 192.168.1.102
              - 192.168.1.103
            category: first floor

    Notes:
        - The identifier for a device can be a mix of both IP address and hostname.
        - Optional category allows controlling multiple devices together based on the location or type.
        - | For example, all devices in the first floor can be categorized as "first floor"
          | and can be controlled together by using the category name.
    """

    hostnames: Optional[List[str]] = []
    ipaddresses: Optional[List[IPv4Address]] = []
    category: str = ""


class TvModel(BaseModel):
    """Data structure for TV.

    >>> TvModel

    Examples:

        .. code-block:: yaml

            living room tv:
              hostname: LGwebOSTV
              mac_address:
                - F8:2A:3B:11:61:9A
                - A8:2A:4B:11:61:9B
            bedroom tv:
              hostname: LGWebOSTV
              mac_address: 78:80:38:FF:4F:B6
              client_key: 123abc456

    Notes:
        Hostname is required to identify the TV and can be used to get the IP address of the TV.
        MAC address is required to turn on the TV using Wake-on-LAN.
        Client key is required for LG TVs for initial authentication. It is not required for Roku TVs.
    """

    hostname: str
    mac_address: List[str] | str
    client_key: str = None
