import os
from datetime import datetime

from api.rh_helper import MarketHours

COMMAND = f"cd {os.getcwd()} && source venv/bin/activate && python api/report_gatherer.py && deactivate"


def expression(extended: bool = False) -> str:
    """Determines the start and end time based on the current timezone.

    Args:
        extended: Uses extended hours.

    See Also:
        - extended: 1 before and after market hours.
        - default(regular): Regular market hours.
    """
    tz = datetime.utcnow().astimezone().tzname()
    start = MarketHours.hours['EXTENDED'][tz]['OPEN'] if extended else MarketHours.hours['REGULAR'][tz]['OPEN']
    end = MarketHours.hours['EXTENDED'][tz]['CLOSE'] if extended else MarketHours.hours['REGULAR'][tz]['CLOSE']
    return f"*/30 {start}-{end} * * 1-5 {COMMAND}"
