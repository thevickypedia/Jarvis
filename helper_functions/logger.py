"""Initiates logger to log start time, restart time, results from security mode and offline communicator
In order to use a common logger across multiple files, a dedicated logger has been created."""

from logging import basicConfig, getLogger, FATAL

basicConfig(filename='../threshold.log', filemode='a', level=FATAL,
            format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = getLogger('jarvis.py')
