import os
import re
from datetime import datetime
from multiprocessing import Process
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from sqlite3 import OperationalError
from subprocess import PIPE, Popen
from typing import NoReturn

from executors.logger import logger
from modules.audio import speaker
from modules.database import database
from modules.models import models
from modules.utils import globals

env = models.env
fileio = models.fileio
EVENT_SCRIPT = f"{env.event_app}.scpt"


def events_writer() -> NoReturn:
    """Gets return value from ``events_gatherer`` function and writes it to events table in the database.

    This function runs in a dedicated process every hour to avoid wait time when events information is requested.
    """
    edb = database.Database(database=fileio.events_db, table_name=env.event_app, columns=['info'])
    event_info = events_gatherer()
    edb.cursor.execute(f"INSERT OR REPLACE INTO {env.event_app} (info) VALUES (?);", (event_info,))
    try:
        edb.connection.commit()
    except OperationalError as error:
        logger.error(error)
        os.remove(fileio.events_db)
        events_writer()


def event_app_launcher() -> NoReturn:
    """Launches either Calendar or Outlook application which is required to read events."""
    if EVENT_SCRIPT == "calendar.scpt":
        os.system("open /System/Applications/Calendar.app > /dev/null 2>&1")
    elif EVENT_SCRIPT == "outlook.scpt":
        os.system("open /Applications/'Microsoft Outlook.app' > /dev/null 2>&1")


def events_gatherer() -> str:
    """Uses ``applescript`` to fetch events from local Calendar (including subscriptions) or Microsoft Outlook.

    See Also:
        When reading from apple ``Calendar``, the calendar should be named as ``Jarvis``

    Returns:
        str:
        - On success, returns a message saying which event is scheduled at what time.
        - If no events, returns a message saying there are no events in the next 12 hours.
        - On failure, returns a message saying Jarvis was unable to read calendar/outlook.
    """
    if not env.mac:
        return f"Reading events from {env.event_app} is not possible on Windows operating system."
    if not os.path.isfile(EVENT_SCRIPT):
        return f"I wasn't able to find the events script for your {env.event_app} {env.title}!"
    event_app_launcher()
    logger.info(f"Getting calendar events from {env.event_app}")
    failure = None
    process = Popen(["/usr/bin/osascript", EVENT_SCRIPT] + [str(arg) for arg in [1, 3]], stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    os.system(f"git checkout -- {EVENT_SCRIPT}")  # Undo the unspecified changes done by ScriptEditor
    if error := process.returncode:  # stores non zero error
        err_msg = err.decode("UTF-8")
        err_code = err_msg.split()[-1].strip()
        if err_code == "(-1728)":  # If 'Jarvis' is unavailable in calendar/outlook application
            logger.warning(f"'Jarvis' is unavailable in {env.event_app}.")
            return f"Jarvis is unavailable in your {env.event_app} {env.title}!"
        elif err_code == "(-1712)":  # If an event takes 2+ minutes, the Apple Event Manager reports a time-out error.
            failure = f"{env.event_app}/event took an unusually long time to respond/complete.\nInclude, " \
                      f"'with timeout of 300 seconds' to your {EVENT_SCRIPT} right after the " \
                      f"'tell application {env.event_app}' step and 'end timeout' before the 'end tell' step."
        elif err_code in ["(-10810)", "(-609)", "(-600)"]:  # If unable to launch the app or app terminates.
            event_app_launcher()
        if not failure:
            failure = f"Unable to read {env.event_app} - [{error}]\n{err_msg}"
        logger.error(failure)
        # failure = failure.replace('"', '')  # An identifier can’t go after this “"”
        # os.system(f"""osascript -e 'display notification "{failure}" with title "Jarvis"'""")
        return f"I was unable to read your {env.event_app} {env.title}! Please make sure it is in sync."

    local_events = out.decode().strip()
    if not local_events or local_events == ",":
        logger.info("No events found!")
        return f"You don't have any events in the next 12 hours {env.title}!"

    local_events = local_events.replace(", date ", " rEpLaCInG ")
    event_time = local_events.split("rEpLaCInG")[1:]
    event_name = local_events.split("rEpLaCInG")[0].split(", ")
    event_name = [i.strip() for n, i in enumerate(event_name) if i not in event_name[n + 1:]]  # remove duplicates
    count = len(event_time)
    logger.info(f"Events: {count}")
    [event_name.remove(e) for e in event_name if len(e) <= 5] if count != len(event_name) else None
    event_status = f"You have {count} events in the next 12 hours {env.title}! " if count > 1 else ""
    local_events = {}
    for i in range(count):
        if i < len(event_name):
            event_time[i] = re.search(" at (.*)", event_time[i]).group(1).strip()
            dt_string = datetime.strptime(event_time[i], "%I:%M:%S %p")
            event_time[i] = dt_string.strftime("%I:%M %p")
            local_events.update({event_name[i]: event_time[i]})
    ordered_data = sorted(local_events.items(), key=lambda x: datetime.strptime(x[1], "%I:%M %p"))
    for index, event in enumerate(ordered_data):
        if count == 1:
            event_status += f"You have an event at {event[1]} {env.title}! {event[0].upper()}. "
        else:
            event_status += f"{event[0]} at {event[1]}, " if index + 1 < len(ordered_data) else \
                f"{event[0]} at {event[1]}."
    return event_status


def events() -> NoReturn:
    """Controller for events."""
    edb = database.Database(database=fileio.events_db, table_name=env.event_app, columns=['info'])
    if event_status := edb.cursor.execute(f"SELECT info FROM {env.event_app}").fetchone():
        speaker.speak(text=event_status[0])
    else:
        if globals.called_by_offline["status"]:
            Process(target=events_gatherer).start()
            speaker.speak(text=f"Events table is empty {env.title}. Please try again in a minute or two.")
            return False
        event = ThreadPool(processes=1).apply_async(func=events_gatherer)  # Runs parallely and awaits completion
        speaker.speak(text=f"Please give me a moment {env.title}! Let me check your {env.event_app}.", run=True)
        try:
            speaker.speak(text=event.get(timeout=60), run=True)
        except ThreadTimeoutError:
            logger.error("Unable to read the calendar within 60 seconds.")
            speaker.speak(text=f"I wasn't able to read your calendar within the set time limit {env.title}!", run=True)
