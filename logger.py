"""Initiates logger to log start time, restart time, results from security mode and offline communicator
In order to use a common logger and use the same logger in multiple files, logger has been created dedicatedly."""

import logging

logging.basicConfig(filename='threshold.log', filemode='a', level=logging.FATAL,
                    format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('jarvis.py')
