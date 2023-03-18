# noinspection PyUnresolvedReferences
"""Initiates a custom logger to be accessed across modules.

>>> CustomLogger

Disables loggers from imported modules, while using the root logger without having to load an external file.

"""

import importlib
import logging
import os
import sys
import time
from datetime import datetime
from logging.config import dictConfig
from typing import Union

import pytz

from jarvis.modules.models import models

if not os.path.isdir(os.path.join('logs', 'api')):
    os.makedirs(os.path.join('logs', 'api'))  # Recursively creates both logs and api directories if unavailable
elif not os.path.isdir('logs'):
    os.mkdir('logs')  # Creates only logs dir if limited mode is enabled

DEFAULT_LOG_FORM = '%(asctime)s - %(levelname)s - [%(processName)s:%(module)s:%(lineno)d] - %(funcName)s - %(message)s'
DEFAULT_FORMATTER = logging.Formatter(datefmt='%b-%d-%Y %I:%M:%S %p', fmt=DEFAULT_LOG_FORM)


def log_file(filename: str) -> str:
    """Creates a log file and writes the headers into it.

    Returns:
        str:
        Log filename.
    """
    return datetime.now().strftime(filename)


def custom_handler(filename: str = None, log_format: logging.Formatter = None) -> logging.FileHandler:
    """Creates a FileHandler, sets the log format and returns it.

    Returns:
        logging.FileHandler:
        Returns file handler.
    """
    handler = logging.FileHandler(filename=log_file(filename=filename or os.path.join('logs', 'jarvis_%d-%m-%Y.log')),
                                  mode='a')
    handler.setFormatter(fmt=log_format or DEFAULT_FORMATTER)
    return handler


importlib.reload(module=logging)
dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
logging.getLogger("_code_cache").propagate = False

logger = logging.getLogger(__name__)
logger.addHandler(hdlr=custom_handler())

if models.env.debug:
    logger.setLevel(level=logging.DEBUG)
else:
    logger.setLevel(level=logging.INFO)


class TestLogger:
    """This is a class to test logger to verify logging using module references and different logging levels.

    Logging works the same way regardless of callable method, static method, function or class.

    >>> TestLogger

    """

    def __init__(self):
        """Instantiates logger."""
        self.logger = logger

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def test_log(self) -> None:
        """Logs the caller function with a custom time."""
        logging.Formatter.converter = self.custom_time
        self.logger.error(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        self.logger.info("I was called by %s which was called by %s", called_func, parent_func)
        self.logger.info("I'm a special function as I use custom timezone, overriding logging.formatTime() method.")

    # noinspection PyUnusedLocal
    @staticmethod
    def custom_time(*args: Union[logging.Formatter, time.time]) -> time.struct_time:
        """Creates custom timezone for ``logging`` which gets used only when invoked by ``Docker``.

        This is used only when triggered within a ``docker container`` as it uses UTC timezone.

        Args:
            *args: Takes ``Formatter`` object and current epoch as arguments passed by ``formatTime`` from ``logging``.

        Returns:
            struct_time:
            A struct_time object which is a tuple of:
            **current year, month, day, hour, minute, second, weekday, year day and dst** *(Daylight Saving Time)*
        """
        utc_dt = pytz.utc.localize(datetime.utcnow())
        my_tz = pytz.timezone("US/Eastern")
        converted = utc_dt.astimezone(my_tz)
        return converted.timetuple()


if __name__ == '__main__':
    test_logger = TestLogger()
    test_logger.test_log()
    for method_name, return_value in TestLogger.__dict__.items():
        if callable(return_value):
            print(method_name)
