import time
from typing import NoReturn, Union

from pydantic import EmailStr

from jarvis.api.modals.settings import (robinhood, stock_monitor_helper,
                                        surveillance)


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
        time.sleep(1)


def reset_stock_monitor(email_address: EmailStr, after: Union[int, float]) -> NoReturn:
    """Resets stock monitor OTP after the set time.

    Args:
        email_address: Email address that should be cleared.
        after: Number of seconds after which the token has to be invalidated.
    """
    start = time.time()
    while True:
        if start + after <= time.time():
            del stock_monitor_helper.otp_sent[email_address]
            break
        if not stock_monitor_helper.otp_sent[email_address]:  # Already set to None
            break
        time.sleep(1)


def reset_surveillance(after: Union[int, float]) -> NoReturn:
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
        time.sleep(1)
