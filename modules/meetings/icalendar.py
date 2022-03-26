from multiprocessing import Process
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from typing import NoReturn

import requests
from ics import Calendar

from executors.logger import logger
from modules.audio import speaker
from modules.database import database
from modules.models import models
from modules.utils import globals

env = models.env
fileio = models.fileio
mdb = database.Database(database='meetings', table_name='Meetings', columns=['info'])


def meetings_writer() -> NoReturn:
    """Gets return value from ``meetings()`` and writes it to a file.

    This function runs in a dedicated process every hour to avoid wait time when meetings information is requested.
    """
    mdb.cursor.execute("INSERT OR REPLACE INTO Meetings (info) VALUES (?);", (meetings_gatherer(),))
    mdb.connection.commit()


def meetings_gatherer() -> str:
    """Gets ICS data and converts into a statement.

    Returns:
        str:
        - On success, returns a message saying which event is scheduled at what time.
        - If no events, returns a message saying there are no events today.
        - On failure, returns a message saying Jarvis was unable to read the calendar schedule.
    """
    if not env.ics_url:
        return f"I wasn't given a calendar URL to look up your meetings {env.title}!"
    response = requests.get(url=env.ics_url)
    if not response.ok:
        logger.error(response.status_code)
        return "I wasn't able to read your calendar schedule sir! Please check the shared URL."
    calendar = Calendar(response.text)
    events = list(calendar.timeline.today())
    if not events:
        return f"You don't have any meetings today {env.title}!"
    meeting_status = f"You have {len(events)} meetings today {env.title}! " if len(events) > 1 else ""
    for index, event in enumerate(events):
        # import dateutil.tz
        # begin_local = event.begin.replace(
        #     tzinfo=dateutil.tz.tzutc()).astimezone(dateutil.tz.tzlocal()).strftime(
        #     format='%A, %B %d, %Y %I:%M %p'
        # )
        # end_local = event.end.replace(
        #     tzinfo=dateutil.tz.tzutc()).astimezone(dateutil.tz.tzlocal()).strftime(
        #     format='%A, %B %d, %Y %I:%M %p'
        # )
        begin_local = event.begin.astimezone(tz=globals.LOCAL_TIMEZONE).strftime("%A, %B %d, %Y %H:%M")
        # end_local = event.end.astimezone(tz=globals.LOCAL_TIMEZONE).strftime("%A, %B %d, %Y %H:%M")
        if len(events) == 1:
            meeting_status += f"You have a meeting at {begin_local} {env.title}! {event.name}. "
        else:
            meeting_status += f"{event.name} at {begin_local}, " if index + 1 < len(events) else \
                f"{event.name} at {begin_local}."
    return meeting_status


def meetings() -> NoReturn:
    """Controller for meetings."""
    if meeting_status := mdb.cursor.execute("SELECT info FROM Meetings").fetchone():
        speaker.speak(text=meeting_status[0])
    else:
        if globals.called_by_offline["status"]:
            Process(target=meetings_gatherer).start()
            speaker.speak(text="Meetings table is empty. Please try again in a minute or two.")
            return False
        meeting = ThreadPool(processes=1).apply_async(func=meetings_gatherer)  # Runs parallely and awaits completion
        speaker.speak(text=f"Please give me a moment {env.title}! I'm working on it.", run=True)
        try:
            speaker.speak(text=meeting.get(timeout=60), run=True)
        except ThreadTimeoutError:
            logger.error("Unable to read the calendar schedule within 60 seconds.")
            speaker.speak(text=f"I wasn't able to read your calendar within the set time limit {env.title}!", run=True)
