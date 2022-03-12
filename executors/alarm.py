import os
import random
import re
import subprocess
import time
from pathlib import Path

from modules.audio import listener, speaker, volume
from modules.conditions import conversation
from modules.models import models
from modules.utils import globals, support

env = models.env


def set_alarm(phrase: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts time from it.
    """
    phrase = phrase.lower()
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', phrase) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', phrase) or re.findall(r'([0-9]+\s?(?:am|pm:?))', phrase)
    if extracted_time:
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
            if not os.path.isdir('alarm'):
                os.mkdir('alarm')
            Path(f'alarm/{hour}_{minute}_{am_pm}.lock').touch()
            if 'wake' in phrase.strip():
                speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                                   f"I will wake you up at {hour}:{minute} {am_pm}.")
            else:
                speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                                   f"Alarm has been set for {hour}:{minute} {am_pm}.")
        else:
            speaker.speak(text=f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                               f"I don't think a time like that exists on Earth.")
    else:
        speaker.speak(text=f"Please tell me a time {env.title}!")
        if globals.called_by_offline['status']:
            return
        speaker.speak(run=True)
        converted = listener.listen(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
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
        converted = listener.listen(timeout=3, phrase_limit=4)
        if converted == 'SR_ERROR':
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


def alarm_executor() -> None:
    """Runs the ``alarm.mp3`` file at max volume and reverts the volume after 3 minutes."""
    volume.volume(level=100)
    subprocess.call(["open", "indicators/alarm.mp3"])
    time.sleep(200)
    volume.volume(level=50)
