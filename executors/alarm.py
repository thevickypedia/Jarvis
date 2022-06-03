import os
import pathlib
import random
import subprocess
import time
from datetime import datetime, timedelta
from typing import NoReturn

from executors.logger import logger
from modules.audio import listener, speaker, volume
from modules.conditions import conversation
from modules.models import models
from modules.utils import shared, support

env = models.env
indicators = models.Indicators()


def create_alarm(hour: str, minute: str, am_pm: str, phrase: str, timer: str = None) -> NoReturn:
    """Creates the lock file necessary to set an alarm/timer.

    Args:
        hour: Hour of alarm time.
        minute: Minute of alarm time.
        am_pm: AM/PM of alarm time.
        phrase: Phrase spoken.
        timer: Number of minutes/hours to alarm.
    """
    if not os.path.isdir('alarm'):
        os.mkdir('alarm')
    pathlib.Path(f'alarm/{hour}_{minute}_{am_pm}.lock').touch()
    if 'wake' in phrase:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I will wake you up at {hour}:{minute} {am_pm}.")
    elif 'timer' in phrase and timer:
        logger.info(f"Timer set at {hour}:{minute} {am_pm}")
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I have set a timer for {timer}.")
    else:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"Alarm has been set for {hour}:{minute} {am_pm}.")


def set_alarm(phrase: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts time from it.
    """
    if 'minute' in phrase:
        if minutes := support.extract_nos(input_=phrase, method=int):
            hour, minute, am_pm = (datetime.now() + timedelta(minutes=minutes)).strftime("%I %M %p").split()
            create_alarm(hour=hour, minute=minute, am_pm=am_pm, phrase=phrase, timer=f"{minutes} minutes")
            return
    elif 'hour' in phrase:
        if hours := support.extract_nos(input_=phrase, method=int):
            hour, minute, am_pm = (datetime.now() + timedelta(hours=hours)).strftime("%I %M %p").split()
            create_alarm(hour=hour, minute=minute, am_pm=am_pm, phrase=phrase, timer=f"{hours} hours")
            return
    if extracted_time := support.extract_time(input_=phrase):
        extracted_time = extracted_time[0]
        am_pm = extracted_time.split()[-1]
        am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
        alarm_time = extracted_time.split()[0]
        if ":" in extracted_time:
            hour = int(alarm_time.split(":")[0])
            minute = int(alarm_time.split(":")[-1])
        else:
            hour = int(alarm_time.split()[0])
            minute = 0
        # makes sure hour and minutes are two digits
        hour, minute = f"{hour:02}", f"{minute:02}"
        am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
        if int(hour) <= 12 and int(minute) <= 59:
            create_alarm(phrase=phrase, hour=hour, minute=minute, am_pm=am_pm)
        else:
            speaker.speak(text=f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                               f"I don't think a time like that exists on Earth.")
    else:
        speaker.speak(text=f"Please tell me a time {env.title}!")
        if shared.called_by_offline:
            return
        speaker.speak(run=True)
        if converted := listener.listen(timeout=3, phrase_limit=4):
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            else:
                set_alarm(converted)


def kill_alarm() -> None:
    """Removes lock file to stop the alarm which rings only when the certain lock file is present."""
    alarm_state = support.lock_files(alarm_files=True)
    if not alarm_state:
        speaker.speak(text=f"You have no alarms set {env.title}!")
    elif len(alarm_state) == 1:
        hour, minute, am_pm = alarm_state[0][0:2], alarm_state[0][3:5], alarm_state[0][6:8]
        os.remove(f"alarm/{alarm_state[0]}")
        speaker.speak(text=f"Your alarm at {hour}:{minute} {am_pm} has been silenced {env.title}!")
    else:
        speaker.speak(text=f"Your alarms are at {', and '.join(alarm_state).replace('.lock', '')}. "
                           "Please let me know which alarm you want to remove.", run=True)
        if not (converted := listener.listen(timeout=3, phrase_limit=4)):
            return
        alarm_time = converted.split()[0]
        am_pm = converted.split()[-1]
        if ":" in converted:
            hour = int(alarm_time.split(":")[0])
            minute = int(alarm_time.split(":")[-1])
        else:
            hour = int(alarm_time.split()[0])
            minute = 0
        hour, minute = f"{hour:02}", f"{minute:02}"
        am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
        if os.path.exists(f'alarm/{hour}_{minute}_{am_pm}.lock'):
            os.remove(f"alarm/{hour}_{minute}_{am_pm}.lock")
            speaker.speak(text=f"Your alarm at {hour}:{minute} {am_pm} has been silenced {env.title}!")
        else:
            speaker.speak(text=f"I wasn't able to find an alarm at {hour}:{minute} {am_pm}. Try again.")


def alarm_executor() -> NoReturn:
    """Runs the ``alarm.mp3`` file at max volume and reverts the volume after 3 minutes."""
    volume.volume(level=100)
    subprocess.call(["open", indicators.alarm])
    time.sleep(200)
    volume.volume(level=env.volume)
