"""Module to parse meetings information from an ICS data.

>>> ICS

"""

import datetime
from collections.abc import Generator

import dateutil.tz
from icalendar import Calendar
from icalendar.prop import vDDDTypes, vText

from jarvis.modules.logger.custom_logger import logger


class ICS:
    """Wrapper for ics events."""

    __slots__ = ['summary', 'start', 'end', 'all_day', 'duration']

    def __init__(self, **kwargs):
        """Instantiates the ICS object to load all required attributes.

        Args:
            kwargs: Takes the data as dictionary to load attributes in the object.
        """
        self.summary: str = kwargs['summary']
        self.start: datetime.datetime = kwargs['start']
        self.end: datetime.datetime = kwargs['end']
        self.all_day: bool = kwargs['all_day']
        self.duration: datetime.timedelta = kwargs['duration']


def convert_to_local_tz(ddd_object: vDDDTypes) -> datetime.datetime:
    """Converts any datetime from any timezone to local time.

    Args:
        ddd_object: Parsed Datetime, Date, Duration object.

    Returns:
        datetime.datetime:
        Local datetime object.
    """
    origin_zone = ddd_object.dt.replace(tzinfo=ddd_object.dt.tzinfo)
    destin_zone = origin_zone.astimezone(tz=dateutil.tz.gettz())
    # convert to a datetime object of desired format
    return datetime.datetime.strptime(destin_zone.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")


def all_day_event(dt_start: vDDDTypes, dt_end: vDDDTypes) -> bool:
    """Check if an event is all day by looking for timestamp in the datetime objects.

    Args:
        dt_start: Start of the event.
        dt_end: End of the event.

    Returns:
        bool:
        True if the start or end datetime objects don't have a timestamp.
    """
    if len(dt_start.dt.__str__().split()) == 1:  # doesn't have a timestamp
        return True
    try:
        _ = dt_start.dt.hour or dt_start.dt.minute or dt_start.dt.second
        _ = dt_end.dt.hour or dt_end.dt.minute or dt_end.dt.second
    except AttributeError:
        return True


def parse_calendar(calendar_data: str, lookup_date: datetime.date) -> Generator[ICS]:
    """Parsed the ICS information and yields the events' information for a specific day.

    Args:
        calendar_data: Extracted ICS data.
        lookup_date: Date to extract meetings for.

    Yields:
        ICS:
        Custom ICS object with event summary, start time, end time, duration and all day event flag.
    """
    calendar = Calendar.from_ical(calendar_data)
    for component in calendar.walk():
        if component.name == "VEVENT":
            summary: vText = component.get('summary')
            dt_start: vDDDTypes = component.get('dtstart')
            dt_end: vDDDTypes = component.get('dtend')
            if not all((summary, dt_start, dt_end)):
                logger.warning("Error while parsing, component information is missing.")
                logger.error("summary: [%s], start: [%s], end: [%s]", summary, dt_start, dt_end)
                logger.error(component)
                continue
            # create a datetime.date object since start/end can be datetime.datetime if it is not an all day event
            start = datetime.date(year=dt_start.dt.year, month=dt_start.dt.month, day=dt_start.dt.day)
            end = datetime.date(year=dt_end.dt.year, month=dt_end.dt.month, day=dt_end.dt.day)
            # event during current date or lookup date is between start and end date (repeat events)
            if start == lookup_date or start <= lookup_date <= end:
                if all_day_event(dt_start, dt_end):
                    # add a timestamp to all day events' start and end
                    _start = datetime.datetime.strptime(start.strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S")
                    _end = datetime.datetime.strptime(end.strftime("%Y-%m-%d 23:59:59"), "%Y-%m-%d %H:%M:%S")
                    yield ICS(summary=summary, start=_start, end=_end, all_day=True, duration=_end - _start)
                else:
                    # convert to local timezone
                    _start = convert_to_local_tz(ddd_object=dt_start)
                    _end = convert_to_local_tz(ddd_object=dt_end)
                    yield ICS(summary=summary, start=_start, end=_end, all_day=False, duration=_end - _start)
