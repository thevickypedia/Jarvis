import os
import re
from datetime import datetime
from subprocess import PIPE, Popen

from executors.custom_logger import logger

MEETING_FILE = f"{os.environ.get('meeting_app', 'calendar')}.scpt"


def meeting_file_writer() -> None:
    """Gets return value from ``meetings()`` and writes it to file named ``meetings``.

    This function runs in a dedicated thread every 30 minutes to avoid wait time when meetings information is requested.
    """
    if os.path.isfile('meetings') and int(datetime.now().timestamp()) - int(os.stat('meetings').st_mtime) < 1_800:
        os.remove('meetings')  # removes the file if it is older than 30 minutes
    data = meetings_gatherer()
    if data.startswith('You'):
        with open('meetings', 'w') as gatherer:
            gatherer.write(data)


def meeting_app_launcher() -> None:
    """Launches either Calendar or Outlook application which is required to read meetings."""
    if MEETING_FILE == 'calendar.scpt':
        os.system('open /System/Applications/Calendar.app > /dev/null 2>&1')
    elif MEETING_FILE == 'outlook.scpt':
        os.system("open /Applications/'Microsoft Outlook.app' > /dev/null 2>&1")


def meetings_gatherer() -> str:
    """Uses ``applescript`` to fetch events/meetings from local Calendar (including subscriptions) or Microsoft Outlook.

    Returns:
        str:
        - On success, returns a message saying which meeting is scheduled at what time.
        - If no events, returns a message saying there are no events in the next 12 hours.
        - On failure, returns a message saying Jarvis was unable to read calendar/outlook.
    """
    source_app = MEETING_FILE.replace('.scpt', '')
    if not os.path.isfile(MEETING_FILE):
        return f"I wasn't able to find the meetings script for your {source_app} sir!"
    failure = None
    process = Popen(['/usr/bin/osascript', MEETING_FILE] + [str(arg) for arg in [1, 3]], stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    os.system(f'git checkout -- {MEETING_FILE}')  # Undo the unspecified changes done by ScriptEditor
    if error := process.returncode:  # stores non zero error
        err_msg = err.decode('UTF-8')
        err_code = err_msg.split()[-1].strip()
        if err_code == '(-1728)':  # If the calendar named 'Office' in unavailable in the calendar application
            logger.error("Calendar, 'Office' is unavailable.")
            return "The calendar Office is unavailable sir!"
        elif err_code == '(-1712)':  # If an event takes 2+ minutes, the Apple Event Manager reports a time-out error.
            failure = f"{source_app}/event took an unusually long time to respond/complete.\nInclude, " \
                      f"'with timeout of 300 seconds' to your {MEETING_FILE} right after the " \
                      f"'tell application {source_app}' step and 'end timeout' before the 'end tell' step."
        elif err_code in ['(-10810)', '(-609)', '(-600)']:  # If unable to launch the app or app terminates.
            meeting_app_launcher()
        if not failure:
            failure = f"Unable to read {source_app} - [{error}]\n{err_msg}"
        logger.error(failure)
        failure = failure.replace('"', '')  # An identifier can’t go after this “"”
        os.system(f"""osascript -e 'display notification "{failure}" with title "Jarvis"'""")
        return f"I was unable to read your {source_app} sir! Please make sure it is in sync."

    events = out.decode().strip()
    if not events or events == ',':
        return "You don't have any meetings in the next 12 hours sir!"

    events = events.replace(', date ', ' rEpLaCInG ')
    event_time = events.split('rEpLaCInG')[1:]
    event_name = events.split('rEpLaCInG')[0].split(', ')
    event_name = [i.strip() for n, i in enumerate(event_name) if i not in event_name[n + 1:]]  # remove duplicates
    count = len(event_time)
    [event_name.remove(e) for e in event_name if len(e) <= 5] if count != len(event_name) else None
    meeting_status = f'You have {count} meetings in the next 12 hours sir! ' if count > 1 else ''
    events = {}
    for i in range(count):
        if i < len(event_name):
            event_time[i] = re.search(' at (.*)', event_time[i]).group(1).strip()
            dt_string = datetime.strptime(event_time[i], '%I:%M:%S %p')
            event_time[i] = dt_string.strftime('%I:%M %p')
            events.update({event_name[i]: event_time[i]})
    ordered_data = sorted(events.items(), key=lambda x: datetime.strptime(x[1], '%I:%M %p'))
    for index, meeting in enumerate(ordered_data):
        if count == 1:
            meeting_status += f"You have a meeting at {meeting[1]} sir! {meeting[0].upper()}. "
        else:
            meeting_status += f"{meeting[0]} at {meeting[1]}, " if index + 1 < len(ordered_data) else \
                f"{meeting[0]} at {meeting[1]}."
    return meeting_status
