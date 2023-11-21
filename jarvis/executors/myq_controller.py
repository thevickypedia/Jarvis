import asyncio
from threading import Thread
from typing import Any, Callable

from pymyq.errors import AuthenticationError, RequestError

from jarvis.modules.audio import speaker
from jarvis.modules.exceptions import CoverNotOnline, NoCoversFound
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.myq import myq
from jarvis.modules.retry import retry
from jarvis.modules.utils import support


class AsyncThread(Thread):
    """Runs asynchronosly using threading.

    >>> AsyncThread

    """

    def __init__(self, func: Callable, args: Any, kwargs: Any):
        """Initiates ``AsyncThread`` object as a super class.

        Args:
            func: Function that has to be triggered.
            args: Arguments.
            kwargs: Keyword arguments.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        super().__init__()

    def run(self) -> None:
        """Initiates ``asyncio.run`` with arguments passed."""
        self.result = asyncio.run(self.func(*self.args, **self.kwargs))


@retry.retry(attempts=3, warn=False, exclude_exc=(RequestError, AuthenticationError))
def run_async(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Checks if an existing loop is running in asyncio and triggers the loop with or without a thread accordingly.

    Args:
        func: Function that has to be triggered.
        args: Arguments.
        kwargs: Keyword arguments.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        thread = AsyncThread(func, args, kwargs)
        thread.start()
        thread.join()
        return thread.result
    else:
        return asyncio.run(func(*args, **kwargs))


def garage(phrase: str) -> None:
    """Handler for the garage door controller.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if all((models.env.myq_username, models.env.myq_password)):
        phrase = phrase.lower()
    else:
        support.no_env_vars()
        return

    logger.info("Getting status of the garage door.")
    try:
        response = run_async(func=myq.garage_controller, phrase=phrase)
    except NoCoversFound as error:
        logger.error(error)
        response = f"No garage doors were found in your MyQ account {models.env.title}! " \
                   "Please check your MyQ account and add a garage door name to control it."
    except CoverNotOnline as error:
        logger.error(error)
        response = f"I'm sorry {models.env.title}! Your {error.device} is not online!"
    speaker.speak(text=response)
