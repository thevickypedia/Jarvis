import functools
import time
from typing import Any, Callable


def timed_cache(max_age: int, maxsize: int = 128, typed: bool = False):
    """Least-recently-used cache decorator with time-based cache invalidation.

    Args:
        max_age: Time to live for cached results (in seconds).
        maxsize: Maximum cache size (see `functools.lru_cache`).
        typed: Cache on distinct input types (see `functools.lru_cache`).

    See Also:
        - ``lru_cache`` takes all params of the function and creates a key.
        - If even one key is changed, it will map to new entry thus refreshed.
        - This is just a trick to force lru_cache lib to provide TTL on top of max size.
        - Uses ``time.monotonic`` since ``time.time`` relies on the system clock and may not be monotonic.
        - | ``time.time()`` not always guaranteed to increase,
          | it may in fact decrease if the machine syncs its system clock over a network.
    """

    def _decorator(fn: Callable) -> Any:
        """Decorator for the timed cache.

        Args:
            fn: Function that has been decorated.
        """

        @functools.lru_cache(maxsize=maxsize, typed=typed)
        def _new(*args, __timed_hash, **kwargs):
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        def _wrapped(*args, **kwargs):
            return _new(*args, **kwargs, __timed_hash=int(time.monotonic() / max_age))

        return _wrapped

    return _decorator


if __name__ == "__main__":

    @timed_cache(3)
    def expensive():
        """Expensive function that returns response from the origin.

        See Also:
            - This function can call N number of downstream functions.
            - The response will be cached as long as the size limit isn't reached.
        """
        print("response from origin")
        return 10

    for _ in range(10):
        print(expensive())
        time.sleep(0.5)
