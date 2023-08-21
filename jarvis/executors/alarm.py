import os
import random
import string
import subprocess
import time
from datetime import datetime, timedelta
from typing import List, NoReturn

import pyvolume

from jarvis.executors import files, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util


def create_alarm(alarm_time: datetime, phrase: str, timer: str = None,
                 repeat: bool = False, day: str = None) -> NoReturn:
    """Creates the lock file necessary to set an alarm/timer.

    Args:
        alarm_time: Time of alarm as a datetime object.
        phrase: Takes the phrase spoken as an argument.
        timer: Number of minutes/hours to alarm.
        repeat: Boolean flag if the alarm should be repeated every day.
        day: Day of week when the alarm should be repeated.
    """
    existing_alarms = files.get_alarms()
    formatted = dict(
        alarm_time=alarm_time.strftime("%I:%M %p"),
        day=day,
        repeat=repeat,
    )
    if not day:
        formatted.pop('day')
    if formatted in existing_alarms:
        speaker.speak(text=f"You have a duplicate alarm {models.env.title}!")
        return
    existing_alarms.append(formatted)
    files.put_alarms(data=existing_alarms)
    logger.info("Alarm/timer set at {%s}", alarm_time.strftime("%I:%M %p"))
    if 'wake' in phrase:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I will wake you up at {alarm_time.strftime('%I:%M %p')}.")
    elif 'timer' in phrase and timer:
        response = [
            f"{random.choice(conversation.acknowledgement)}! I have set a timer for {timer}.",
            f"{timer}! Counting down.."
        ]
        speaker.speak(text=random.choice(response))
    else:
        if day:  # If day is set, then it's obviously a repeat with a 'day' filter
            add = f"every {day}."
        elif repeat:  # If no day is set, then it's a repeat everyday
            add = "every day."
        elif alarm_time.date() > datetime.today().date():
            add = "tomorrow."
        else:
            add = "."
        response = [
            f"Alarm has been set for {alarm_time.strftime('%I:%M %p')} {add}",
            f"Your alarm is set for {alarm_time.strftime('%I:%M %p')} {add}"
        ]
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! {random.choice(response)}")


def set_alarm(phrase: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if models.settings.limited:
        speaker.speak(text="Alarm features are currently unavailable, as you're running on restricted mode.")
        return
    phrase = phrase.lower()
    if 'minute' in phrase:
        if minutes := util.extract_nos(input_=phrase, method=int):
            create_alarm(
                alarm_time=datetime.now() + timedelta(minutes=minutes), phrase=phrase,
                timer=f"{minutes} {support.ENGINE.plural(text='minute', count=minutes)}"
            )
            return
    elif 'hour' in phrase:
        if hours := util.extract_nos(input_=phrase, method=int):
            create_alarm(
                alarm_time=datetime.now() + timedelta(hours=hours), phrase=phrase,
                timer=f"{hours} {support.ENGINE.plural(text='hour', count=hours)}"
            )
            return
    if extracted_time := util.extract_time(input_=phrase) or word_match.word_match(
            phrase=phrase, match_list=('noon', 'midnight', 'mid night')
    ):
        if 'noon' in phrase:
            extracted_time = ["12:00 PM"]
        elif 'night' in phrase:
            extracted_time = ["12:00 AM"]
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
            datetime_obj = datetime.strptime(f"{hour}:{minute} {am_pm}", "%I:%M %p")
            # todo: alarm at 5 AM every day has been set already and user is trying to set a new 5 AM alarm for Friday
            # todo: match existing alarms and duplicate it in the create_alarm function
            if day := word_match.word_match(phrase=phrase, match_list=('sunday', 'monday', 'tuesday', 'wednesday',
                                                                       'thursday', 'friday', 'saturday')):
                create_alarm(phrase=phrase, alarm_time=datetime_obj, day=string.capwords(day), repeat=True)
            elif word_match.word_match(phrase=phrase, match_list=('everyday', 'every day', 'daily')):
                create_alarm(phrase=phrase, alarm_time=datetime_obj, repeat=True)
            else:
                create_alarm(phrase=phrase, alarm_time=datetime_obj)
        else:
            speaker.speak(text=f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                               "I don't think a time like that exists on Earth.")
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


def get_alarm_state() -> List[str]:
    """Frames a response text with all the alarms present.

    Returns:
        List[str]:
        Returns a list of alarms framed as a response.
    """
    # todo: extract response for a particular time here instead of using .startswith()
    response = []
    for _alarm in files.get_alarms():
        if _alarm['repeat']:
            response.append(f"{_alarm['alarm_time']} on every {_alarm.get('day', 'day')}")
        else:
            response.append(_alarm['alarm_time'])
    return response


def kill_alarm(phrase: str) -> None:
    """Removes lock file to stop the alarm which rings only when the certain lock file is present.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    word = 'timer' if 'timer' in phrase else 'alarm'
    alarms = files.get_alarms()
    if not alarms:
        speaker.speak(text=f"You have no {word}s set {models.env.title}!")
        return
    if len(alarms) == 1:
        _alarm = alarms[0]
        response = f"Your {word} at {_alarm['alarm_time']} "
        if _alarm['repeat']:
            response += f"on every {_alarm.get('day', 'day')} "
        response += f"has been silenced {models.env.title}!"
        speaker.speak(text=response)
        return
    if "all" in phrase.split():
        alarms.clear()
        files.put_alarms(data=alarms)
        speaker.speak(text=f"I have silenced {len(alarms)} of your alarms {models.env.title}!")
        return
    if extracted_time := util.extract_time(input_=phrase) or word_match.word_match(
            phrase=phrase, match_list=('noon', 'midnight', 'mid night')
    ):
        if 'noon' in phrase:
            extracted_time = ["12:00 PM"]
        elif 'night' in phrase:
            extracted_time = ["12:00 AM"]
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
            chosen_alarm = f"{hour}:{minute} {am_pm}"
            if chosen_alarm in [_alarm['alarm_time'] for _alarm in alarms]:
                # construct response before updating the base file
                alarm_states = [_alarm for _alarm in get_alarm_state() if _alarm.startswith(chosen_alarm)]
                # todo: there might different alarms set at the same time (eg: 5 AM on Monday and Friday)
                # if len(alarm_states) > 1:
                #     speaker.speak(f"You have {len(alarm_states)} alarms matching the same time {models.env.title}!")
                response = f"Your alarm at {alarm_states[0]} has been silenced {models.env.title}!"
                files.put_alarms(data=[_alarm for _alarm in alarms if _alarm['alarm_time'] != chosen_alarm])
                speaker.speak(text=response)
            else:
                speaker.speak(text=f"There are no such alarms setup {models.env.title}!")
        else:
            speaker.speak(text="Such an alarm time is impossible!")
    else:
        alarm_states = get_alarm_state()
        response = f"Your alarms are at, {util.comma_separator(alarm_states)}. " \
                   "Please let me know which one I should delete."
        speaker.speak(text=response)


def executor() -> NoReturn:
    """Runs the ``alarm.mp3`` file at max volume and reverts the volume after 3 minutes."""
    pyvolume.pyvolume(level=100, debug=models.env.debug, logger=logger)
    if models.settings.os != models.supported_platforms.windows:
        subprocess.call(["open", models.indicators.alarm])
    else:
        os.system(f'start wmplayer {models.indicators.alarm}')
    time.sleep(200)
    pyvolume.pyvolume(level=models.env.volume, debug=models.env.debug, logger=logger)
