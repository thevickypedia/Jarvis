from pydantic import EmailStr

from jarvis.api.models import settings


def reset_robinhood() -> None:
    """Resets robinhood token after the set time."""
    settings.robinhood.token = None


def reset_stock_monitor(email_address: EmailStr) -> None:
    """Resets stock monitor OTP after the set time.

    Args:
        email_address: Email address that should be cleared.
    """
    if settings.stock_monitor_helper.otp_sent.get(email_address):
        del settings.stock_monitor_helper.otp_sent[email_address]


def reset_surveillance() -> None:
    """Resets surveillance token after the set time."""
    settings.surveillance.token = None
