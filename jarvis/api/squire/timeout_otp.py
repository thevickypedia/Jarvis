from typing import NoReturn

from pydantic import EmailStr

from jarvis.api.modals.settings import (robinhood, stock_monitor_helper,
                                        surveillance)


def reset_robinhood() -> NoReturn:
    """Resets robinhood token after the set time."""
    robinhood.token = None


def reset_stock_monitor(email_address: EmailStr) -> NoReturn:
    """Resets stock monitor OTP after the set time.

    Args:
        email_address: Email address that should be cleared.
    """
    if stock_monitor_helper.otp_sent.get(email_address):
        del stock_monitor_helper.otp_sent[email_address]


def reset_surveillance() -> NoReturn:
    """Resets surveillance token after the set time."""
    surveillance.token = None
