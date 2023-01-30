# noinspection PyUnresolvedReferences
"""This is a space for support functions used across different modules.

>>> Support

"""

import math
import os
import socket
import sys
import time
from datetime import datetime, timezone
from typing import Iterable, List, NoReturn, Union

import dateutil.tz
import inflect
import psutil
import yaml
from holidays import country_holidays

from jarvis.executors.internet import ip_address
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared

db = database.Database(database=models.fileio.base_db)


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
        logger.error(f"{error} on {hostname}")
        return []
    logger.debug({"Hostname": _hostname, "Alias": _alias_list, "Interfaces": _ipaddr_list})
    if not _ipaddr_list:
        logger.critical(f"ATTENTION::No interfaces found for {hostname}")
    elif len(_ipaddr_list) > 1:
        logger.warning(f"Host {hostname} has multiple interfaces. {_ipaddr_list}") if localhost else None
        return _ipaddr_list
    else:
        if localhost:
            ip_addr = ip_address()
            if _ipaddr_list[0].split('.')[0] == ip_addr.split('.')[0]:
                return _ipaddr_list
            else:
                logger.error(f"NetworkID of the InterfaceIP [{ip_addr}] of host {hostname!r} does not match the "
                             f"network id of the DeviceIP [{', '.join(_ipaddr_list)}].")
                return []
        else:
            return _ipaddr_list


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
    elif models.env.birthday == datetime.now().strftime("%d-%B"):
        return "Birthday"


def get_capitalized(phrase: str, ignore: Iterable = None, dot: bool = True) -> Union[str, None]:
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
    ignore = tuple(ignore or ()) + tuple(keywords.keywords.avoid)
    place = ""
    for word in phrase.split():
        if word[0].isupper() and word.lower() not in map(lambda x: x.lower(), ignore):  # convert iterable to lowercase
            place += word + " "
        elif "." in word and dot:
            place += word + " "
    return place.strip() if place.strip() else None


def unrecognized_dumper(train_data: dict) -> NoReturn:
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
                dst=str(models.fileio.training_data).replace(".", f"_{datetime.now().strftime('%m_%d_%Y_%H_%M')}.")
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
            dt: unrec for dt, unrec in sorted(unrec_dict.items(), reverse=True,
                                              key=lambda item: datetime.strptime(item[0], "%B %d, %Y %H:%M:%S.%f"))
        } for func, unrec_dict in data.items()
    }

    with open(models.fileio.training_data, 'w') as writer:
        yaml.dump(data=data, stream=writer, sort_keys=False)


def size_converter(byte_size: int) -> str:
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
    return f"{round(byte_size / pow(1024, index), 2)} {size_name[index]}"


def lock_files(alarm_files: bool = False, reminder_files: bool = False) -> List[str]:
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
    if reminder_files:
        return [f for f in os.listdir("reminder") if not f.startswith(".")] if os.path.isdir("reminder") else None


def check_restart() -> List[str]:
    """Checks for entries in the restart table in base db.

    Returns:
        list:
        Returns the flag, caller from the restart table.
    """
    with db.connection:
        cursor = db.connection.cursor()
        flag = cursor.execute("SELECT flag, caller FROM restart").fetchone()
        cursor.execute("DELETE FROM restart")
        db.connection.commit()
    return flag


def utc_to_local(utc_dt: datetime) -> datetime:
    """Converts UTC datetime object to local datetime object.

    Args:
        utc_dt: Takes UTC datetime object as an argument

    Returns:
        datetime:
        Local datetime as an object.
    """
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)  # Tell datetime object that the tz is UTC
    local_tz = dateutil.tz.gettz(datetime.now().astimezone().tzname())  # Get local timezone
    return utc_dt.astimezone(local_tz)  # Convert the UTC timestamp to local


def check_stop() -> List[str]:
    """Checks for entries in the stopper table in base db.

    Returns:
        list:
        Returns the flag, caller from the stopper table.
    """
    with db.connection:
        cursor = db.connection.cursor()
        flag = cursor.execute("SELECT flag, caller FROM stopper").fetchone()
        cursor.execute("DELETE FROM stopper")
        db.connection.commit()
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


def no_env_vars() -> NoReturn:
    """Says a message about permissions when env vars are missing."""
    logger.error(f"Called by: {sys._getframe(1).f_code.co_name}")  # noqa
    speaker.speak(text=f"I'm sorry {models.env.title}! I lack the permissions!")


def unsupported_features() -> NoReturn:
    """Says a message about unsupported features."""
    logger.error(f"Called by: {sys._getframe(1).f_code.co_name}")  # noqa
    speaker.speak(text=f"I'm sorry {models.env.title}! This feature is yet to be implemented on "
                       f"{shared.hosted_device['os_name']}!")


def flush_screen() -> NoReturn:
    """Flushes the screen output."""
    if models.settings.ide:
        sys.stdout.flush()
        sys.stdout.write("\r")
    else:
        sys.stdout.flush()
        sys.stdout.write(f"\r{' '.join(['' for _ in range(os.get_terminal_size().columns)])}")


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


def pluralize(count: int, word: str) -> str:
    """Helper for ``time_converter`` function.

    Args:
        count: Number based on which plural form should be determined.
        word: Word for which the plural form should be converted.

    Returns:
        str:
        String formatted time in singular or plural.
    """
    return f"{count} {inflect.engine().plural(text=word, count=count)}"


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


def remove_file(filepath: str, delay: int = 0) -> NoReturn:
    """Deletes the requested file after a certain time.

    Args:
        filepath: Filepath that has to be removed.
        delay: Delay in seconds after which the requested file is to be deleted.
    """
    time.sleep(delay)
    os.remove(filepath) if os.path.isfile(filepath) else logger.error(f"{filepath} not found.")


def stop_process(pid: int) -> NoReturn:
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
        logger.error(error)
