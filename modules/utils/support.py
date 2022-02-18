# noinspection PyUnresolvedReferences
"""This is a space for support functions used across different modules.

>>> Support

"""

import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from difflib import SequenceMatcher
from resource import RUSAGE_SELF, getrusage

import yaml
from appscript import app as apple_script
from holidays import CountryHoliday

from executors.custom_logger import logger
from modules.audio import speaker
from modules.netgear.ip_scanner import LocalIPScan
from modules.utils import globals

env = globals.ENV


def flush_screen():
    """Flushes the screen output."""
    sys.stdout.flush()
    sys.stdout.write("\r")


def initiate_tunneling(offline_host: str, offline_port: int, home: str) -> None:
    """Initiates Ngrok to tunnel requests from external sources if they aren't running already.

    Notes:
        - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the port ``4483``.
        - The connection is tunneled through a public facing URL used to make ``POST`` requests to Jarvis API.
    """
    ngrok_status = False
    target_script = 'forever_ngrok.py'
    activator = 'source venv/bin/activate'

    pid_check = subprocess.check_output(f"ps -ef | grep {target_script}", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'grep' not in id_ and '/bin/sh' not in id_:
            if target_script == 'forever_ngrok.py':
                ngrok_status = True
                logger.info('An instance of ngrok connection for offline communicator is running already.')
    if not ngrok_status:
        if os.path.exists(f"{home}/JarvisHelper"):
            logger.info('Initiating ngrok connection for offline communicator.')
            initiate = f'cd {home}/JarvisHelper && {activator} && export port={offline_port} && python {target_script}'
            apple_script('Terminal').do_script(initiate)
        else:
            logger.error(f'JarvisHelper is not available to trigger an ngrok tunneling through {offline_port}')
            endpoint = rf'http:\\{offline_host}:{offline_port}'
            logger.error(f'However offline communicator can still be accessed via '
                         f'{endpoint}\\offline-communicator for API calls and {endpoint}\\docs for docs.')


def celebrate() -> str:
    """Function to look if the current date is a holiday or a birthday.

    Returns:
        str:
        A string of the event observed today.
    """
    day = datetime.today().date()
    today = datetime.now().strftime("%d-%B")
    us_holidays = CountryHoliday('US').get(day)  # checks if the current date is a US holiday
    in_holidays = CountryHoliday('IND', prov='TN', state='TN').get(day)  # checks if Indian (esp TN) holiday
    if in_holidays:
        return in_holidays
    elif us_holidays and 'Observed' not in us_holidays:
        return us_holidays
    elif (birthday := os.environ.get('birthday')) and today == birthday:
        return 'Birthday'


def part_of_day() -> str:
    """Checks the current hour to determine the part of day.

    Returns:
        str:
        Morning, Afternoon, Evening or Night based on time of day.
    """
    current_hour = int(datetime.now().strftime("%H"))
    if 5 <= current_hour <= 11:
        return 'Morning'
    if 12 <= current_hour <= 15:
        return 'Afternoon'
    if 16 <= current_hour <= 19:
        return 'Evening'
    return 'Night'


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
    if days:
        return f'{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds'
    elif hours:
        return f'{hours} hours, {minutes} minutes, and {seconds} seconds'
    elif minutes:
        return f'{minutes} minutes, and {seconds} seconds'
    elif seconds:
        return f'{seconds} seconds'


def get_capitalized(phrase: str, dot: bool = True) -> str:
    """Looks for words starting with an upper-case letter.

    Args:
        phrase: Takes input string as an argument.
        dot: Takes a boolean flag whether to include words separated by (.) dot.

    Returns:
        str:
        Returns the upper case words if skimmed.
    """
    place = ''
    for word in phrase.split():
        if word[0].isupper():
            place += word + ' '
        elif '.' in word and dot:
            place += word + ' '
    if place:
        return place


def get_closest_match(text: str, match_list: list) -> str:
    """Get the closest matching word from a list of words.

    Args:
        text: Text to look for in the matching list.
        match_list: List to be compared against.

    Returns:
        str:
        Returns the text that matches closest in the list.
    """
    closest_match = [{'key': key, 'val': SequenceMatcher(a=text, b=key).ratio()} for key in match_list]
    return sorted(closest_match, key=lambda d: d['val'], reverse=True)[0].get('key')


def unrecognized_dumper(train_data: dict) -> None:
    """If none of the conditions are met, converted text is written to a yaml file for training purpose.

    Args:
        train_data: Takes the dictionary that has to be written as an argument.
    """
    dt_string = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")
    if os.path.isfile('training_data.yaml'):
        with open('training_data.yaml') as reader:
            data = yaml.safe_load(stream=reader) or {}
        for key, value in train_data.items():
            if data.get(key):
                data[key].update({dt_string: value})
            else:
                data.update({key: {dt_string: value}})
    else:
        data = {key1: {dt_string: value1} for key1, value1 in train_data.items()}

    with open('training_data.yaml', 'w') as writer:
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
        byte_size = getrusage(RUSAGE_SELF).ru_maxrss
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(byte_size, 1024)))
    return f'{round(byte_size / pow(1024, index), 2)} {size_name[index]}'


def comma_separator(list_: list) -> str:
    """Separates commas using simple ``.join()`` function and analysis based on length of the list taken as argument.

    Args:
        list_: Takes a list of elements as an argument.

    Returns:
        str:
        Comma separated list of elements.
    """
    return ', and '.join([', '.join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_)


def extract_nos(input_: str) -> float:
    """Extracts number part from a string.

    Args:
        input_: Takes string as an argument.

    Returns:
        float:
        Float values.
    """
    if value := re.findall(r"\d+", input_):
        return float('.'.join(value))


def format_nos(input_: float) -> int:
    """Removes ``.0`` float values.

    Args:
        input_: Int if found, else returns the received float value.

    Returns:
        int:
        Formatted integer.
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
    return ''.join([i for i in input_ if not i.isdigit() and i not in [',', '.', '?', '-', ';', '!', ':']]).strip()


def stop_terminal() -> None:
    """Uses pid to kill terminals as terminals await user confirmation interrupting shutdown/restart."""
    pid_check = subprocess.check_output("ps -ef | grep 'iTerm\\|Terminal'", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'Applications' in id_ and '/usr/bin/login' not in id_:
            os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout


def remove_files() -> None:
    """Function that deletes multiple files when called during exit operation.

    Warnings:
        Deletes:
            - all ``.lock`` files created for alarms and reminders.
            - ``location.yaml`` file, to recreate a new one next time around.
            - ``meetings`` file, to recreate a new one next time around.
    """
    shutil.rmtree('alarm') if os.path.isdir('alarm') else None
    shutil.rmtree('reminder') if os.path.isdir('reminder') else None
    os.remove('location.yaml') if os.path.isfile('location.yaml') else None
    os.remove('meetings') if os.path.isfile('meetings') else None


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
        return [f for f in os.listdir('alarm') if not f.startswith('.')] if os.path.isdir('alarm') else None
    elif reminder_files:
        return [f for f in os.listdir('reminder') if not f.startswith('.')] if os.path.isdir('reminder') else None


def terminator() -> None:
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc.

    Using this, eliminates the hassle of forcing multiple threads to stop.

    Examples:
        - os._exit(0)
        - kill -15 `PID`
    """
    pid_check = subprocess.check_output("ps -ef | grep jarvis.py", shell=True)
    pid_list = pid_check.decode('utf-8').splitlines()
    for pid_info in pid_list:
        if pid_info and 'grep' not in pid_info and '/bin/sh' not in pid_info:
            os.system(f'kill -15 {pid_info.split()[1].strip()}')


def exit_message() -> str:
    """Variety of exit messages based on day of week and time of day.

    Returns:
        str:
        A greeting bye message.
    """
    am_pm = datetime.now().strftime("%p")  # current part of day (AM/PM)
    hour = datetime.now().strftime("%I")  # current hour
    day = datetime.now().strftime("%A")  # current day

    if am_pm == 'AM' and int(hour) < 10:
        exit_msg = f"Have a nice day, and happy {day}."
    elif am_pm == 'AM' and int(hour) >= 10:
        exit_msg = f"Enjoy your {day}."
    elif am_pm == 'PM' and (int(hour) == 12 or int(hour) < 3) and day in ['Friday', 'Saturday']:
        exit_msg = "Have a nice afternoon, and enjoy your weekend."
    elif am_pm == 'PM' and (int(hour) == 12 or int(hour) < 3):
        exit_msg = "Have a nice afternoon."
    elif am_pm == 'PM' and int(hour) < 6 and day in ['Friday', 'Saturday']:
        exit_msg = "Have a nice evening, and enjoy your weekend."
    elif am_pm == 'PM' and int(hour) < 6:
        exit_msg = "Have a nice evening."
    elif day in ['Friday', 'Saturday']:
        exit_msg = "Have a nice night, and enjoy your weekend."
    else:
        exit_msg = "Have a nice night."

    if event := celebrate():
        exit_msg += f'\nAnd by the way, happy {event}'

    return exit_msg


def scan_smart_devices() -> dict:
    """Retrieves devices IP by doing a local IP range scan using Netgear API.

    See Also:
        This can also be done my manually passing the IP addresses in a list (for lights) or string (for TV)
        Using Netgear API will avoid the manual change required to rotate the IPs whenever the router is restarted.
    """
    if os.path.isfile('smart_devices.yaml'):
        with open('smart_devices.yaml') as file:
            data = yaml.load(stream=file, Loader=yaml.FullLoader)
        if data and data.get('restart'):
            os.remove('smart_devices.yaml')
        elif data:
            return data
    if router_pass := os.environ.get('router_pass'):
        local_devices = LocalIPScan(router_pass=router_pass)
        tv_ip, tv_mac = local_devices.tv()
        return {
            'hallway_ip': list(local_devices.hallway()),
            'kitchen_ip': list(local_devices.kitchen()),
            'bedroom_ip': list(local_devices.bedroom()),
            'tv_ip': tv_ip,
            'tv_mac': tv_mac
        }
    return {}


def no_env_vars():
    """Says a message about permissions when env vars are missing."""
    logger.error(f'Called by: {sys._getframe(1).f_code.co_name}')  # noqa
    speaker.speak(text="I'm sorry sir! I lack the permissions!")
