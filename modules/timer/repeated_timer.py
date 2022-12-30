from threading import Timer
from typing import Callable, NoReturn, Union

from modules.logger.custom_logger import logger


class RepeatedTimer:
    """Initiate ``RepeatedTimer`` object to run a task repeated after given intervals.

    >>> RepeatedTimer

    """

    def __init__(self, interval: Union[int, float], function: Callable, *args, **kwargs):
        """Instantiates the object and starts the task.

        Args:
            interval: Seconds after which the task should be triggered repeatedly.
            function: Function that has to be called.
            *args: Arguments.
            **kwargs: Keyword arguments.
        """
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self) -> NoReturn:
        """Initiates function."""
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self) -> NoReturn:
        """Checks if task is running, schedules a thread timer otherwise."""
        if not self.is_running:
            logger.info(f"Starting {self.function.__name__} to execute {', '.join(self.args or self.kwargs)!r}")
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self) -> NoReturn:
        """Flips the running flag to False and cancels the existing timer."""
        logger.info(f"Stopping {self.function.__name__} while executing {', '.join(self.args or self.kwargs)!r}")
        self._timer.cancel()
        self.is_running = False
