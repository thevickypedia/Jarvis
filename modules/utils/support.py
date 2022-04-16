# noinspection PyUnresolvedReferences
"""This is a space for support functions used across different modules.

>>> Support

"""

import hashlib
import math
import os
import random
import re
import string
import sys
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, NoReturn, Union

import inflect
import psutil
import yaml
from holidays import country_holidays

from executors import display_functions
from executors.logger import logger
from modules.audio import speaker, volume
from modules.models import models
from modules.netgear.ip_scanner import LocalIPScan

env = models.env
fileio = models.fileio


def celebrate() -> str:
    """Function to look if the current date is a holiday or a birthday.

    Returns:
        str:
        A string of the event observed today.
    """
    day = datetime.today().date()
    us_holidays = country_holidays("US").get(day)  # checks if the current date is a US holiday
    in_holidays = country_holidays("IND", prov="TN", state="TN").get(day)  # checks if Indian (esp TN) holiday
    if in_holidays:
        return in_holidays
    elif us_holidays and "Observed" not in us_holidays:
        return us_holidays
    elif env.birthday == datetime.now().strftime("%d-%B"):
        return "Birthday"


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


def get_capitalized(phrase: str, dot: bool = True) -> Union[str, None]:
    """Looks for words starting with an upper-case letter.

    Args:
        phrase: Takes input string as an argument.
        dot: Takes a boolean flag whether to include words separated by (.) dot.

    Returns:
        str:
        Returns the upper case words if skimmed.
    """
    place = ""
    for word in phrase.split():
        if word[0].isupper():
            place += word + " "
        elif "." in word and dot:
            place += word + " "
    return place.strip() if place.strip() else None


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


def unrecognized_dumper(train_data: dict) -> NoReturn:
    """If none of the conditions are met, converted text is written to a yaml file for training purpose.

    Args:
        train_data: Takes the dictionary that has to be written as an argument.
    """
    dt_string = datetime.now().strftime("%B %d, %Y %H:%M:%S.%f")[:-3]
    if os.path.isfile(fileio.training):
        with open(fileio.training) as reader:
            data = yaml.safe_load(stream=reader) or {}
        for key, value in train_data.items():
            if data.get(key):
                data[key].update({dt_string: value})
            else:
                data.update({key: {dt_string: value}})
    else:
        data = {key1: {dt_string: value1} for key1, value1 in train_data.items()}

    with open(fileio.training, 'w') as writer:
        yaml.dump(data=data, stream=writer)


def size_converter(byte_size: int) -> str:
    """Gets the current memory consumed and converts it to human friendly format.

    Args:
        byte_size: Receives byte size as argument.

    Returns:
        str:
        Converted understandable size.
    """
    if not byte_size:
        if env.mac:
            import resource
            byte_size = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        else:
            byte_size = psutil.Process(os.getpid()).memory_info().peak_wset
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(byte_size, 1024)))
    return f"{round(byte_size / pow(1024, index), 2)} {size_name[index]}"


def comma_separator(list_: list) -> str:
    """Separates commas using simple ``.join()`` function and analysis based on length of the list taken as argument.

    Args:
        list_: Takes a list of elements as an argument.

    Returns:
        str:
        Comma separated list of elements.
    """
    return ", and ".join([", ".join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_)


def extract_time(input_: str) -> list:
    """Extracts 12-hour time value from a string.

    Args:
        input_: Int if found, else returns the received float value.

    Returns:
        list:
        Extracted time from the string.
    """
    return re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', input_) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', input_) or \
        re.findall(r'([0-9]+:[0-9]+\s?(?:am|pm:?))', input_) or \
        re.findall(r'([0-9]+\s?(?:am|pm:?))', input_)


def extract_nos(input_: str, method: type = float) -> Union[int, float]:
    """Extracts number part from a string.

    Args:
        input_: Takes string as an argument.
        method: Takes a type to return a float or int value.

    Returns:
        float:
        Float values.
    """
    if value := re.findall(r"\d+", input_):
        return method(".".join(value))


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


def matrix_to_flat_list(input_: List[list]) -> list:
    """Converts a matrix into flat list.

    Args:
        input_: Takes a list of list as an argument.

    Returns:
        list:
        Flat list.
    """
    return sum(input_, []) or [item for sublist in input_ for item in sublist]


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
    for word in input_.replace('-', ' ').split(' '):
        if word in number_mapping:
            numbers.append(number_mapping[word])
        elif word == 'hundred':
            numbers[-1] *= 100
        elif word == 'thousand':
            numbers = [x * 1000 for x in numbers]
        elif word == 'million':
            numbers = [x * 1000000 for x in numbers]
    return sum(numbers)


def number_to_words(input_: Union[int, str], capitalize: bool = False) -> str:
    """Converts integer version of a number into words.

    Args:
        input_: Takes the integer version of a number as an argument.
        capitalize: Boolean flag to capitalize the first letter.

    Returns:
        str:
        String version of the number.
    """
    result = inflect.engine().number_to_words(num=input_)
    return result[0].upper() + result[1:] if capitalize else result


def lock_files(alarm_files: bool = False, reminder_files: bool = False) -> list:
    """Checks for ``*.lock`` files within the ``alarm`` directory if present.

    Args:
        alarm_files: Takes a boolean value to gather list of alarm lock files.
        reminder_files: Takes a boolean value to gather list of reminder lock files.

    Returns:
        list:
        List of ``*.lock`` file names ignoring other hidden files.
    """
    if alarm_files:
        return [f for f in os.listdir("alarm") if not f.startswith(".")] if os.path.isdir("alarm") else None
    elif reminder_files:
        return [f for f in os.listdir("reminder") if not f.startswith(".")] if os.path.isdir("reminder") else None


def exit_message() -> str:
    """Variety of exit messages based on day of week and time of day.

    Returns:
        str:
        A greeting bye message.
    """
    am_pm = datetime.now().strftime("%p")  # current part of day (AM/PM)
    hour = datetime.now().strftime("%I")  # current hour
    day = datetime.now().strftime("%A")  # current day

    if am_pm == "AM" and int(hour) < 10:
        exit_msg = f"Have a nice day, and happy {day}."
    elif am_pm == "AM" and int(hour) >= 10:
        exit_msg = f"Enjoy your {day}."
    elif am_pm == "PM" and (int(hour) == 12 or int(hour) < 3) and day in ["Friday", "Saturday"]:
        exit_msg = "Have a nice afternoon, and enjoy your weekend."
    elif am_pm == "PM" and (int(hour) == 12 or int(hour) < 3):
        exit_msg = "Have a nice afternoon."
    elif am_pm == "PM" and int(hour) < 6 and day in ["Friday", "Saturday"]:
        exit_msg = "Have a nice evening, and enjoy your weekend."
    elif am_pm == "PM" and int(hour) < 6:
        exit_msg = "Have a nice evening."
    elif day in ["Friday", "Saturday"]:
        exit_msg = "Have a nice night, and enjoy your weekend."
    else:
        exit_msg = "Have a nice night."

    if event := celebrate():
        exit_msg += f"\nAnd by the way, happy {event}"

    return exit_msg


def scan_smart_devices() -> NoReturn:
    """Retrieves devices IP by doing a local IP range scan using Netgear API.

    See Also:
        - This can also be done my manually passing the IP addresses in a list (for lights) or string (for TV)
        - Using Netgear API will avoid the manual change required to rotate the IPs whenever the router is restarted.
    """
    smart_devices = LocalIPScan().smart_devices()
    with open(fileio.smart_devices, 'w') as file:
        yaml.dump(stream=file, data=smart_devices)


def daytime_nighttime_swapper() -> NoReturn:
    """Automatically puts the Mac on sleep and sets the volume to 25% after 9 PM and 50% after 6 AM."""
    hour = int(datetime.now().strftime("%H"))
    locker = """osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'"""
    if 20 >= hour >= 7:
        volume.volume(level=50)
    elif hour >= 21 or hour <= 6:
        volume.volume(level=30)
        if env.mac:
            display_functions.decrease_brightness()
            os.system(locker)


def no_env_vars() -> NoReturn:
    """Says a message about permissions when env vars are missing."""
    logger.error(f"Called by: {sys._getframe(1).f_code.co_name}")  # noqa
    speaker.speak(text=f"I'm sorry {env.title}! I lack the permissions!")


def keygen(length: int, punctuation: bool = False) -> str:
    """Generates random key.

    Args:
        length: Length of the keygen.
        punctuation: A boolean flag to include punctuation in the keygen.

    Returns:
        str:
        10 digit random key as a string.
    """
    if punctuation:
        required_str = string.ascii_letters + string.digits + string.punctuation
    else:
        required_str = string.ascii_letters + string.digits
    return "".join(random.choices(required_str, k=length))


def flush_screen() -> NoReturn:
    """Flushes the screen output."""
    sys.stdout.flush()
    sys.stdout.write("\r")


def block_print() -> NoReturn:
    """Suppresses print statement."""
    sys.stdout = open(os.devnull, 'w')


def release_print() -> NoReturn:
    """Removes print statement's suppression."""
    sys.stdout = sys.__stdout__


def missing_windows_features() -> NoReturn:
    """Speaker for unsupported features in Windows."""
    speaker.speak(text=f"Requested feature is not available in Windows {env.title}")


def hashed(key: uuid.UUID) -> str:
    """Generates sha from UUID.

    Args:
        key: Takes the UUID generated as an argument.

    Returns:
        str:
        Hashed value of the UUID received.
    """
    return hashlib.sha1(key.bytes + bytes(key.hex, "utf-8")).digest().hex()


def token() -> str:
    """Generates a token using hashed uuid4.

    Returns:
        str:
        Returns hashed UUID as a string.
    """
    return hashed(key=uuid.uuid4())
