# noinspection PyUnresolvedReferences
"""This is a space for support functions used across different modules.

>>> Support

"""
import math
import os
import socket
import string
import sys
import time
from datetime import datetime, timedelta, timezone
from http.client import HTTPSConnection
from typing import Any, Dict, Iterable, List, Tuple

import dateutil.tz
import inflect
import psutil
import pytz
import yaml
from dateutil import parser, relativedelta

from jarvis.executors import internet, others, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.utils import shared, util

ENGINE = inflect.engine()

days_in_week = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def hostname_to_ip(hostname: str, localhost: bool = True) -> List[str]:
    """Uses ``socket.gethostbyname_ex`` to translate a host name to IPv4 address format, extended interface.

    See Also:
        - A host may have multiple interfaces.
        - | In case of true DNS being used or the host entry file is carefully handwritten, the system will look
          | there to find the translation.
        - | But depending on the configuration, the host name can be bound to all the available interfaces, including
          | the loopback ones.
        - ``gethostbyname`` returns the address of the first of those interfaces in its own order.
        - | To get the assigned IP, ``gethostbyname_ex`` is used, which returns a list of all the interfaces, including
          | the host spot connected, and loopback IPs.

    References:
        https://docs.python.org/3/library/socket.html#socket.gethostbyname_ex

    Args:
        hostname: Takes the hostname of a device as an argument.
        localhost: Takes a boolean value to behave differently in case of localhost.
    """
    try:
        _hostname, _alias_list, _ipaddr_list = socket.gethostbyname_ex(hostname)
    except socket.error as error:
        logger.error("%s [%d] on %s", error.strerror, error.errno, hostname)
        return []
    logger.debug(
        {"Hostname": _hostname, "Alias": _alias_list, "Interfaces": _ipaddr_list}
    )
    if not _ipaddr_list:
        logger.critical("ATTENTION::No interfaces found for %s", hostname)
    elif len(_ipaddr_list) > 1:
        logger.warning(
            "Host %s has multiple interfaces. %s", hostname, _ipaddr_list
        ) if localhost else None
        return _ipaddr_list
    else:
        if localhost:
            ip_addr = internet.ip_address()
            if _ipaddr_list[0].split(".")[0] == ip_addr.split(".")[0]:
                return _ipaddr_list
            else:
                logger.error(
                    "NetworkID of the InterfaceIP [%s] of host '%s' does not match the network id of the "
                    "DeviceIP [%s].",
                    ip_addr,
                    hostname,
                    ", ".join(_ipaddr_list),
                )
                return []
        else:
            return _ipaddr_list


def country_timezone() -> Dict[str, str]:
    """Returns a mapping of timezone and the country where the timezone belongs."""
    timezone_country = {}
    for countrycode in pytz.country_timezones:
        timezones = pytz.country_timezones[countrycode]
        for timezone_ in timezones:
            timezone_country[timezone_] = countrycode
    return timezone_country


def get_capitalized(
    phrase: str, ignore: Iterable = None, dot: bool = True
) -> str | None:
    """Looks for words starting with an upper-case letter.

    Args:
        phrase: Takes input string as an argument.
        ignore: Takes an iterable of upper case strings to be ignored.
        dot: Takes a boolean flag whether to include words separated by (.) dot.

    Returns:
        str:
        Returns the upper case words if skimmed.
    """
    # Set ignore as a tuple with avoid keywords regardless of current state
    ignore = tuple(ignore or ()) + tuple(keywords.keywords["avoid"])
    place = ""
    for idx, word in enumerate(phrase.split()):
        # 1st letter should be upper-cased
        # Should not be the first word of the phrase
        # Should not be ignored
        if (
            word[0].isupper()
            and idx != 0
            and word.lower() not in map(lambda x: x.lower(), ignore)
        ):
            place += word + " "
        elif "." in word and dot:
            place += word + " "
    return place.strip() if place.strip() else None


def unrecognized_dumper(train_data: dict) -> None:
    """If none of the conditions are met, converted text is written to a yaml file for training purpose.

    Args:
        train_data: Takes the dictionary that has to be written as an argument.
    """
    dt_string = datetime.now().strftime("%B %d, %Y %H:%M:%S.%f")[:-3]
    data = {}
    if os.path.isfile(models.fileio.training_data):
        try:
            with open(models.fileio.training_data) as reader:
                data = yaml.load(stream=reader, Loader=yaml.FullLoader) or {}
        except yaml.YAMLError as error:
            logger.error(error)
            os.rename(
                src=models.fileio.training_data,
                dst=str(models.fileio.training_data).replace(
                    ".", f"_{datetime.now().strftime('%m_%d_%Y_%H_%M')}."
                ),
            )
        for key, value in train_data.items():
            if data.get(key):
                data[key].update({dt_string: value})
            else:
                data.update({key: {dt_string: value}})

    if not data:
        data = {key1: {dt_string: value1} for key1, value1 in train_data.items()}

    data = {
        func: {
            dt: unrec
            for dt, unrec in sorted(
                unrec_dict.items(),
                reverse=True,
                key=lambda item: datetime.strptime(item[0], "%B %d, %Y %H:%M:%S.%f"),
            )
        }
        for func, unrec_dict in data.items()
    }

    with open(models.fileio.training_data, "w") as writer:
        yaml.dump(data=data, stream=writer, sort_keys=False)


def size_converter(byte_size: int | float) -> str:
    """Gets the current memory consumed and converts it to human friendly format.

    Args:
        byte_size: Receives byte size as argument.

    Returns:
        str:
        Converted understandable size.
    """
    if not byte_size:
        byte_size = psutil.Process(pid=models.settings.pid).memory_info().rss
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(byte_size, 1024)))
    return (
        f"{util.format_nos(round(byte_size / pow(1024, index), 2))} {size_name[index]}"
    )


def check_restart() -> List[str]:
    """Checks for entries in the restart table in base db.

    Returns:
        list:
        Returns the flag, caller from the restart table.
    """
    with models.db.connection as connection:
        cursor = connection.cursor()
        flag = cursor.execute("SELECT flag, caller FROM restart").fetchone()
        cursor.execute("DELETE FROM restart")
        connection.commit()
    return flag


def utc_to_local(utc_dt: datetime) -> datetime:
    """Converts UTC datetime object to local datetime object.

    Args:
        utc_dt: Takes UTC datetime object as an argument

    Returns:
        datetime:
        Local datetime as an object.
    """
    # Tell datetime object that the tz is UTC
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    # Get local timezone
    local_tz = dateutil.tz.gettz(datetime.now().astimezone().tzname())
    # Convert the UTC timestamp to local
    return utc_dt.astimezone(local_tz)


def build_lookup() -> List[str]:
    """Build an array and get the number of days ahead and before of a certain day to lookup.

    Returns:
        List[str]:
        Returns a list of days ahead and before of the lookup date.
    """
    day_str = datetime.today().strftime("%A")
    floating_days = [""] * 8
    for idx, day in enumerate(days_in_week):
        if day == day_str:
            floating_days[0] = day_str
            floating_days[7] = day_str
            for i, j in zip(
                range(idx + 1, len(days_in_week)), range(1, len(days_in_week))
            ):
                floating_days[j] = days_in_week[i]
            for i in range(idx):
                floating_days[7 - (idx - i)] = days_in_week[i]
    return floating_days


def detect_lookup_date(phrase: str) -> Tuple[datetime, str]:
    """Converts general human phrases into datetime objects.

    Args:
        phrase: Takes input string as an argument.

    Returns:
        Tuple[datetime, str]:
        Returns a tuple of the datetime object, the detected/supported humanized date.
    """
    if "before" in phrase and "yesterday" in phrase:
        datetime_obj = datetime.today() - timedelta(days=2)
        addon = "day before yesterday"
    elif "yesterday" in phrase:
        datetime_obj = datetime.today() - timedelta(days=1)
        addon = "yesterday"
    elif "after" in phrase and "tomorrow" in phrase:
        datetime_obj = datetime.today() + timedelta(days=2)
        addon = "day after tomorrow"
    elif "tomorrow" in phrase:
        datetime_obj = datetime.today() + timedelta(days=1)
        addon = "tomorrow"
    else:
        return humanized_day_to_datetime(phrase=phrase)
    return datetime_obj, addon


def humanized_day_to_datetime(phrase: str) -> Tuple[datetime, str] | None:
    """Converts human date from general conversations into a datetime object.

    Args:
        phrase: Takes input string as an argument.

    See Also:
        - | Supports terms like ``day before yesterday``, ``yesterday``, ``tomorrow``, ``day after tomorrow``,
          | ``last friday``, ``this wednesday``, ``next monday``
        - For extended lookup, refer to extract_humanized_date

    Returns:
        Tuple[datetime, str]:
        Returns a tuple of the datetime object, the detected/supported humanized date.
    """
    floating_days = build_lookup()
    lookup_day = get_capitalized(phrase=phrase)
    # basically, if lookup day is in lower case
    if not lookup_day or lookup_day not in days_in_week:
        if matched := word_match.word_match(phrase=phrase, match_list=days_in_week):
            lookup_day = string.capwords(matched)
    if not lookup_day or lookup_day not in days_in_week:
        logger.error("Received incorrect lookup day: %s", lookup_day)
        return
    if "last" in phrase.lower():
        td = timedelta(days=-(7 - floating_days.index(lookup_day)))
        addon = f"last {lookup_day}"
    elif "next" in phrase.lower():
        td = timedelta(days=(7 + floating_days.index(lookup_day)))
        addon = f"next {lookup_day}"
    elif "this" in phrase.lower():
        td = timedelta(days=floating_days.index(lookup_day))
        addon = f"this {lookup_day}"
    else:
        logger.error("Supports only 'last', 'next' and 'this' but received %s", phrase)
        return
    return datetime.today() + td, addon


def extract_humanized_date(
    phrase: str, fail_past: bool = False
) -> Tuple[datetime.date, str, str] | None:
    """Converts most humanized date into datetime object.

    Args:
        phrase: Takes the phrase spoken as an argument.
        fail_past: Boolean value to raise an error in case the humanized datetime is in the past.

    Returns:
        Tuple[datetime.date, str, str]:
        A tuple of the date object, human friendly name, and the tense.
    """
    today = datetime.now().date()

    if "day after tomorrow" in phrase:
        return today + relativedelta.relativedelta(days=2), "day after tomorrow", "is"
    elif "day before yesterday" in phrase:
        if fail_past:
            raise ValueError("'day before yesterday' is in the past!")
        return (
            today - relativedelta.relativedelta(days=2),
            "day before yesterday",
            "was",
        )
    elif "tomorrow" in phrase:
        return today + relativedelta.relativedelta(days=1), "tomorrow", "is"
    elif "yesterday" in phrase:
        if fail_past:
            raise ValueError("'yesterday' is in the past!")
        return today - relativedelta.relativedelta(days=1), "yesterday", "was"

    try:
        parsed_date = parser.parse(phrase, fuzzy=True)
    except parser.ParserError as error:
        logger.error(error)
        return today, "today", "is"

    if "next" in phrase:
        next_occurrence = parsed_date + relativedelta.relativedelta(weeks=1)
        return (
            next_occurrence.date(),
            f"next {next_occurrence.strftime('%A')}, ({next_occurrence.strftime('%B')} "
            f"{ENGINE.ordinal(next_occurrence.strftime('%d'))})",
            "is",
        )
    elif "last" in phrase:
        last_occurrence = parsed_date - relativedelta.relativedelta(weeks=1)
        if fail_past:
            raise ValueError(f"'last {last_occurrence.strftime('%A')}' is in the past!")
        return (
            last_occurrence.date(),
            f"last {last_occurrence.strftime('%A')}, ({last_occurrence.strftime('%B')} "
            f"{ENGINE.ordinal(last_occurrence.strftime('%d'))})",
            "was",
        )

    # validates only the date, so the date might be same with a past-time
    if parsed_date.date() < today and fail_past:
        raise ValueError(f"{parsed_date!r} is in the past!")

    return (
        parsed_date.date(),
        f"{parsed_date.strftime('%A')}, ({parsed_date.strftime('%B')} "
        f"{ENGINE.ordinal(parsed_date.strftime('%d'))})",
        "is",
    )


def check_stop() -> List[str]:
    """Checks for entries in the stopper table in base db.

    Returns:
        list:
        Returns the flag, caller from the stopper table.
    """
    with models.db.connection as connection:
        cursor = connection.cursor()
        flag = cursor.execute("SELECT flag, caller FROM stopper").fetchone()
        cursor.execute("DELETE FROM stopper")
        connection.commit()
    return flag


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
    elif (
        am_pm == "PM"
        and (int(hour) == 12 or int(hour) < 3)
        and day in ["Friday", "Saturday"]
    ):
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

    if event := others.celebrate():
        exit_msg += f"\nAnd by the way, happy {event}"

    return exit_msg


def no_env_vars() -> None:
    """Says a message about permissions when env vars are missing."""
    logger.error("Called by: %s", sys._getframe(1).f_code.co_name)  # noqa
    speaker.speak(text=f"I'm sorry {models.env.title}! I lack the permissions!")


def unsupported_features() -> None:
    """Says a message about unsupported features."""
    logger.error("Called by: %s", sys._getframe(1).f_code.co_name)  # noqa
    speaker.speak(
        text=f"I'm sorry {models.env.title}! This feature is yet to be implemented on {models.settings.os}!"
    )


def write_screen(text: Any) -> None:
    """Write text on screen that can be cleared later.

    Args:
        text: Text to be written.
    """
    if shared.called_by_offline:
        return
    text = str(text).strip()
    if models.settings.interactive:
        term_size = os.get_terminal_size().columns
        sys.stdout.write(f"\r{' ' * term_size}")
        if len(text) > term_size:
            # Get 90% of the text size and ONLY print that on screen
            size = round(term_size * (90 / 100))
            sys.stdout.write(f"\r{text[:size].strip()}...")
            return
    sys.stdout.write(f"\r{text}")


def flush_screen() -> None:
    """Flushes the screen output.

    See Also:
        Writes new set of empty strings for the size of the terminal if ran using one.
    """
    if models.settings.interactive:
        sys.stdout.write(f"\r{' ' * os.get_terminal_size().columns}")
    else:
        sys.stdout.write("\r")


def number_to_words(input_: int | str, capitalize: bool = False) -> str:
    """Converts integer version of a number into words.

    Args:
        input_: Takes the integer version of a number as an argument.
        capitalize: Boolean flag to capitalize the first letter.

    Returns:
        str:
        String version of the number.
    """
    result = ENGINE.number_to_words(num=input_)
    return result[0].upper() + result[1:] if capitalize else result


def pluralize(
    count: int, word: str, to_words: bool = False, cap_word: bool = False
) -> str:
    """Helper for ``time_converter`` function.

    Args:
        count: Number based on which plural form should be determined.
        word: Word for which the plural form should be converted.
        to_words: Boolean flag to convert numeric to words in the response string.
        cap_word: If to_words is passed as True, then analyzes whether the first letter should be capitalized.

    Returns:
        str:
        String formatted time in singular or plural.
    """
    if to_words:
        return f"{number_to_words(input_=count, capitalize=cap_word)} {ENGINE.plural(text=word, count=count)}"
    return f"{count} {ENGINE.plural(text=word, count=count)}"


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
        return (
            f"{pluralize(day, 'day')}, {pluralize(hour, 'hour')}, "
            f"{pluralize(minute, 'minute')}, and {pluralize(second, 'second')}"
        )
    elif day and hour and minute:
        return (
            f"{pluralize(day, 'day')}, {pluralize(hour, 'hour')}, "
            f"and {pluralize(minute, 'minute')}"
        )
    elif day and hour:
        return f"{pluralize(day, 'day')}, and {pluralize(hour, 'hour')}"
    elif day:
        return pluralize(day, "day")
    elif hour and minute and second:
        return f"{pluralize(hour, 'hour')}, {pluralize(minute, 'minute')}, and {pluralize(second, 'second')}"
    elif hour and minute:
        return f"{pluralize(hour, 'hour')}, and {pluralize(minute, 'minute')}"
    elif hour:
        return pluralize(hour, "hour")
    elif minute and second:
        return f"{pluralize(minute, 'minute')}, and {pluralize(second, 'second')}"
    elif minute:
        return pluralize(minute, "minute")
    else:
        return pluralize(second, "second")


def remove_file(filepath: str, delay: int = 0) -> None:
    """Deletes the requested file after a certain time.

    Args:
        filepath: Filepath that has to be removed.
        delay: Delay in seconds after which the requested file is to be deleted.
    """
    time.sleep(delay)
    os.remove(filepath) if os.path.isfile(filepath) else logger.error(
        "%s not found.", filepath
    )


def stop_process(pid: int) -> None:
    """Stop a particular process using ``SIGTERM`` and ``SIGKILL`` signals.

    Args:
        pid: Process ID that has to be shut down.
    """
    try:
        proc = psutil.Process(pid=pid)
        if proc.is_running():
            proc.terminate()
        time.sleep(0.5)
        if proc.is_running():
            proc.kill()
    except psutil.NoSuchProcess as error:
        logger.debug(error)
    except psutil.AccessDenied as error:
        logger.error(error)


def connected_to_network() -> bool:
    """Function to check internet connection status.

    Returns:
        bool:
        True if connection is active, False otherwise.
    """
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if models.settings.os == enums.SupportedPlatforms.windows:
            # Recreate a new connection everytime
            connection = HTTPSConnection("8.8.8.8", timeout=5)
            connection.request("HEAD", "/")
        else:
            socket_.connect(("8.8.8.8", 80))
        return True
    except OSError as error:
        logger.error("OSError [%d]: %s", error.errno, error.strerror)
    except Exception as error:
        logger.critical(error)
