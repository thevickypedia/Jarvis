# noinspection PyUnresolvedReferences
"""Looger configuration specific for Jarvis API.

>>> Logger

See Also:
    - Configures custom logging for uvicorn.
    - Disables uvicorn access logs from printing on the screen.
    - Modifies application logs to match uvicorn default log format.
    - Creates a multiprocessing log wrapper, and adds a filter to include custom process name in the logger format.
"""

import importlib
import logging
import os
import pathlib
from logging.config import dictConfig

from jarvis.modules.logger import config

api_config = config.APIConfig()
config.multiprocessing_logger(filename=api_config.DEFAULT_LOG_FILENAME,
                              log_format=logging.Formatter(api_config.DEFAULT_LOG_FORMAT))


# Creates log files
if not os.path.isfile(config.APIConfig().ACCESS_LOG_FILENAME):
    pathlib.Path(config.APIConfig().ACCESS_LOG_FILENAME).touch()

if not os.path.isfile(config.APIConfig().DEFAULT_LOG_FILENAME):
    pathlib.Path(config.APIConfig().DEFAULT_LOG_FILENAME).touch()

# Configure logging
importlib.reload(module=logging)
dictConfig(config=api_config.LOG_CONFIG)
logging.getLogger("uvicorn.access").propagate = False  # Disables access logger in default logger to log independently
logger = logging.getLogger("uvicorn.default")
