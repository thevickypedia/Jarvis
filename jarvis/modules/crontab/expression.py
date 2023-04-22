# noinspection PyUnresolvedReferences
"""Module to handle crontab expressions.

>>> Expression

"""

import calendar
import datetime
from typing import Tuple, Union

from jarvis.modules.exceptions import InvalidArgument


class CronExpression:
    """Initiates CronExpression object to validate a crontab entry.

    >>> CronExpression

    """

    DAY_NAMES = zip(('sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'), range(7))
    MINUTES = (0, 59)
    HOURS = (0, 23)
    DAYS_OF_MONTH = (1, 31)
    MONTHS = (1, 12)
    DAYS_OF_WEEK = (0, 6)
    L_FIELDS = (DAYS_OF_WEEK, DAYS_OF_MONTH)
    FIELD_RANGES = (MINUTES, HOURS, DAYS_OF_MONTH, MONTHS, DAYS_OF_WEEK)
    MONTH_NAMES = zip(('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec'), range(1, 13))
    DEFAULT_EPOCH = (1970, 1, 1, 0, 0, 0)
    SUBSTITUTIONS = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *"
    }

    def __init__(self, line: str, epoch: tuple = DEFAULT_EPOCH, epoch_utc_offset: int = 0):
        """Instantiates a CronExpression object with an optionally defined epoch.

        Raises:
            InvalidArgument:
            If the given number of fields is invalid.

        Notes:
            If the epoch is defined, the UTC offset can be specified one of two ways:
                - As the sixth element in 'epoch' or supplied in epoch_utc_offset.
                - The epoch should be defined down to the minute sorted by descending significance.
        """
        self.numerical_tab = []
        for key, value in self.SUBSTITUTIONS.items():
            if line.startswith(key):
                line = line.replace(key, value)
                break

        fields = line.split(None, 5)
        if len(fields) == 5:
            fields.append('')

        if len(fields) < 6:
            raise InvalidArgument(f"{line!r} has invalid cron expression!")

        minutes, hours, dom, months, dow, self.comment = fields
        self.expression = ' '.join(fields[:5])

        dow = dow.replace('7', '0').replace('?', '*')
        dom = dom.replace('?', '*')

        for monthstr, monthnum in self.MONTH_NAMES:
            months = months.lower().replace(monthstr, str(monthnum))

        for dowstr, downum in self.DAY_NAMES:
            dow = dow.lower().replace(dowstr, str(downum))

        self.string_tab = [minutes, hours, dom.upper(), months, dow.upper()]
        try:
            self.compute_numtab()
        except TypeError:
            raise InvalidArgument(f"{line!r} has invalid cron expression!")
        if len(epoch) == 5:
            y, mo, d, h, m = epoch
            self.epoch = (y, mo, d, h, m, epoch_utc_offset)
        else:
            self.epoch = epoch

    def __str__(self):
        """Built-in override."""
        base = self.__class__.__name__ + "(%s)"
        cron_line = self.string_tab + [str(self.comment)]
        if not self.comment:
            cron_line.pop()
        arguments = '"' + ' '.join(cron_line) + '"'
        if self.epoch != self.DEFAULT_EPOCH:
            return base % (arguments + ", epoch=" + repr(self.epoch))
        else:
            return base % arguments

    def __repr__(self):
        """Built-in override."""
        return str(self)

    def compute_numtab(self):
        """Recomputes the sets for the static ranges of the trigger time.

        Notes:
            This method should only be called by the user if the string_tab member is modified.
        """
        self.numerical_tab = []

        for field_str, span in zip(self.string_tab, self.FIELD_RANGES):
            split_field_str = field_str.split(',')
            if len(split_field_str) > 1 and "*" in split_field_str:
                raise InvalidArgument("\"*\" must be alone in a field.")

            unified = set()
            for cron_atom in split_field_str:
                # parse_atom only handles static cases
                for special_char in ('%', '#', 'L', 'W'):
                    if special_char in cron_atom:
                        break
                else:
                    unified.update(parse_atom(cron_atom, span))

            self.numerical_tab.append(unified)

        if self.string_tab[2] == "*" and self.string_tab[4] != "*":
            self.numerical_tab[2] = set()

    def check_trigger(self, date_tuple: Union[Tuple[int, int, int, int, int], Tuple[int, ...]] = None,
                      utc_offset: int = 0) -> bool:
        """Returns boolean indicating if the trigger is active at the given time.

        Args:
            date_tuple: Tuple of year, month, date, hour and minute. Defaults to current.
            utc_offset: UTC offset.

        See Also:
            - | The date tuple should be in the local time. Unless periodicities are used, utc_offset does not need to
              | be specified. If periodicity is used, specifically in the hour and minutes fields, it is crucial that
              | the utc_offset is specified.

        Returns:
            bool:
            A boolean flag to indicate whether the given datetime matches the crontab entry.
        """
        if date_tuple:
            year, month, day, hour, mins = date_tuple
        else:
            year, month, day, hour, mins = tuple(map(int, datetime.datetime.now().strftime("%Y %m %d %H %M").split()))
        given_date = datetime.date(year, month, day)
        zeroday = datetime.date(*self.epoch[:3])
        last_dom = calendar.monthrange(year, month)[-1]
        dom_matched = True

        # In calendar and datetime.date.weekday, Monday = 0
        given_dow = (datetime.date.weekday(given_date) + 1) % 7
        first_dow = (given_dow + 1 - day) % 7

        # Figure out how much time has passed from the epoch to the given date
        utc_diff = utc_offset - self.epoch[5]
        mod_delta_yrs = year - self.epoch[0]
        mod_delta_mon = month - self.epoch[1] + mod_delta_yrs * 12
        mod_delta_day = (given_date - zeroday).days
        mod_delta_hrs = hour - self.epoch[3] + mod_delta_day * 24 + utc_diff
        mod_delta_min = mins - self.epoch[4] + mod_delta_hrs * 60

        # Makes iterating through like components easier.
        quintuple = zip((mins, hour, day, month, given_dow), self.numerical_tab, self.string_tab,
                        (mod_delta_min, mod_delta_hrs, mod_delta_day, mod_delta_mon, mod_delta_day),
                        self.FIELD_RANGES)

        for value, valid_values, field_str, delta_t, field_type in quintuple:
            # All valid, static values for the fields are stored in sets
            if value in valid_values:
                continue

            # The following for loop implements the logic for context
            # sensitive and epoch sensitive constraints. break statements,
            # which are executed when a match is found, lead to a continue
            # in the outer loop. If there are no matches found, the given date
            # does not match expression constraints, so the function returns
            # False as seen at the end of this for...else... construct.
            for cron_atom in field_str.split(','):
                if cron_atom[0] == '%':
                    if not (delta_t % int(cron_atom[1:])):
                        break

                elif field_type == self.DAYS_OF_WEEK and '#' in cron_atom:
                    d, n = int(cron_atom[0]), int(cron_atom[2])
                    # Computes Nth occurence of D day of the week
                    if (((d - first_dow) % 7) + 1 + 7 * (n - 1)) == day:
                        break

                elif field_type == self.DAYS_OF_MONTH and cron_atom[-1] == 'W':
                    target = min(int(cron_atom[:-1]), last_dom)
                    lands_on = (first_dow + target - 1) % 7
                    if lands_on == 0:
                        # Shift from Sun. to Mon. unless Mon. is next month
                        target += 1 if target < last_dom else -2
                    elif lands_on == 6:
                        # Shift from Sat. to Fri. unless Fri. in prior month
                        target += -1 if target > 1 else 2

                    # Break if the day is correct, and target is a weekday
                    if target == day and (first_dow + target - 7) % 7 > 1:
                        break

                elif field_type in self.L_FIELDS and cron_atom.endswith('L'):
                    # In dom field, L means the last day of the month
                    target = last_dom

                    if field_type == self.DAYS_OF_WEEK:
                        # Calculates the last occurence of given day of week
                        desired_dow = int(cron_atom[:-1])
                        target = (((desired_dow - first_dow) % 7) + 29)
                        target -= 7 if target > last_dom else 0

                    if target == day:
                        break
            else:
                # See 2010.11.15 of CHANGELOG
                if field_type == self.DAYS_OF_MONTH and self.string_tab[4] != '*':
                    dom_matched = False
                    continue
                elif field_type == self.DAYS_OF_WEEK and self.string_tab[2] != '*':
                    # If we got here, then days of months validated so it does
                    # not matter that days of the week failed.
                    return dom_matched

                # None of the expressions matched which means this field fails
                return False

        # Arriving at this point means the date landed within the constraints
        # of all fields; the associated trigger should be fired.
        return True


def parse_atom(parse: str, minmax: tuple) -> set:
    """Returns a set containing valid values for a given cron-style range of numbers.

    Args:
        parse: Element to be parsed.
        minmax: Two element iterable containing the inclusive upper and lower limits of the expression

    Raises:
        InvalidArgument:
        If the cron expression is invalid.

    Examples:
        >>> parse_atom("1-5",(0,6))
        set([1, 2, 3, 4, 5])

        >>> parse_atom("*/6",(0,23))
        set([0, 6, 12, 18])

        >>> parse_atom("18-6/4",(0,23))
        set([18, 22, 0, 4])

        >>> parse_atom("*/9",(0,23))
        set([0, 9, 18])
    """
    parse = parse.strip()
    increment = 1
    if parse == '*':
        return set(range(minmax[0], minmax[1] + 1))
    elif parse.isdigit():
        # A single number still needs to be returned as a set
        value = int(parse)
        if minmax[0] <= value <= minmax[1]:
            return {value}
        else:
            raise InvalidArgument(f"invalid bounds: {parse}")
    elif '-' in parse or '/' in parse:
        divide = parse.split('/')
        subrange = divide[0]
        if len(divide) == 2:
            # Example: 1-3/5 or */7 increment should be 5 and 7 respectively
            increment = int(divide[1])

        if '-' in subrange:
            # Example: a-b
            prefix, suffix = [int(n) for n in subrange.split('-')]
            if prefix < minmax[0] or suffix > minmax[1]:
                raise InvalidArgument(f"invalid bounds: {parse}")
        elif subrange == '*':
            # Include all values with the given range
            prefix, suffix = minmax
        else:
            raise InvalidArgument(f"unrecognized symbol: {subrange}")

        if prefix < suffix:
            # Example: 7-10
            return set(range(prefix, suffix + 1, increment))
        else:
            # Example: 12-4/2; (12, 12 + n, ..., 12 + m*n) U (n_0, ..., 4)
            noskips = list(range(prefix, minmax[1] + 1))
            noskips += list(range(minmax[0], suffix + 1))
            return set(noskips[::increment])


if __name__ == '__main__':
    job = CronExpression("0 0 * * 1-5/2 find /var/log -delete")
    print(job.comment)
    print(job.expression)

    print(job.check_trigger(tuple(map(int, datetime.datetime.now().strftime("%Y,%m,%d,%H,%M").split(",")))))

    print(job.check_trigger((2022, 7, 27, 0, 0)))
    print(job.check_trigger((2022, 7, 26, 0, 0)))
