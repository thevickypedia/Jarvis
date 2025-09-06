# noinspection PyUnresolvedReferences
"""Looger configuration specific for Jarvis API.

>>> Logger

See Also:
    - Configures custom logging for uvicorn.
    - Disables uvicorn access logs from printing on the screen.
    - Modifies application logs to match uvicorn default log format.
    - Creates a multiprocessing log wrapper, and adds a filter to include custom process name in the logger format.
"""

import logging
import os
import pathlib
from logging.config import dictConfig

from jarvis.modules.logger import APIConfig, multiprocessing_logger

api_config = APIConfig()
multiprocessing_logger(filename=api_config.DEFAULT_LOG_FILENAME)

# Creates log files
if not os.path.isfile(api_config.ACCESS_LOG_FILENAME):
    pathlib.Path(api_config.ACCESS_LOG_FILENAME).touch()

if not os.path.isfile(api_config.DEFAULT_LOG_FILENAME):
    pathlib.Path(api_config.DEFAULT_LOG_FILENAME).touch()

# Configure logging
dictConfig(config=api_config.LOG_CONFIG)
# Disables access logger in default logger to log independently
logging.getLogger("uvicorn.access").propagate = False
logger = logging.getLogger("uvicorn.default")
