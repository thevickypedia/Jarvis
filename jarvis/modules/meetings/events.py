# noinspection PyUnresolvedReferences
"""Module to gather events from the chosen macOS application.

>>> Events

"""

import os
import re
import sqlite3
import subprocess
from datetime import datetime
from multiprocessing import Process
from multiprocessing.context import \
    TimeoutError as ThreadTimeoutError  # noqa: PyProtectedMember
from multiprocessing.pool import ThreadPool
from typing import NoReturn

import pynotification

from jarvis.modules.audio import speaker
from jarvis.modules.database import database
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.retry import retry
from jarvis.modules.utils import shared, util

db = database.Database(database=models.fileio.base_db)


@retry.retry(attempts=3, interval=2, exclude_exc=sqlite3.OperationalError)
def events_writer() -> NoReturn:
    """Gets return value from ``events_gatherer`` function and writes it to events table in the database.

    This function runs in a dedicated process to avoid wait time when events information is requested.
    """
    info = events_gatherer()
    query = f"INSERT or REPLACE INTO {models.env.event_app} (info, date) VALUES " \
            f"{(info, datetime.now().strftime('%Y_%m_%d'))}"
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute(f"DELETE FROM {models.env.event_app}")  # Use f-string or %s as table names can't be parametrized
        cursor.connection.commit()
        cursor.execute(query)
        cursor.connection.commit()
    return


def event_app_launcher() -> NoReturn:
    """Launches either Calendar or Outlook application which is required to read events."""
    if models.env.event_app == "calendar":
        os.system(f"osascript {models.fileio.app_launcher} Calendar")
    else:
        # Just `Outlook` works too but requires manual click to map the shortcut for the first time
        os.system(f"osascript {models.fileio.app_launcher} 'Microsoft Outlook.app'")


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
    if models.settings.os != models.supported_platforms.macOS:
        return f"Reading events from {models.env.event_app} is currently possible only on macOS, " \
               f"but the host machine is currently running {models.settings.os}."
    failure = None
    process = subprocess.Popen(["/usr/bin/osascript", models.fileio.event_script] + [str(arg) for arg in [1, 3]],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    # Undo unspecified changes done by ScriptEditor (should only be necessary when package is not pip installed)
    os.system(f"git checkout HEAD -- {models.fileio.event_script} >/dev/null 2>&1")
    # noinspection GrazieInspection
    if error := process.returncode:  # stores non zero error
        err_msg = err.decode("UTF-8")
        err_code = err_msg.split()[-1].strip()
        if err_code == "(-1728)":  # If 'Jarvis' is unavailable in calendar/outlook application
            logger.warning("'Jarvis' is unavailable in %s.", models.env.event_app)
            return f"Jarvis is unavailable in your {models.env.event_app} {models.env.title}!"
        elif err_code == "(-1712)":  # If an event takes 2+ minutes, the Apple Event Manager reports a time-out error.
            failure = f"{models.env.event_app}/event took an unusually long time to respond/complete.\nInclude, " \
                      f"'with timeout of 300 seconds' to your {models.fileio.event_script} right after the " \
                      f"'tell application {models.env.event_app}' step and 'end timeout' before the 'end tell' step."
        elif err_code in ["(-10810)", "(-609)", "(-600)"]:  # If unable to launch the app or app terminates.
            event_app_launcher()
        if not failure:
            failure = f"[{models.env.event_app}:{error}] - {err_msg}"
        failure = failure.replace('"', '')  # An identifier can’t go after this “"”
        logger.error(failure)
        pynotification.pynotifier(title="Jarvis", message=failure)
        return f"I was unable to read your {models.env.event_app} {models.env.title}! Please make sure it is in sync."

    local_events = out.decode().strip()
    if not local_events or local_events == ",":
        return f"You don't have any events in the next 12 hours {models.env.title}!"

    local_events = local_events.replace(", date ", " rEpLaCInG ")
    event_time = local_events.split("rEpLaCInG")[1:]
    event_name = local_events.split("rEpLaCInG")[0].split(", ")
    event_name = util.remove_duplicates(input_=event_name)
    count = len(event_time)
    [event_name.remove(e) for e in event_name if len(e) <= 5] if count != len(event_name) else None
    event_status = f"You have {count} events in the next 12 hours {models.env.title}! " if count > 1 else ""
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
            event_status += f"You have an event at {event[1]} {models.env.title}! {event[0].upper()}. "
        else:
            event_status += f"{event[0]} at {event[1]}, " if index + 1 < len(ordered_data) else \
                f"{event[0]} at {event[1]}."
    return event_status


def events(*args) -> None:
    """Controller for events."""
    with db.connection:
        cursor = db.connection.cursor()
        # Use f-string or %s as table names cannot be parametrized
        event_status = cursor.execute(f"SELECT info, date FROM {models.env.event_app}").fetchone()
    if event_status and event_status[1] == datetime.now().strftime('%Y_%m_%d'):
        speaker.speak(text=event_status[0])
    elif event_status:
        logger.warning("Date in event status (%s) does not match the current date (%s)",
                       event_status[1], datetime.now().strftime('%Y_%m_%d'))
        logger.info("Starting adhoc process to update %s table.", models.env.event_app)
        Process(target=events_writer).start()
        speaker.speak(text=f"Events table is outdated {models.env.title}. Please try again in a minute or two.")
    else:
        if shared.called_by_offline:
            logger.info("Starting adhoc process to get events from %s.", models.env.event_app)
            Process(target=events_writer).start()
            speaker.speak(text=f"Events table is empty {models.env.title}. Please try again in a minute or two.")
            return
        event = ThreadPool(processes=1).apply_async(func=events_gatherer)  # Runs parallely and awaits completion
        speaker.speak(text=f"Please give me a moment {models.env.title}! Let me check your {models.env.event_app}.",
                      run=True)
        try:
            speaker.speak(text=event.get(timeout=60), run=True)
        except ThreadTimeoutError:
            logger.error("Unable to read the calendar within 60 seconds.")
            speaker.speak(text=f"I wasn't able to read your calendar within the set time limit {models.env.title}!",
                          run=True)
