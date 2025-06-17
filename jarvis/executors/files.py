"""Wrapper for frequently used mapping files."""

import collections
import os
import shutil
import sys
import time
import warnings
from datetime import datetime
from threading import Timer
from typing import Any, DefaultDict, Dict, List, OrderedDict

import yaml
from pydantic import ValidationError
from pydantic.v1 import DirectoryPath, FilePath

from jarvis.modules.logger import logger
from jarvis.modules.models import classes, models


def _loader(
    filepath: FilePath,
    default: List[Any] | Dict[str, Any] | OrderedDict | DefaultDict = None,
) -> List[Any] | Dict[str, Any]:
    """Loads the given yaml file and returns the data.

    Args:
        filepath: YAML filepath to load.
        default: Default value if loading failed or file missing.

    Returns:
        List[Any] | Dict[str, Any]:
        Returns the YAML data as a list or dict.
    """
    caller = sys._getframe(1).f_code.co_name  # noqa
    try:
        with open(filepath) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader) or default
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.debug(error)
        logger.debug("Caller: %s", caller)
    return default


def _dumper(
    filepath: FilePath,
    data: List[Any] | Dict[str, Any] | OrderedDict | DefaultDict,
    indent: int = 2,
    sort_keys: bool = False,
) -> None:
    """Dumps the data into the given yaml filepath.

    Args:
        filepath: Filepath to dump.
        data: Data to dump.
        indent: Indentation to maintain.
        sort_keys: Boolean flag to sort the keys.
    """
    with open(filepath, "w") as file:
        yaml.dump(data=data, stream=file, sort_keys=sort_keys, indent=indent)
        file.flush()


def get_contacts() -> Dict[str, Dict[str, str]] | DefaultDict[str, Dict[str, str]]:
    """Reads the contact file and returns the data."""
    return _loader(
        models.fileio.contacts,
        default=collections.defaultdict(lambda: {}, phone={}, email={}),
    )


def get_frequent() -> Dict[str, int]:
    """Retrieve frequently used keywords' mapping file."""
    return _loader(models.fileio.frequent, default={})


def put_frequent(data: Dict[str, int]) -> None:
    """Writes frequently used keywords into a mapping file.

    Args:
        data: Takes the mapping dictionary as an argument.
    """
    _dumper(models.fileio.frequent, data)


def get_location() -> DefaultDict[str, Dict | float | bool]:
    """Reads the location file and returns the location data."""
    # noinspection PyTypeChecker
    return _loader(
        models.fileio.location,
        default=collections.defaultdict(
            lambda: {}, address={}, latitude=0.0, longitude=0.0, reserved=False
        ),
    )


def get_secure_send() -> Dict[str, Dict[str, Any]]:
    """Get existing secure-send information from the mapping file."""
    return _loader(models.fileio.secure_send, default={})


def delete_secure_send(key: str) -> None:
    """Delete a particular secure key dictionary stored in the mapping file.

    Args:
        key: Key in dictionary to be deleted.
    """
    current_data = get_secure_send()
    if current_data.get(key):
        logger.info("Deleting %s: %s", key, [*current_data[key].keys()][0])
        del current_data[key]
    else:
        logger.critical("data for key [%s] was removed unprecedentedly", key)
    _dumper(models.fileio.secure_send, current_data)


def put_secure_send(data: Dict[str, Dict[str, Any]]) -> None:
    """Add a particular secure key dictionary to the mapping file.

    Args:
        data: Data dict that has to be added.
    """
    existing = get_secure_send()
    _dumper(models.fileio.secure_send, {**existing, **data})
    logger.info(
        "Secure dict for [%s] will be cleared after 5 minutes",
        [*[*data.values()][0].keys()][0],
    )
    Timer(function=delete_secure_send, args=data.keys(), interval=300).start()


def get_custom_conditions() -> Dict[str, Dict[str, str]]:
    """Custom conditions to map specific keywords to one or many functions."""
    return _loader(models.fileio.conditions)


def get_restrictions() -> List[str]:
    """Function level restrictions to restrict certain keywords via offline communicator."""
    return _loader(models.fileio.restrictions, default=[])


def put_restrictions(restrictions: List[str]) -> None:
    """Function level restrictions to restrict certain keywords via offline communicator.

    Args:
        restrictions: A list of function names that has to be restricted.
    """
    _dumper(models.fileio.restrictions, restrictions)


def get_gpt_data() -> List[Dict[str, str]]:
    """Get history from Jarvis -> Ollama conversation."""
    return _loader(models.fileio.gpt_data)


def put_gpt_data(data: List[Dict[str, str]]) -> None:
    """Stores Jarvis -> Ollama conversations in a history file.

    Args:
        data: List of dictionaries that have to be saved for future reference.
    """
    _dumper(models.fileio.gpt_data, data, indent=4)


def get_automation() -> Dict[str, List[Dict[str, str | bool]] | Dict[str, str | bool]]:
    """Load automation data from feed file."""
    return _loader(models.fileio.automation, default={})


def put_automation(
    data: Dict[str, List[Dict[str, str | bool]] | Dict[str, str | bool]]
) -> None:
    """Dumps automation data into feed file.

    Args:
        data: Data that has to be dumped into the automation feed file.
    """
    # Sort the keys by timestamp
    try:
        sorted_data = {
            k: data[k]
            for k in sorted(data.keys(), key=lambda x: datetime.strptime(x, "%I:%M %p"))
        }
    except ValueError as error:
        logger.error(error)
        logger.error("Writing automation data without sorting")
        sorted_data = data

    _dumper(models.fileio.automation, sorted_data)


def get_smart_devices() -> dict | None:
    """Load smart devices' data from feed file."""
    return _loader(models.fileio.smart_devices)


def put_smart_devices(data: dict) -> None:
    """Dumps smart devices' data into feed file.

    Args:
        data: Data that has to be dumped into the smart devices' feed file.
    """
    _dumper(models.fileio.smart_devices, data)


def get_processes() -> Dict[str, List[int | List[str]]]:
    """Get the processes' mapping from stored map file."""
    return _loader(models.fileio.processes, default={})


def get_reminders() -> List[Dict[str, str]]:
    """Get all reminders stored."""
    return _loader(models.fileio.reminders, default=[])


def put_reminders(data: List[Dict[str, str]]) -> None:
    """Dumps the reminder data into the respective yaml file.

    Args:
        data: Data to be dumped.
    """
    _dumper(models.fileio.reminders, data)


def get_alarms() -> List[Dict[str, str | bool]]:
    """Get all alarms stored."""
    return _loader(models.fileio.alarms, default=[])


def put_alarms(data: List[Dict[str, str | bool]]) -> None:
    """Dumps the alarm data into the respective yaml file.

    Args:
        data: Data to be dumped.
    """
    return _dumper(models.fileio.alarms, data)


def get_recognizer() -> classes.RecognizerSettings:
    """Get the stored settings for speech recognition."""
    try:
        rec_data = _loader(models.fileio.recognizer, default={})
        return classes.RecognizerSettings(**rec_data)
    except (TypeError, ValidationError) as error:
        logger.debug(error)
    return classes.RecognizerSettings()


def get_crontab() -> List[str]:
    """Get list of stored crontab settings."""
    try:
        data = _loader(models.fileio.crontab, default=[])
        assert isinstance(data, list)
        return data
    except AssertionError as error:
        logger.error(error)
        os.rename(src=models.fileio.crontab, dst=models.fileio.tmp_crontab)
        warnings.warn("CRONTAB :: Invalid file format.")
    return []


def get_ip_info() -> Dict[str, Any]:
    """Get IP information from a stored yaml file."""
    return _loader(models.fileio.ip_info, default={})


def put_ip_info(data: Dict[str, Any]) -> None:
    """Store IP address information in a mapping file.

    Args:
        data: IP information to be stored.
    """
    data["timestamp"] = int(time.time())
    if not data.get("loc") and data.get("lat") and data.get("lon"):
        logger.debug("Writing loc info to IP data.")
        data["loc"] = f"{data['lat']},{data['lon']}"
    _dumper(models.fileio.ip_info, data)


def delete(path: FilePath | DirectoryPath) -> None:
    """Delete a file or directory.

    Args:
        path: File or directory path to be removed.
    """
    logger.info("Removing %s", path)
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        logger.warning("No such file or directory: %s", path.__str__())
