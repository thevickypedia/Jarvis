# noinspection PyUnresolvedReferences
"""This is a space for utility functions that do not rely on any external or internal modules but built-ins.

>>> Util

"""

import hashlib
import inspect
import random
import re
import string
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from typing import Hashable

import inflect

engine = inflect.engine()


def get_timezone() -> str:
    """Get local timezone using datetime module.

    Returns:
        str:
        Returns local timezone abbreviation.
    """
    return datetime.utcnow().astimezone().tzname()


def part_of_day() -> str:
    """Checks the current hour to determine the part of day.

    Returns:
        str:
        Morning, Afternoon, Evening or Night based on time of day.
    """
    current_hour = int(datetime.now().strftime("%H"))
    if 5 <= current_hour <= 11:
        return "Morning"
    if 12 <= current_hour <= 15:
        return "Afternoon"
    if 16 <= current_hour <= 19:
        return "Evening"
    return "Night"


def pluralize(count: int) -> str:
    """Helper for ``time_converter`` function."""
    pluralize.counter += 1  # noqa: PyUnresolvedReferences
    frame = inspect.currentframe()
    frame = inspect.getouterframes(frame)[1]
    word = re.findall('\((.*?)\)', frame.code_context[0].strip())[pluralize.counter]  # noqa: PyUnresolvedReferences
    return f"{count} {engine.plural(text=word, count=count)}"


def time_converter(seconds: float) -> str:
    """Modifies seconds to appropriate days/hours/minutes/seconds.

    Args:
        seconds: Takes number of seconds as argument.

    Returns:
        str:
        Seconds converted to days or hours or minutes or seconds.
    """
    day = round(seconds // 86400)
    seconds = round(seconds % (24 * 3600))
    hour = round(seconds // 3600)
    seconds %= 3600
    minute = round(seconds // 60)
    seconds %= 60
    pluralize.counter = -1
    if day and hour and minute and seconds:
        return f"{pluralize(day)}, {pluralize(hour)}, {pluralize(minute)}, and {pluralize(seconds)}"
    elif day and hour and minute:
        return f"{pluralize(day)}, {pluralize(hour)}, and {pluralize(minute)}"
    elif day and hour:
        return f"{pluralize(day)}, and {pluralize(hour)}"
    elif day:
        return pluralize(day)
    elif hour and minute and seconds:
        return f"{pluralize(hour)}, {pluralize(minute)}, and {pluralize(seconds)}"
    elif hour and minute:
        return f"{pluralize(hour)}, and {pluralize(minute)}"
    elif hour:
        return pluralize(hour)
    elif minute and seconds:
        return f"{pluralize(minute)}, and {pluralize(seconds)}"
    elif minute:
        return pluralize(minute)
    else:
        return pluralize(seconds)


def get_closest_match(text: str, match_list: list) -> str:
    """Get the closest matching word from a list of words.

    Args:
        text: Text to look for in the matching list.
        match_list: List to be compared against.

    Returns:
        str:
        Returns the text that matches closest in the list.
    """
    closest_match = [{"key": key, "val": SequenceMatcher(a=text, b=key).ratio()} for key in match_list]
    return sorted(closest_match, key=lambda d: d["val"], reverse=True)[0].get("key")


def hashed(key: uuid.UUID) -> Hashable:
    """Generates sha from UUID.

    Args:
        key: Takes the UUID generated as an argument.

    Returns:
        str:
        Hashed value of the UUID received.
    """
    return hashlib.sha1(key.bytes + bytes(key.hex, "utf-8")).digest().hex()


def token() -> Hashable:
    """Generates a token using hashed uuid4.

    Returns:
        str:
        Returns hashed UUID as a string.
    """
    return hashed(key=uuid.uuid4())


def keygen_str(length: int, punctuation: bool = False) -> str:
    """Generates random key.

    Args:
        length: Length of the keygen.
        punctuation: A boolean flag to include punctuation in the keygen.

    Returns:
        str:
        Random key of specified length.
    """
    if punctuation:
        required_str = string.ascii_letters + string.digits + string.punctuation
    else:
        required_str = string.ascii_letters + string.digits
    return "".join(random.choices(required_str, k=length))


def keygen_uuid(length: int = 32) -> str:
    """Generates random key from hex-d UUID.

    Args:
        length: Length of the required key.

    Returns:
        str:
        Random key of specified length.
    """
    return uuid.uuid4().hex.upper()[:length]
