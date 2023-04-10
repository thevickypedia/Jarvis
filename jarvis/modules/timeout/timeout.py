# noinspection PyUnresolvedReferences
"""Module that can be used to set timeout for a function.

>>> Timeout

"""

import multiprocessing
import time
from logging import Logger
from typing import Callable, Dict, List, Tuple, Union

from pydantic import PositiveFloat, PositiveInt


def timeout(seconds: Union[PositiveInt, PositiveFloat], function: Callable,
            args: Union[List, Tuple] = None, kwargs: Dict = None, logger: Logger = None) -> bool:
    """Run the given function and kill it if exceeds the set timeout.

    Args:
        seconds: Timeout after which the said function has to be terminated.
        function: Function to run and timeout.
        args: Args to be passed to the function.
        kwargs: Keyword args to be passed to the function.
        logger: Logger to optionally log the timeout events.

    Returns:
        bool:
        Boolean flag to indicate if the function completed within the set timeout.
    """
    process = multiprocessing.Process(target=function, args=args or [], kwargs=kwargs or {})
    _start = time.time()
    if logger:
        logger.info("Starting %s at %s with timeout: %s" %
                    (function.__name__, time.strftime('%H:%M:%S', time.localtime(_start)), seconds))
    process.start()
    process.join(timeout=seconds)
    exec_time = round(float(time.time() - _start), 2)
    logger.info("Joined process %d after %d seconds.", process.pid, exec_time) if logger else None
    if process.is_alive():
        logger.warning("Process %d is still alive. Terminating.", process.pid) if logger else None
        process.terminate()
        process.join(timeout=1e-01)
        try:
            logger.info("Closing process: %d", process.pid) if logger else None
            process.close()  # Close immediately instead of waiting to be garbage collected
        except ValueError as error:
            # Expected when join timeout is insufficient. The resources will be released eventually but not immediately.
            logger.error(error) if logger else None
        return False
    return True
