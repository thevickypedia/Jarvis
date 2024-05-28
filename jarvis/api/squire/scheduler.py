import os
import shutil
from typing import Dict

from jarvis.api import triggers
from jarvis.modules.crontab import expression
from jarvis.modules.utils import util


def market_hours(extended: bool = False) -> Dict[str, Dict[str, int]]:
    """Returns the market hours for each timezone in the US.

    Args:
        extended: Boolean flag to use extended hours.

    Returns:
        Dict[str, Dict[str, int]]:
        Returns a dictionary of timezone and the market open and close hours.
    """
    if extended:
        return {
            "EDT": {"OPEN": 7, "CLOSE": 18},
            "EST": {"OPEN": 7, "CLOSE": 18},
            "CDT": {"OPEN": 6, "CLOSE": 17},
            "CST": {"OPEN": 6, "CLOSE": 17},
            "MDT": {"OPEN": 5, "CLOSE": 16},
            "MST": {"OPEN": 5, "CLOSE": 16},
            "PDT": {"OPEN": 4, "CLOSE": 15},
            "PST": {"OPEN": 4, "CLOSE": 15},
            "OTHER": {"OPEN": 5, "CLOSE": 21},  # 5 AM to 9 PM
        }
    return {
        "EDT": {"OPEN": 9, "CLOSE": 16},
        "EST": {"OPEN": 9, "CLOSE": 16},
        "CDT": {"OPEN": 8, "CLOSE": 15},
        "CST": {"OPEN": 8, "CLOSE": 15},
        "MDT": {"OPEN": 7, "CLOSE": 14},
        "MST": {"OPEN": 7, "CLOSE": 14},
        "PDT": {"OPEN": 6, "CLOSE": 13},
        "PST": {"OPEN": 6, "CLOSE": 13},
        "OTHER": {"OPEN": 7, "CLOSE": 19},  # 7 AM to 7 PM
    }


def rh_cron_schedule(extended: bool = False) -> expression.CronExpression:
    """Creates a cron expression for ``stock_report.py``. Determines cron schedule based on current timezone.

    Args:
        extended: Boolean flag to use extended hours.

    See Also:
        - extended: 1 before and after market hours.
        - default(regular): Regular market hours.

    Returns:
        CronExpression:
        Crontab expression object running every 30 minutes during market hours based on the current timezone.
    """
    hours = market_hours(extended)
    job = f"{shutil.which(cmd='python')} {os.path.join(triggers.__path__[0], 'stock_report.py')}"
    tz = util.get_timezone()
    if tz not in hours:
        tz = "OTHER"
    return expression.CronExpression(
        f"*/30 {hours[tz]['OPEN']}-{hours[tz]['CLOSE']} * * 1-5 {job}"
    )


def sm_cron_schedule(include_weekends: bool = False) -> expression.CronExpression:
    """Creates a cron expression for ``stock_monitor.py``.

    Args:
        include_weekends: Takes a boolean flag to run cron schedule over the weekends.

    Returns:
        CronExpression:
        Crontab expression object running every 15 minutes.
    """
    job = f"{shutil.which(cmd='python')} {os.path.join(triggers.__path__[0], 'stock_monitor.py')}"
    if include_weekends:
        return expression.CronExpression(f"*/15 * * * * {job}")
    return expression.CronExpression(f"*/15 * * * 1-5 {job}")
