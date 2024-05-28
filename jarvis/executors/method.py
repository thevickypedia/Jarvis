from typing import Callable

from jarvis.modules.logger import logger
from jarvis.modules.utils import shared


def executor(func: Callable, phrase: str) -> None:
    """Executes a function.

    Args:
        func: Function to be called.
        phrase: Takes the phrase spoken as an argument.
    """
    # disable logging for background tasks, as they are meant run very frequently
    if shared.called_by_bg_tasks:
        logger.propagate = False
        logger.disabled = True
        func(phrase)
        logger.propagate = True
        logger.disabled = False
    else:
        func(phrase)
