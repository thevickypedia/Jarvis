import os
import pathlib
import random
import subprocess
import time
from datetime import datetime, timedelta
from typing import NoReturn

from jarvis.executors.volume import volume
from jarvis.executors.word_match import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util


def create_alarm(hour: str, minute: str, am_pm: str, phrase: str, timer: str = None,
                 repeat: bool = False, day: str = None) -> NoReturn:
    """Creates the lock file necessary to set an alarm/timer.

    Args:
        hour: Hour of alarm time.
        minute: Minute of alarm time.
        am_pm: AM/PM of alarm time.
        phrase: Takes the phrase spoken as an argument.
        timer: Number of minutes/hours to alarm.
        repeat: Boolean flag if the alarm should be repeated every day.
        day: Day of week when the alarm should be repeated.
    """
    if not os.path.isdir('alarm'):
        os.mkdir('alarm')
    if repeat:
        pathlib.Path(f'alarm/{hour}_{minute}_{am_pm}_repeat.lock').touch()
    elif day:
        pathlib.Path(f'alarm/{day}_{hour}_{minute}_{am_pm}_repeat.lock').touch()
    else:
        pathlib.Path(f'alarm/{hour}_{minute}_{am_pm}.lock').touch()
    if 'wake' in phrase:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I will wake you up at {hour}:{minute} {am_pm}.")
    elif 'timer' in phrase and timer:
        logger.info(f"Timer set at {hour}:{minute} {am_pm}")
        response = [f"{random.choice(conversation.acknowledgement)}! I have set a timer for {timer}.",
                    f"{timer}! Counting down.."]
        speaker.speak(text=random.choice(response))
    else:
        if repeat:
            add = " every day."
        elif day:
            add = f" every {day}."
        elif datetime.strptime(datetime.today().strftime("%I:%M %p"), "%I:%M %p") >= \
                datetime.strptime(f"{hour}:{minute} {am_pm}", "%I:%M %p"):
            add = " tomorrow."
        else:
            add = "."
        response = [f"Alarm has been set for {hour}:{minute} {am_pm}{add}",
                    f"Your alarm is set for {hour}:{minute} {am_pm}{add}"]
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! {random.choice(response)}")


def set_alarm(phrase: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if models.settings.limited:
        speaker.speak(text="Alarm features are currently unavailable, as you're running on restricted mode.")
        return
    if 'minute' in phrase:
        if minutes := util.extract_nos(input_=phrase, method=int):
            hour, minute, am_pm = (datetime.now() + timedelta(minutes=minutes)).strftime("%I %M %p").split()
            create_alarm(hour=hour, minute=minute, am_pm=am_pm, phrase=phrase, timer=f"{minutes} minutes")
            return
    elif 'hour' in phrase:
        if hours := util.extract_nos(input_=phrase, method=int):
            hour, minute, am_pm = (datetime.now() + timedelta(hours=hours)).strftime("%I %M %p").split()
            create_alarm(hour=hour, minute=minute, am_pm=am_pm, phrase=phrase, timer=f"{hours} hours")
            return
    if extracted_time := util.extract_time(input_=phrase):
        extracted_time = extracted_time[0]
        alarm_time = extracted_time.split()[0]
        if ":" in extracted_time:
            hour = int(alarm_time.split(":")[0])
            minute = int(alarm_time.split(":")[-1])
        else:
            hour = int(alarm_time.split()[0])
            minute = 0
        # makes sure hour and minutes are two digits
        hour, minute = f"{hour:02}", f"{minute:02}"
        am_pm = "AM" if "A" in extracted_time.split()[-1].upper() else "PM"
        if int(hour) <= 12 and int(minute) <= 59:
            if day := word_match(phrase=phrase, match_list=['sunday', 'monday', 'tuesday', 'wednesday',
                                                            'thursday', 'friday', 'saturday']):
                day = day[0].upper() + day[1:].lower()
                create_alarm(phrase=phrase, hour=hour, minute=minute, am_pm=am_pm, day=day)
            elif word_match(phrase=phrase, match_list=['everyday', 'every day', 'daily']):
                create_alarm(phrase=phrase, hour=hour, minute=minute, am_pm=am_pm, repeat=True)
            else:
                create_alarm(phrase=phrase, hour=hour, minute=minute, am_pm=am_pm)
        else:
            speaker.speak(text=f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                               f"I don't think a time like that exists on Earth.")
    else:
        speaker.speak(text=f"Please tell me a time {models.env.title}!")
        if shared.called_by_offline:
            return
        speaker.speak(run=True)
        if converted := listener.listen():
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            else:
                set_alarm(converted)


def kill_alarm(phrase: str) -> None:
    """Removes lock file to stop the alarm which rings only when the certain lock file is present.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    word = 'timer' if 'timer' in phrase else 'alarm'
    alarm_state = support.lock_files(alarm_files=True)
    if not alarm_state:
        speaker.speak(text=f"You have no {word}s set {models.env.title}!")
    elif len(alarm_state) == 1:
        hour, minute, am_pm = alarm_state[0][:2], alarm_state[0][3:5], alarm_state[0][6:8]
        os.remove(f"alarm/{alarm_state[0]}")
        speaker.speak(text=f"Your {word} at {hour}:{minute} {am_pm} has been silenced {models.env.title}!")
    else:
        speaker.speak(text=f"Your {word}s are at {', and '.join(alarm_state).replace('.lock', '')}. "
                           f"Please let me know which {word} you want to remove.", run=True)
        if not (converted := listener.listen()):
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
            speaker.speak(text=f"Your {word} at {hour}:{minute} {am_pm} has been silenced {models.env.title}!")
        else:
            speaker.speak(text=f"I wasn't able to find your {word} at {hour}:{minute} {am_pm}. Try again.")


def alarm_executor() -> NoReturn:
    """Runs the ``alarm.mp3`` file at max volume and reverts the volume after 3 minutes."""
    volume(level=100)
    if models.settings.os != "Windows":
        subprocess.call(["open", models.indicators.alarm])
    else:
        os.system(f'start wmplayer {models.indicators.alarm}')
    time.sleep(200)
    volume(level=models.env.volume)
