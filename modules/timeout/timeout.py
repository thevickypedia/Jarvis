import multiprocessing
import time
from typing import Callable, Union

from modules.timeout.responder import Response


def timeout(seconds: Union[int, float], function: Callable,
            args: Union[list, tuple] = None, kwargs: dict = None) -> Response:
    """Runs the given function.

    Args:
        seconds: Timeout after which the said function has to be terminated.
        function: Function to run and timeout.
        args: Args to be passed to the function.
        kwargs: Keyword args to be passed to the function.

    Returns:
        Response:
        A custom response class to indicate whether the function completed within the set timeout.
    """
    process = multiprocessing.Process(target=function, args=args or [], kwargs=kwargs or {})
    _start = time.time()
    process.start()
    process.join(timeout=seconds)
    if process.is_alive():
        process.terminate()
        process.join(timeout=1e-01)
        try:
            process.close()  # Close immediately instead of waiting to be garbage collected
        except ValueError:
            # Expected when join timeout is insufficient. The resources will be released eventually but not immediately.
            pass
        return Response(dictionary={
            "ok": False,
            "msg": f"Function [{function.__name__}] exceeded {seconds} seconds."
        })
    return Response(dictionary={
        "ok": True,
        "msg": f"Function [{function.__name__}] completed in {round(float(time.time() - _start), 2)} seconds."
    })
