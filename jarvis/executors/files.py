"""Wrapper for frequently used mapping files."""

import collections
from threading import Timer
from typing import Any, DefaultDict, Dict, List, Union

import yaml
from pydantic import ValidationError

from jarvis.modules.logger import logger
from jarvis.modules.models import classes, models


def get_contacts() -> Union[Dict[str, Dict[str, str]], DefaultDict[str, Dict[str, str]]]:
    """Reads the contact file and returns the data."""
    try:
        with open(models.fileio.contacts) as file:
            if contacts := yaml.load(stream=file, Loader=yaml.FullLoader):
                return contacts
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return collections.defaultdict(lambda: {}, phone={}, email={})


def get_frequent() -> Dict[str, int]:
    """Support getting frequently used keywords' mapping file."""
    try:
        with open(models.fileio.frequent) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader) or {}
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return {}


def put_frequent(data: Dict[str, int]) -> None:
    """Support writing frequently used keywords' mapping file.

    Args:
        data: Takes the mapping dictionary as an argument.
    """
    with open(models.fileio.frequent, 'w') as file:
        yaml.dump(data=data, stream=file, sort_keys=False)
        file.flush()  # Write everything in buffer to file right away


def get_location() -> Dict:
    """Reads the location file and returns the location data."""
    try:
        with open(models.fileio.location) as file:
            if location := yaml.load(stream=file, Loader=yaml.FullLoader):
                return location
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return collections.defaultdict(lambda: {}, address={}, latitude=0.0, longitude=0.0, reserved=False)


def get_secure_send() -> Dict[str, Dict[str, Any]]:
    """Get existing secure string information from the mapping file.

    Returns:
        Dict[str, Dict[str, Any]]:
        Dictionary of secure send data.
    """
    try:
        with open(models.fileio.secure_send) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader) or {}
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return {}


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
    with open(models.fileio.secure_send, 'w') as file:
        yaml.dump(data=current_data, stream=file, Dumper=yaml.Dumper)
        file.flush()  # Write buffer to file immediately


def put_secure_send(data: Dict[str, Dict[str, Any]]):
    """Add a particular secure key dictionary to the mapping file.

    Args:
        data: Data dict that has to be added.
    """
    existing = get_secure_send()
    with open(models.fileio.secure_send, 'w') as file:
        yaml.dump(data={**existing, **data}, stream=file, Dumper=yaml.Dumper)
        file.flush()  # Write buffer to file immediately
    logger.info("Secure dict for [%s] will be cleared after 5 minutes", [*[*data.values()][0].keys()][0])
    Timer(function=delete_secure_send, args=data.keys(), interval=300).start()


def get_custom_conditions() -> Dict[str, Dict[str, str]]:
    """Custom conditions to map specific keywords to one or many functions.

    Returns:
        Dict[str, Dict[str, str]]:
        A unique key value pair of custom phrase as key and an embedded dict of function name and phrase.
    """
    try:
        with open(models.fileio.conditions) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader)
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)


def get_restrictions() -> List[str]:
    """Function level restrictions to restrict certain keywords via offline communicator.

    Returns:
        List[str]:
        A list of function names that has to be restricted.
    """
    try:
        with open(models.fileio.restrictions) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader)
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return []


def put_restrictions(restrictions: List[str]) -> None:
    """Function level restrictions to restrict certain keywords via offline communicator.

    Args:
        restrictions: A list of function names that has to be restricted.
    """
    with open(models.fileio.restrictions, 'w') as file:
        yaml.dump(data=restrictions, stream=file, indent=2, sort_keys=False)
        file.flush()  # Write buffer to file immediately


def get_gpt_data() -> List[Dict[str, str]]:
    """Get history from Jarvis -> ChatGPT conversation.

    Returns:
        List[Dict[str, str]]:
        A list of dictionaries with request and response key-value pairs.
    """
    try:
        with open(models.fileio.gpt_data) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader)
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)


def put_gpt_data(data: List[Dict[str, str]]) -> None:
    """Stores Jarvis -> ChatGPT conversations in a history file.

    Args:
        data: List of dictionaries that have to be saved for future reference.
    """
    with open(models.fileio.gpt_data, 'w') as file:
        yaml.dump(data=data, stream=file, indent=4, Dumper=yaml.Dumper)
        file.flush()  # Write buffer to file immediately


def get_automation() -> Dict[str, Union[List[Dict[str, Union[str, bool]]], Dict[str, Union[str, bool]]]]:
    """Load automation data from feed file.

    Returns:
        Dict[str, Union[List[Dict[str, Union[str, bool]]], Dict[str, Union[str, bool]]]]:
        Returns the automation data in the feed file.
    """
    try:
        with open(models.fileio.automation) as read_file:
            return yaml.load(stream=read_file, Loader=yaml.FullLoader) or {}
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return {}


def put_automation(data: Dict[str, Union[List[Dict[str, Union[str, bool]]], Dict[str, Union[str, bool]]]]) -> None:
    """Dumps automation data into feed file.

    Args:
        data: Data that has to be dumped into the automation feed file.
    """
    with open(models.fileio.automation, 'w') as file:
        yaml.dump(data=data, stream=file, indent=2, sort_keys=False)
        file.flush()  # Write buffer to file immediately


def get_smart_devices() -> Union[dict, bool, None]:
    """Load smart devices' data from feed file.

    Returns:
        Union[dict, bool]:
        Returns the smart devices' data in the feed file.
    """
    try:
        with open(models.fileio.smart_devices) as file:
            if smart_devices := yaml.load(stream=file, Loader=yaml.FullLoader):
                return smart_devices
            else:
                logger.warning("'%s' is empty.", models.fileio.smart_devices)
    except (yaml.YAMLError, FileNotFoundError) as error:
        if isinstance(error, FileNotFoundError):
            logger.warning("%s not found.", models.fileio.smart_devices)
            return
        else:
            logger.error(error)
            return False


def put_smart_devices(data: dict) -> None:
    """Dumps smart devices' data into feed file.

    Args:
        data: Data that has to be dumped into the smart devices' feed file.
    """
    with open(models.fileio.smart_devices, 'w') as file:
        yaml.dump(data=data, stream=file, indent=2, sort_keys=False)
        file.flush()  # Write buffer to file immediately


def get_processes() -> Dict[str, List[Union[int, List[str]]]]:
    """Get the processes' mapping from stored map file.

    Returns:
        Dict[str, List[Union[int, List[str]]]]:
        Processes' mapping data.
    """
    try:
        with open(models.fileio.processes) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader) or {}
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return {}


def get_reminders() -> List[Dict[str, str]]:
    """Get all reminders stored.

    Returns:
        List[Dict[str, str]]:
        Returns a list of dictionary of information for stored reminders.
    """
    try:
        with open(models.fileio.reminders) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader) or []
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return []


def put_reminders(data: List[Dict[str, str]]):
    """Dumps the reminder data into the respective yaml file.

    Args:
        data: Data to be dumped.
    """
    with open(models.fileio.reminders, 'w') as file:
        yaml.dump(data=data, stream=file, indent=2, sort_keys=False)
        file.flush()  # Write buffer to file immediately


def get_alarms() -> List[Dict[str, Union[str, bool]]]:
    """Get all alarms stored.

    Returns:
        Dict[str, Union[str, bool]]:
        Returns a dictionary of information for stored alarms.
    """
    try:
        with open(models.fileio.alarms) as file:
            return yaml.load(stream=file, Loader=yaml.FullLoader) or []
    except (yaml.YAMLError, FileNotFoundError) as error:
        logger.error(error)
    return []


def put_alarms(data: List[Dict[str, Union[str, bool]]]):
    """Dumps the alarm data into the respective yaml file.

    Args:
        data: Data to be dumped.
    """
    with open(models.fileio.alarms, 'w') as file:
        yaml.dump(data=data, stream=file, indent=2, sort_keys=False)
        file.flush()  # Write buffer to file immediately


def get_recognizer() -> classes.RecognizerSettings:
    """Get the stored settings for speech recognition.

    Returns:
        RecognizerSettings:
        Returns the parsed recognizer settings or default.
    """
    try:
        with open(models.fileio.recognizer) as file:
            rec_data = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
        return classes.RecognizerSettings(**rec_data)
    except (yaml.YAMLError, FileNotFoundError, TypeError, ValidationError) as error:
        logger.error(error)
    return classes.RecognizerSettings()
