"""Wrapper for frequently used mapping files."""

import collections
import os
from threading import Timer
from typing import Any, DefaultDict, Dict, NoReturn, Union

import yaml

from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models


def get_contacts() -> Union[Dict[str, Dict[str, str]], DefaultDict[str, Dict[str, str]]]:
    """Reads the contact file and returns the data."""
    if os.path.isfile(models.fileio.contacts):
        with open(models.fileio.contacts) as file:
            try:
                if contacts := yaml.load(stream=file, Loader=yaml.FullLoader):
                    return contacts
            except yaml.YAMLError as error:
                logger.error(error)
    return collections.defaultdict(lambda: {}, phone={}, email={})


def get_frequent(func: str) -> Dict[str, int]:
    """Support getting frequently used keywords' mapping file.

    Args:
        func: Takes function name as an argument.
    """
    if os.path.isfile(models.fileio.frequent):
        try:
            with open(models.fileio.frequent) as file:
                data = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
        except yaml.YAMLError as error:
            data = {}
            logger.error(error)
        if data.get(func):
            data[func] += 1
        else:
            data[func] = 1
    else:
        data = {func: 1}
    return data


def put_frequent(data: Dict[str, int]) -> NoReturn:
    """Support writing frequently used keywords' mapping file.

    Args:
        data: Takes the mapping dictionary as an argument.
    """
    with open(models.fileio.frequent, 'w') as file:
        yaml.dump(data=data, stream=file, sort_keys=False)
        file.flush()  # Write everything in buffer to file right away


def get_location() -> Dict:
    """Reads the location file and returns the location data."""
    if os.path.isfile(models.fileio.location):
        try:
            with open(models.fileio.location) as file:
                if location := yaml.load(stream=file, Loader=yaml.FullLoader):
                    return location
        except yaml.YAMLError as error:
            logger.error(error)
    return collections.defaultdict(lambda: {}, address={}, latitude=0.0, longitude=0.0, reserved=False)


def get_secure_send() -> Dict[str, Dict[str, Any]]:
    """Get existing secure string information from the mapping file.

    Returns:
        Dict[str, Dict[str, Any]]:
        Dictionary of secure send data.
    """
    if os.path.isfile(models.fileio.secure_send):
        try:
            with open(models.fileio.secure_send) as file:
                return yaml.load(stream=file, Loader=yaml.FullLoader) or {}
        except yaml.YAMLError as error:
            logger.error(error)
    return collections.defaultdict(lambda: {})


def delete_secure_send(key: str) -> NoReturn:
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
        yaml.dump(data=current_data, stream=file, Dumper=yaml.SafeDumper)
        file.flush()  # Write buffer to file immediately


def put_secure_send(data: Dict[str, Dict[str, Any]]):
    """Add a particular secure key dictionary to the mapping file.

    Args:
        data: Data dict that has to be added.
    """
    existing = get_secure_send()
    with open(models.fileio.secure_send, 'w') as file:
        yaml.dump(data={**existing, **data}, stream=file, Dumper=yaml.SafeDumper)
        file.flush()  # Write buffer to file immediately
    logger.info("Secure dict for [%s] will be cleared after 5 minutes", [*[*data.values()][0].keys()][0])
    Timer(function=delete_secure_send, args=data.keys(), interval=300).start()
