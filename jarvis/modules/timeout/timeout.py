import multiprocessing
import time
from logging import Logger
from typing import Callable, Union

from jarvis.modules.responder import Response


def timeout(seconds: Union[int, float], function: Callable,
            args: Union[list, tuple] = None, kwargs: dict = None, logger: Logger = None) -> Response:
    """Runs the given function.

    Args:
        seconds: Timeout after which the said function has to be terminated.
        function: Function to run and timeout.
        args: Args to be passed to the function.
        kwargs: Keyword args to be passed to the function.
        logger: Logger to optionally log the timeout events.

    Returns:
        Response:
        A custom response class to indicate whether the function completed within the set timeout.
    """
    process = multiprocessing.Process(target=function, args=args or [], kwargs=kwargs or {})
    _start = time.time()
    if logger:
        logger.info(f"Starting {function.__name__} at {time.strftime('%H:%M:%S', time.localtime(_start))} with "
                    f"timeout: {seconds}")
    process.start()
    process.join(timeout=seconds)
    exec_time = round(float(time.time() - _start), 2)
    logger.info(f"Joined process {process.pid} after {exec_time} seconds.") if logger else None
    if process.is_alive():
        logger.warning(f"Process {process.pid} is still alive. Terminating.") if logger else None
        process.terminate()
        process.join(timeout=1e-01)
        try:
            logger.info(f"Closing process: {process.pid}") if logger else None
            process.close()  # Close immediately instead of waiting to be garbage collected
        except ValueError as error:
            # Expected when join timeout is insufficient. The resources will be released eventually but not immediately.
            logger.error(error) if logger else None
        return Response(dictionary={
            "ok": False,
            "msg": f"Function [{function.__name__}] exceeded {seconds} seconds."
        })
    return Response(dictionary={
        "ok": True,
        "msg": f"Function [{function.__name__}] completed in {exec_time} seconds."
    })
