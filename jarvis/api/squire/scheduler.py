import os
import shutil

from jarvis.api import triggers
from jarvis.modules.crontab.expression import CronExpression
from jarvis.modules.utils import util


class MarketHours:
    """Initiates MarketHours object to store the market hours for each timezone in USA.

    >>> MarketHours

    See Also:
        Class member ``hours`` contains key-value pairs for both ``EXTENDED`` and ``REGULAR`` market hours.
    """

    hours = {
        'EXTENDED': {
            'EDT': {'OPEN': 7, 'CLOSE': 18}, 'EST': {'OPEN': 7, 'CLOSE': 18},
            'CDT': {'OPEN': 6, 'CLOSE': 17}, 'CST': {'OPEN': 6, 'CLOSE': 17},
            'MDT': {'OPEN': 5, 'CLOSE': 16}, 'MST': {'OPEN': 5, 'CLOSE': 16},
            'PDT': {'OPEN': 4, 'CLOSE': 15}, 'PST': {'OPEN': 4, 'CLOSE': 15},
            'OTHER': {'OPEN': 5, 'CLOSE': 21}  # 5 AM to 9 PM
        },
        'REGULAR': {
            'EDT': {'OPEN': 9, 'CLOSE': 16}, 'EST': {'OPEN': 9, 'CLOSE': 16},
            'CDT': {'OPEN': 8, 'CLOSE': 15}, 'CST': {'OPEN': 8, 'CLOSE': 15},
            'MDT': {'OPEN': 7, 'CLOSE': 14}, 'MST': {'OPEN': 7, 'CLOSE': 14},
            'PDT': {'OPEN': 6, 'CLOSE': 13}, 'PST': {'OPEN': 6, 'CLOSE': 13},
            'OTHER': {'OPEN': 7, 'CLOSE': 19}  # 7 AM to 7 PM
        }
    }


def rh_cron_schedule(extended: bool = False) -> CronExpression:
    """Creates a cron expression for ``stock_report.py``. Determines cron schedule based on current timezone.

    Args:
        extended: Uses extended hours.

    See Also:
        - extended: 1 before and after market hours.
        - default(regular): Regular market hours.

    Returns:
        CronExpression:
        Crontab expression object running every 30 minutes during market hours based on the current timezone.
    """
    job = f"cd {os.getcwd()} && {shutil.which(cmd='python')} {os.path.join(triggers.__path__[0], 'stock_report.py')}"
    tz = util.get_timezone()
    if tz not in MarketHours.hours['REGULAR'] or tz not in MarketHours.hours['EXTENDED']:
        tz = 'OTHER'
    start = MarketHours.hours['EXTENDED'][tz]['OPEN'] if extended else MarketHours.hours['REGULAR'][tz]['OPEN']
    end = MarketHours.hours['EXTENDED'][tz]['CLOSE'] if extended else MarketHours.hours['REGULAR'][tz]['CLOSE']
    return CronExpression(f"*/30 {start}-{end} * * 1-5 {job}")


def sm_cron_schedule(include_weekends: bool = True) -> CronExpression:
    """Creates a cron expression for ``stock_monitor.py``.

    Args:
        include_weekends: Takes a boolean flag to run cron schedule over the weekends.

    Returns:
        CronExpression:
        Crontab expression object running every 15 minutes.
    """
    job = f"cd {os.getcwd()} && {shutil.which(cmd='python')} {os.path.join(triggers.__path__[0], 'stock_monitor.py')}"
    if include_weekends:
        return CronExpression(f"*/15 * * * * {job}")
    return CronExpression(f"*/15 * * * 1-5 {job}")
