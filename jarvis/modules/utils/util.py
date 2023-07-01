# noinspection PyUnresolvedReferences
"""This is a space for utility functions that do not rely on any external or internal modules but built-ins.

>>> Util

"""

import contextlib
import difflib
import hashlib
import os
import random
import re
import socket
import string
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Hashable, List, NoReturn, Union


def get_timezone() -> str:
    """Get local timezone using datetime module.

    Returns:
        str:
        Returns local timezone abbreviation.
    """
    return datetime.utcnow().astimezone().tzname()


def epoch_to_datetime(seconds: Union[int, float], format_: str = None, zone: timezone = None) -> Union[datetime, str]:
    """Convert epoch time to datetime.

    Args:
        seconds: Epoch timestamp.
        format_: Custom datetime string format.
        zone: Timezone of epoch.

    Returns:
        Union[datetime, str]:
        Returns either a datetime object or a string formatted datetime.
    """
    if zone:
        datetime_obj = datetime.fromtimestamp(seconds, zone)
    else:
        datetime_obj = datetime.fromtimestamp(seconds)
    if format_:
        datetime_obj.strftime(format_)
    return datetime_obj


def miles_to_kms(miles: Union[int, float]) -> float:
    """Takes miles as an argument and returns it in kilometers."""
    return round(miles / 0.621371, 2)


def kms_to_miles(kms: Union[int, float]) -> float:
    """Takes kilometers as an argument and returns it in miles."""
    return round(kms * 0.621371, 2)


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


def get_closest_match(text: str, match_list: list, get_ratio: bool = False) -> Union[Dict[str, float], str]:
    """Get the closest matching word from a list of words.

    Args:
        text: Text to look for in the matching list.
        match_list: List to be compared against.
        get_ratio: Boolean flag to return the closest match along with the ratio, as a dict.

    Returns:
        Union[Dict[str, float], str]:
        Returns the text that matches closest in the list or a dictionary of the closest match and the match ratio.
    """
    closest_match = [{"text": key, "ratio": difflib.SequenceMatcher(a=text, b=key).ratio()} for key in match_list]
    if get_ratio:
        return sorted(closest_match, key=lambda d: d["ratio"], reverse=True)[0]
    return sorted(closest_match, key=lambda d: d["ratio"], reverse=True)[0].get("text")


def hashed(key: uuid.UUID) -> Hashable:
    """Generates sha from UUID.

    Args:
        key: Takes the UUID generated as an argument.

    Returns:
        Hashable:
        Hashed value of the UUID received.
    """
    return hashlib.sha1(key.bytes + bytes(key.hex, "utf-8")).digest().hex()


def token() -> Hashable:
    """Generates a token using hashed uuid4.

    Returns:
        Hashable:
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


def words_to_number(input_: str) -> int:
    """Converts words into integers.

    Args:
        input_: Takes an integer wording as an argument.

    Returns:
        int:
        Integer version of the words.
    """
    input_ = input_.lower()
    number_mapping = {
        'zero': 0,
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
        'ten': 10,
        'eleven': 11,
        'twelve': 12,
        'thirteen': 13,
        'fourteen': 14,
        'fifteen': 15,
        'sixteen': 16,
        'seventeen': 17,
        'eighteen': 18,
        'nineteen': 19,
        'twenty': 20,
        'thirty': 30,
        'forty': 40,
        'fifty': 50,
        'sixty': 60,
        'seventy': 70,
        'eighty': 80,
        'ninety': 90,
    }
    numbers = []
    for word in input_.replace('-', ' ').split():
        if word in number_mapping:
            numbers.append(number_mapping[word])
        elif word == 'hundred':
            numbers[-1] *= 100
        elif word == 'thousand':
            numbers = [x * 1000 for x in numbers]
        elif word == 'million':
            numbers = [x * 1000000 for x in numbers]
    return sum(numbers)


def comma_separator(list_: list) -> str:
    """Separates commas using simple ``.join()`` function and analysis based on length of the list taken as argument.

    Args:
        list_: Takes a list of elements as an argument.

    Returns:
        str:
        Comma separated list of elements.
    """
    return ", and ".join([", ".join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_)


def extract_time(input_: str) -> List[str]:
    """Extracts 12-hour time value from a string.

    Args:
        input_: Int if found, else returns the received float value.

    Returns:
        List[str]:
        Extracted time from the string.
    """
    input_ = input_.lower()
    return re.findall(r'(\d+:\d+\s?(?:a.m.|p.m.:?))', input_) or \
        re.findall(r'(\d+\s?(?:a.m.|p.m.:?))', input_) or \
        re.findall(r'(\d+:\d+\s?(?:am|pm:?))', input_) or \
        re.findall(r'(\d+\s?(?:am|pm:?))', input_)


def delay_calculator(phrase: str) -> Union[int, float]:
    """Calculates the delay in phrase (if any).

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        Union[int, float]:
        Seconds of delay.
    """
    if not (count := extract_nos(input_=phrase)):
        count = 1
    if 'hour' in phrase:
        delay = 3_600
    elif 'minute' in phrase:
        delay = 60
    else:  # Default to # as seconds
        delay = 60
    return count * delay


def extract_nos(input_: str, method: type = float) -> Union[int, float]:
    """Extracts number part from a string.

    Args:
        input_: Takes string as an argument.
        method: Takes a type to return a float or int value.

    Returns:
        Union[int, float]:
        Float values.
    """
    if value := re.findall(r"\d+", input_):
        if method == float:
            try:
                return method(".".join(value))
            except ValueError:
                method = int
        if method == int:
            return method("".join(value))


def format_nos(input_: float) -> int:
    """Removes ``.0`` float values.

    Args:
        input_: Strings or integers with ``.0`` at the end.

    Returns:
        int:
        Int if found, else returns the received float value.
    """
    return int(input_) if isinstance(input_, float) and input_.is_integer() else input_


def extract_str(input_: str) -> str:
    """Extracts strings from the received input.

    Args:
        input_: Takes a string as argument.

    Returns:
        str:
        A string after removing special characters.
    """
    return "".join([i for i in input_ if not i.isdigit() and i not in [",", ".", "?", "-", ";", "!", ":"]]).strip()


def matrix_to_flat_list(input_: List[list]) -> List:
    """Converts a matrix into flat list.

    Args:
        input_: Takes a list of list as an argument.

    Returns:
        list:
        Flat list.
    """
    if filter(lambda x: isinstance(x, list), input_):  # do conversion only if it is a real matrix
        return sum(input_, []) or [item for sublist in input_ for item in sublist]
    return input_


def remove_none(input_: List[Any]) -> List[Any]:
    """Removes None values from a list.

    Args:
        input_: Takes a list as an argument.

    Returns:
        List[Any]:
        Clean list without None values.
    """
    return list(filter(None, input_))


def remove_duplicates(input_: List[Any]) -> List[Any]:
    """Remove duplicate values from a list.

    Args:
        input_: Takes a list as an argument.

    Returns:
        List[Any]:
        Returns a cleaned up list.
    """
    # return list(set(input_))
    return [i for n, i in enumerate(input_) if i not in input_[n + 1:]]


def block_print() -> NoReturn:
    """Suppresses print statement."""
    sys.stdout = open(os.devnull, 'w')


def release_print() -> NoReturn:
    """Removes print statement's suppression."""
    sys.stdout = sys.__stdout__


def get_free_port() -> int:
    """Chooses a PORT number dynamically that is not being used to ensure we don't rely on a single port.

    Instead of binding to a specific port, ``sock.bind(('', 0))`` is used to bind to 0.

    See Also:
        - The port number chosen can be found using ``sock.getsockname()[1]``
        - Passing it on to the slaves so that they can connect back.
        - ``sock`` is the socket that was created, returned by socket.socket.
        - The OS will then pick an available port.

    Notes:
        - Well-Known ports: 0 to 1023
        - Registered ports: 1024 to 49151
        - Dynamically available: 49152 to 65535

    Returns:
        int:
        Randomly chosen port number that is not in use.
    """
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(('', 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]
