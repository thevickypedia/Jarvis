import signal
import time
from contextlib import contextmanager
from types import FrameType
from typing import NoReturn, Union


@contextmanager
def timeout(duration: Union[int, float], capture_frame: bool = True) -> NoReturn:
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

    signal.signal(signalnum=signal.SIGALRM, handler=timeout_handler)
    signal.alarm(duration)
    yield
    signal.alarm(0)


if __name__ == '__main__':
    import logging

    logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(fmt=logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
        datefmt="%b %d, %Y %H:%M:%S"
    ))
    logger.addHandler(hdlr=log_handler)
    logger.setLevel(level=logging.DEBUG)

    def _sleeper(duration: Union[int, float]) -> NoReturn:
        """Sleeps for the given duration and prints a finish message.

        Args:
            duration: Takes the duration in seconds as args.
        """
        start = time.time()
        time.sleep(duration)
        logger.info(f'Task Finished in {int(time.time() - start)}s')

    # Test1: Fails with a TimeoutError since sleep duration is longer than the set timeout
    with timeout(duration=2):
        try:
            _sleeper(duration=5)
        except TimeoutError as error:
            logger.error(error)
    # Test2: Passes since the sleep duration is less than the timeout and the function returns before hitting a timeout
    with timeout(duration=3):
        _sleeper(duration=2)
