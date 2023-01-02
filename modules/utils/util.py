# noinspection PyUnresolvedReferences
"""This is a space for utility functions that do not rely on any external or internal modules but built-ins.

>>> Util

"""

import hashlib
import random
import string
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from typing import Hashable

import inflect

engine = inflect.engine()


class Dict2Class:
    """Turns a dictionary into an object."""

    def __init__(self, dictionary: dict):
        """Creates an object and inserts the key value pairs as members of the class.

        Args:
            dictionary: Takes the dictionary to be converted as an argument.
        """
        for key in dictionary:
            setattr(self, key, dictionary[key])


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


def pluralize(count: int, word: str) -> str:
    """Helper for ``time_converter`` function.

    Args:
        count: Number based on which plural form should be determined.
        word: Word for which the plural form should be converted.

    Returns:
        str:
        String formatted time in singular or plural.
    """
    return f"{count} {engine.plural(text=word, count=count)}"


def time_converter(second: float) -> str:
    """Modifies seconds to appropriate days/hours/minutes/seconds.

    Args:
        second: Takes number of seconds as argument.

    Returns:
        str:
        Seconds converted to days or hours or minutes or seconds.
    """
    day = round(second // 86400)
    second = round(second % (24 * 3600))
    hour = round(second // 3600)
    second %= 3600
    minute = round(second // 60)
    second %= 60
    pluralize.counter = -1
    if day and hour and minute and second:
        return f"{pluralize(day, 'day')}, {pluralize(hour, 'hour')}, " \
               f"{pluralize(minute, 'minute')}, and {pluralize(second, 'second')}"
    elif day and hour and minute:
        return f"{pluralize(day, 'day')}, {pluralize(hour, 'hour')}, " \
               f"and {pluralize(minute, 'minute')}"
    elif day and hour:
        return f"{pluralize(day, 'day')}, and {pluralize(hour, 'hour')}"
    elif day:
        return pluralize(day, 'day')
    elif hour and minute and second:
        return f"{pluralize(hour, 'hour')}, {pluralize(minute, 'minute')}, and {pluralize(second, 'second')}"
    elif hour and minute:
        return f"{pluralize(hour, 'hour')}, and {pluralize(minute, 'minute')}"
    elif hour:
        return pluralize(hour, 'hour')
    elif minute and second:
        return f"{pluralize(minute, 'minute')}, and {pluralize(second, 'second')}"
    elif minute:
        return pluralize(minute, 'minute')
    else:
        return pluralize(second, 'second')


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
