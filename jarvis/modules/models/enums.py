# noinspection PyUnresolvedReferences
"""Space for all Enums.

>>> Enums

"""

import sys

if sys.version_info.minor > 10:
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Override for python 3.10 due to lack of StrEnum."""


class SupportedPlatforms(StrEnum):
    """Supported operating systems."""

    windows: str = "Windows"
    macOS: str = "Darwin"
    linux: str = "Linux"


class ReminderOptions(StrEnum):
    """Supported reminder options."""

    phone: str = "phone"
    email: str = "email"
    telegram: str = "telegram"
    ntfy: str = "ntfy"
    all: str = "all"


class StartupOptions(StrEnum):
    """Background threads to startup."""

    all: str = "all"
    car: str = "car"
    none: str = "None"
    thermostat: str = "thermostat"


class TemperatureUnits(StrEnum):
    """Types of temperature units supported by Jarvis.

    >>> TemperatureUnits

    """

    METRIC: str = "metric"
    IMPERIAL: str = "imperial"


class DistanceUnits(StrEnum):
    """Types of distance units supported by Jarvis.

    >>> DistanceUnits

    """

    MILES: str = "miles"
    KILOMETERS: str = "kilometers"


class EventApp(StrEnum):
    """Types of event applications supported by Jarvis.

    >>> EventApp

    """

    CALENDAR = "calendar"
    OUTLOOK = "outlook"


class SSQuality(StrEnum):
    """Quality modes available for speech synthesis.

    >>> SSQuality

    """

    High_Quality = "high"
    Medium_Quality = "medium"
    Low_Quality = "low"
