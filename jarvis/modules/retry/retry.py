# noinspection PyUnresolvedReferences
"""Module that creates a wrapper that can be used to functions that should be retried upon exceptions.

>>> Retry

"""

import functools
import time
import warnings
from typing import Any, Callable, NoReturn, Union

import inflect

from jarvis.modules.logger.custom_logger import logger


def retry(attempts: int = 3, interval: Union[int, float] = 0, warn: bool = False, exclude_exc=None) -> \
        Union[Callable, Any, NoReturn, None]:
    """Wrapper for any function that has to be retried upon failure.

    Args:
        attempts: Number of retry attempts.
        interval: Seconds to wait between each iteration.
        warn: Takes a boolean flag whether to throw a warning message instead of raising final exception.
        exclude_exc: Exception that has to be logged and ignored.

    Returns:
        Callable:
        Calls the decorator function.
    """

    def decorator(func: Callable) -> Callable:
        """Calls the child func recursively.

        Args:
            func: Takes the function as an argument. Implemented as a decorator.

        Returns:
            Callable:
            Calls the wrapper functon.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Callable:
            """Executes the wrapped function in a loop for the number of attempts mentioned.

            Args:
                *args: Arguments.
                **kwargs: Keyword arguments.

            Returns:
                Callable:
                Return value of the function implemented.

            Raises:
                Raises the exception as received beyond the given number of attempts.
            """
            return_exc = None
            for i in range(1, attempts + 1):
                try:
                    return_val = func(*args, **kwargs)
                    # Log messages only when the function did not return during the first attempt
                    if i > 1:
                        logger.info(msg=f"{func.__name__} returned at {inflect.engine().ordinal(num=i)} attempt")
                    return return_val
                except exclude_exc or KeyboardInterrupt as excl_error:
                    logger.error(msg=excl_error)
                except Exception as error:
                    return_exc = error
                time.sleep(interval)
            logger.error(msg=f"{func.__name__} exceeded retry count::{attempts}")
            if return_exc and warn:
                warnings.warn(
                    f"{type(return_exc).__name__}: {return_exc}"
                )
            elif return_exc:
                raise return_exc

        return wrapper

    return decorator
