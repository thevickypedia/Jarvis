import functools
import time
from typing import Any, Callable, NoReturn, Optional, Union

from inflect import engine

from executors.logger import logger


def retry(attempts: int = 3, interval: Union[int, float] = 0, exclude_exc=None) -> \
        Optional[Union[Callable, Any, NoReturn]]:
    """Wrapper for any function that has to be retried upon failure.

    Args:
        attempts: Number of retry attempts.
        interval: Seconds to wait between each iteration.
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
                    logger.info(msg=f"Succeeded in {engine().ordinal(num=i)} attempt.")
                    return return_val
                except exclude_exc or KeyboardInterrupt as excl_error:
                    logger.error(msg=excl_error)
                except Exception as error:
                    return_exc = error
                time.sleep(interval)
            logger.error(msg=f"Exceeded retry count::{attempts}")
            if return_exc:
                raise return_exc

        return wrapper

    return decorator
