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


def time_converter(seconds: float) -> str:
    """Modifies seconds to appropriate days/hours/minutes/seconds.

    Args:
        seconds: Takes number of seconds as argument.

    Returns:
        str:
        Seconds converted to days or hours or minutes or seconds.
    """
    days = round(seconds // 86400)
    seconds = round(seconds % (24 * 3600))
    hours = round(seconds // 3600)
    seconds %= 3600
    minutes = round(seconds // 60)
    seconds %= 60
    if days and hours and minutes and seconds:
        return f"{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds"
    elif days and hours and minutes:
        return f"{days} days, {hours} hours, and {minutes} minutes"
    elif days and hours:
        return f"{days} days, and {hours} hours"
    elif days:
        return f"{days} days"
    elif hours and minutes and seconds:
        return f"{hours} hours, {minutes} minutes, and {seconds} seconds"
    elif hours and minutes:
        return f"{hours} hours, and {minutes} minutes"
    elif hours:
        return f"{hours} hours"
    elif minutes and seconds:
        return f"{minutes} minutes, and {seconds} seconds"
    elif minutes:
        return f"{minutes} minutes"
    else:
        return f"{seconds} seconds"


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
