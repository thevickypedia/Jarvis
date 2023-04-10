# noinspection PyUnresolvedReferences
"""Module to get meetings information from parsed ICS data.

>>> ICalendar

"""

import datetime
import sqlite3
import time
from multiprocessing import Process, Queue
from multiprocessing.context import \
    TimeoutError as ThreadTimeoutError  # noqa: PyProtectedMember
from multiprocessing.pool import ThreadPool
from typing import List, NoReturn

import requests

from jarvis.executors import word_match
from jarvis.modules.audio import speaker
from jarvis.modules.database import database
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.meetings import ics
from jarvis.modules.models import models
from jarvis.modules.retry import retry
from jarvis.modules.utils import shared, support

db = database.Database(database=models.fileio.base_db)


@retry.retry(attempts=3, interval=2, exclude_exc=sqlite3.OperationalError)
def meetings_writer(queue: Queue = None) -> NoReturn:
    """Gets return value from ``meetings()`` and writes it to a file.

    This function runs in a dedicated process every hour to avoid wait time when meetings information is requested.

    Args:
        queue: Multiprocessing queue in case mute for meetings is enabled.
    """
    info = meetings_gatherer(queue=queue)
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM ics")
        cursor.connection.commit()
        cursor.execute("INSERT OR REPLACE INTO ics (info, date) VALUES (?,?)",
                       (info, datetime.datetime.now().strftime('%Y_%m_%d'),))
        cursor.connection.commit()
    return


def meetings_gatherer(custom_date: datetime.date = None, addon: str = "today", queue: Queue = None) -> str:
    """Get ICS data, parse it and frame a statement with meeting information.

    Args:
        custom_date: Takes custom date as a datetime object.
        addon: When the custom date is.
        queue: Multiprocessing queue to put events' time during which the listener will be deactivated.

    Returns:
        str:
        - On success, returns a message saying which event is scheduled at what time.
        - If no events, returns a message saying there are no events today.
        - On failure, returns a message saying Jarvis was unable to read the calendar schedule.
    """
    if not models.env.ics_url:
        return f"I wasn't given a calendar URL to look up your meetings {models.env.title}!"
    try:
        response = requests.get(url=models.env.ics_url)
    except EgressErrors as error:
        logger.error(error)
        return f"I was unable to connect to the internet {models.env.title}! Please check your connection."
    if not response.ok:
        logger.error("[%d]: [%s]", response.status_code, response.text)
        return "I wasn't able to read your calendar schedule sir! Please check the shared URL."
    if custom_date:
        events: List[ics.ICS] = list(ics.parse_calendar(calendar_data=response.text, lookup_date=custom_date))
    else:
        now = datetime.datetime.now()
        events: List[ics.ICS] = list(ics.parse_calendar(
            calendar_data=response.text, lookup_date=datetime.date(year=now.year, month=now.month, day=now.day))
        )
    if not events:
        if "last" in addon or "yesterday" in addon:
            return f"You did not have any meetings {addon} {models.env.title}!"
        return f"You don't have any meetings {addon} {models.env.title}!"
    meeting_status, count = "", 0
    for index, event in enumerate(events):
        # Skips if meeting ended earlier than current time
        if time.mktime(event.end.timetuple()) < int(time.time()) and \
                "last" not in addon and "yesterday" not in addon:
            continue
        count += 1
        begin_local = event.start.strftime("%I:%M %p")
        event_duration = support.time_converter(second=event.duration.total_seconds())
        if queue and models.env.mute_for_meetings and not event.all_day:
            logger.debug("Adding entry to mute during meetings: %s: %s", begin_local, event_duration)
            # create a dict instead of putting the event in queue, as duplicate objects cannot be stripped
            queue.put({event.summary: [begin_local, event.duration.total_seconds()]})
        if len(events) == 1:
            if event.all_day:
                meeting_status += f"You have an all day meeting {models.env.title}! {event.summary}. "
            else:
                meeting_status += f"You have a meeting at {begin_local} for {event_duration} {models.env.title}! " \
                                  f"{event.summary}. "
        else:
            if event.all_day:
                meeting_status += f"{event.summary} - all day"
            else:
                meeting_status += f"{event.summary} at {begin_local} for {event_duration}"
            meeting_status += ', ' if index + 1 < len(events) else '.'
    if count:
        plural = "meeting" if count == 1 else "meetings"
        meeting_status = f"You have {count} {plural} {addon} {models.env.title}! {meeting_status}"
    else:
        plural = "meeting" if len(events) == 1 else "meetings"
        meeting_status = f"You have no more meetings for rest of the day {models.env.title}! " \
                         f"However, you had {len(events)} {plural} earlier {addon}. {meeting_status}"
    if "last" in addon or "yesterday" in addon:
        meeting_status = meeting_status.replace("You have", "You had")
    return meeting_status


def custom_meetings(phrase: str) -> bool:
    """Handles meeting request for a custom date.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        bool:
        A true flag if the custom meetings request matches the supported format.
    """
    if tuple_res := support.detect_lookup_date(phrase):
        datetime_obj, addon = tuple_res
        meeting_status = meetings_gatherer(
            custom_date=datetime.date(year=datetime_obj.year, month=datetime_obj.month, day=datetime_obj.day),
            addon=addon
        )
        speaker.speak(meeting_status)
        return True


def meetings(phrase: str) -> None:
    """Controller for meetings.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    if word_match.word_match(phrase=phrase, match_list=("tomorrow", "yesterday", "last", "this", "next")) and \
            custom_meetings(phrase=phrase):
        return
    with db.connection:
        cursor = db.connection.cursor()
        meeting_status = cursor.execute("SELECT info, date FROM ics").fetchone()
    if meeting_status and meeting_status[1] == datetime.datetime.now().strftime('%Y_%m_%d'):
        speaker.speak(text=meeting_status[0])
    elif meeting_status:
        logger.warning("Date in meeting status (%s) does not match the current date (%s)" %
                       (meeting_status[1], datetime.datetime.now().strftime('%Y_%m_%d')))
        logger.info("Starting adhoc process to update ics table.")
        Process(target=meetings_writer).start()
        speaker.speak(text=f"Meetings table is outdated {models.env.title}. Please try again in a minute or two.")
    else:
        if shared.called_by_offline:
            logger.info("Starting adhoc process to get meetings from ICS.")
            Process(target=meetings_writer).start()
            speaker.speak(text=f"Meetings table is empty {models.env.title}. Please try again in a minute or two.")
            return
        meeting = ThreadPool(processes=1).apply_async(func=meetings_gatherer)  # Runs parallely and awaits completion
        speaker.speak(text=f"Please give me a moment {models.env.title}! I'm working on it.", run=True)
        try:
            speaker.speak(text=meeting.get(timeout=60), run=True)
        except ThreadTimeoutError:
            logger.error("Unable to read the calendar schedule within 60 seconds.")
            speaker.speak(text=f"I wasn't able to read your calendar within the set time limit {models.env.title}!",
                          run=True)
