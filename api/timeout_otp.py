import time
from typing import NoReturn, Union

from api.settings import robinhood, surveillance


def reset_robinhood(after: Union[int, float]) -> NoReturn:
    """Resets robinhood token after the set time.

    Args:
        after: Number of seconds after which the token has to be invalidated.
    """
    start = time.time()
    while True:
        if start + after <= time.time():
            robinhood.token = None
            break
        if not robinhood.token:  # Already set to None
            break


def reset_surveillance(after: Union[int, float]):
    """Resets surveillance token after the set time.

    Args:
        after: Number of seconds after which the token has to be invalidated.
    """
    start = time.time()
    while True:
        if start + after <= time.time():
            surveillance.token = None
            break
        if not surveillance.token:  # Already set to None
            break
