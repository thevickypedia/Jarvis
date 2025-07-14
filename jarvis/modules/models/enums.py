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

    windows = "Windows"
    macOS = "Darwin"
    linux = "Linux"


class ReminderOptions(StrEnum):
    """Supported reminder options."""

    phone = "phone"
    email = "email"
    telegram = "telegram"
    ntfy = "ntfy"
    all = "all"


class StartupOptions(StrEnum):
    """Background threads to startup."""

    all = "all"
    car = "car"
    gpt = "gpt"
    none = "None"
    thermostat = "thermostat"


class TemperatureUnits(StrEnum):
    """Types of temperature units supported by Jarvis.

    >>> TemperatureUnits

    """

    METRIC = "metric"
    IMPERIAL = "imperial"


class DistanceUnits(StrEnum):
    """Types of distance units supported by Jarvis.

    >>> DistanceUnits

    """

    MILES = "miles"
    KILOMETERS = "kilometers"


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

    High = "high"
    Medium = "medium"
    Low = "low"
