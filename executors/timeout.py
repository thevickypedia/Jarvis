import functools
import signal
from contextlib import contextmanager
from threading import Thread
from types import FrameType
from typing import Callable, NoReturn, Union


@contextmanager
def timeout_mac(duration: Union[int, float], capture_frame: bool = True) -> NoReturn:
    """Creates a timeout handler.

    Args:
        duration: Takes the duration as an argument.
        capture_frame: Takes a boolean flag whether to raise a ``TimeoutError`` along with the frame information.
    """

    def timeout_handler(signum: int, frame: FrameType):
        """Raises a TimeoutError.

        Args:
            signum: Takes the signal number as an argument.
            frame: Takes the trigger frame as an argument.

        Raises:
            TimeoutError
        """
        if capture_frame:
            raise TimeoutError(
                f'Block timed out with signal {signum} after {duration} seconds.\n{frame.f_code}'
            )
        else:
            raise TimeoutError(
                f'Block timed out after {duration} seconds.'
            )

    signal.signal(signalnum=signal.SIGALRM, handler=timeout_handler)  # noqa
    signal.alarm(duration)
    yield
    signal.alarm(0)


def timeout_win(duration: Union[float, int]) -> Callable:
    """Timeout handler for Windows OS.

    Args:
        duration: Takes the duration as an argument.

    Returns:
        Callable:
        Returns the decorator method.
    """

    def decorator(func: Callable) -> Callable:
        """Decorator for the function to be timed out.

        Args:
            func: Function that is to be timed out.

        Returns:
            Callable:
            Returns the wrapper.
        """

        @functools.wraps(wrapped=func)
        def wrapper(*args, **kwargs) -> TimeoutError:
            """Wrapper for the function that has to be timed out.

            Args:
                *args: Arguments for the function.
                **kwargs: Keyword arguments for the function.

            Raises:
                TimeoutError:
                Raises TimeoutError as specified.
            """
            result = {'ERROR': TimeoutError(f'Function [{func.__name__}] exceeded the timeout [{duration} seconds]!')}

            def place_holder() -> NoReturn:
                """A place-holder function to be called by the thread."""
                try:
                    result['ERROR'] = func(*args, **kwargs)
                except TimeoutError as error_:
                    result['ERROR'] = error_

            thread = Thread(target=place_holder, daemon=True)
            try:
                thread.start()
                thread.join(timeout=duration)
            except Exception as error:
                print("called")
                raise error
            base_error = result['ERROR']
            if isinstance(base_error, TimeoutError):
                raise TimeoutError(
                    base_error
                )
            return base_error

        return wrapper

    return decorator
