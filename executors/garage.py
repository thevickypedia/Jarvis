import asyncio
from threading import Thread
from typing import Any, Callable, NoReturn

from pymyq.errors import AuthenticationError, InvalidCredentialsError, MyQError

from executors.logger import logger
from modules.audio import speaker
from modules.models import models
from modules.myq.connector import Operation, garage_controller
from modules.utils import support


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

    def run(self) -> NoReturn:
        """Initiates ``asyncio.run`` with arguments passed."""
        self.result = asyncio.run(self.func(*self.args, **self.kwargs))


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


def garage_door(phrase: str) -> NoReturn:
    """Handler for the garage door controller.

    Args:
        phrase: Takes the recognized phrase as an argument.
    """
    if not all([models.env.myq_username, models.env.myq_password]):
        support.no_env_vars()
        return

    logger.info("Getting status of the garage door.")
    try:
        status = run_async(func=garage_controller, operation=Operation.STATE)
    except InvalidCredentialsError as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! Your credentials do not match.")
        return
    except AuthenticationError as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! There was an authentication error.")
        return
    except MyQError as error:
        logger.error(error)
        speaker.speak(text=f"I wasn't able to connect to the module {models.env.title}! "
                           "Please check the logs for more information.")
        return

    logger.info(status)
    if "open" in phrase:
        if status['state']['door_state'] == Operation.OPEN:
            speaker.speak(text=f"Your {status['name']} is already open {models.env.title}!")
            return
        elif status['state']['door_state'] == Operation.OPENING:
            speaker.speak(text=f"Your {status['name']} is currently opening {models.env.title}!")
            return
        elif status['state']['door_state'] == Operation.CLOSING:
            speaker.speak(text=f"Your {status['name']} is currently closing {models.env.title}! "
                               "You may want to try to after a minute or two!")
            return
        logger.info(f"Opening {status['name']}.")
        speaker.speak(text=f"Opening your {status['name']} {models.env.title}!")
        run_async(func=garage_controller, operation=Operation.OPEN)
    elif "close" in phrase:
        if status['state']['door_state'] == Operation.CLOSED:
            speaker.speak(text=f"Your {status['name']} is already closed {models.env.title}!")
            return
        elif status['state']['door_state'] == Operation.CLOSING:
            speaker.speak(text=f"Your {status['name']} is currently closing {models.env.title}!")
            return
        elif status['state']['door_state'] == Operation.OPENING:
            speaker.speak(text=f"Your {status['name']} is currently opening {models.env.title}! "
                               "You may want to try to after a minute or two!")
            return
        logger.info(f"Closing {status['name']}.")
        speaker.speak(text=f"Closing your {status['name']} {models.env.title}!")
        run_async(func=garage_controller, operation=Operation.CLOSE)
    else:
        logger.info(f"{status['name']}: {status['state']['door_state']}")
        speaker.speak(text=f"Your {status['name']} is currently {status['state']['door_state']} {models.env.title}! "
                           f"What do you want me to do to your {status['name']}?")
