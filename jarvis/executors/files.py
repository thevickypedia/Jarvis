"""Wrapper for frequently used mapping files."""

import collections
import os
from typing import DefaultDict, Dict, NoReturn, Union

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
