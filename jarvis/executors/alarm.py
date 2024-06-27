import os
import random
import string
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List

import pyvolume

from jarvis.executors import files, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.utils import shared, support, util


def check_overlap(
    new_alarm: Dict[str, str | bool], old_alarms: List[Dict[str, str | bool]]
) -> bool:
    """Checks to see if there is a possibility of an overlap.

    Args:
        new_alarm: Current alarm formatted as a dict.
        old_alarms: List of existing alarms.

    Returns:
        bool:
        Returns a True flag if it is an overlap.
    """
    if new_alarm in old_alarms:
        speaker.speak(text=f"You have a duplicate alarm {models.env.title}!")
        return True
    for old_alarm in old_alarms:
        # old alarm is set for the same time and the old alarm is set for everyday
        difference = abs(
            (
                datetime.strptime(old_alarm["alarm_time"], "%I:%M %p")
                - datetime.strptime(new_alarm["alarm_time"], "%I:%M %p")
            ).total_seconds()
        )
        # check if alarm time are the same or overlaps within 230 seconds (number of seconds an alarm will play)
        # check if the alarm is set daily ('repeat' is 'True' but 'day' is null)
        if (
            (new_alarm["alarm_time"] == old_alarm["alarm_time"] or difference <= 203)
            and old_alarm["repeat"]
            and not old_alarm.get("day")
        ):
            if difference <= 203:  # within 203 seconds of an existing alarm
                logger.info(
                    "Difference between both the alarms in seconds: %.2f", difference
                )
            speaker.speak(
                text=f"You have an existing alarm, at {old_alarm['alarm_time']} "
                f"that overlaps with this one {models.env.title}!"
            )
            return True


def create_alarm(
    alarm_time: datetime,
    phrase: str,
    timer: str = None,
    repeat: bool = False,
    day: str = None,
) -> None:
    """Creates an entry in the alarms' mapping file.

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
        formatted.pop("day")
    if check_overlap(new_alarm=formatted, old_alarms=existing_alarms):
        return
    existing_alarms.append(formatted)
    files.put_alarms(data=existing_alarms)
    logger.info("Alarm/timer set at {%s}", alarm_time.strftime("%I:%M %p"))
    if "wake" in phrase:
        speaker.speak(
            text=f"{random.choice(conversation.acknowledgement)}! "
            f"I will wake you up at {alarm_time.strftime('%I:%M %p')}."
        )
    elif "timer" in phrase and timer:
        response = [
            f"{random.choice(conversation.acknowledgement)}! I have set a timer for {timer}.",
            f"{timer}! Counting down..",
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
            f"Your alarm is set for {alarm_time.strftime('%I:%M %p')} {add}",
        ]
        speaker.speak(
            text=f"{random.choice(conversation.acknowledgement)}! {random.choice(response)}"
        )


def set_alarm(phrase: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if models.settings.limited:
        speaker.speak(
            text="Alarm features are currently unavailable, as you're running on restricted mode."
        )
        return
    phrase = phrase.lower()
    if "minute" in phrase:
        if minutes := util.extract_nos(input_=phrase, method=int):
            create_alarm(
                alarm_time=datetime.now() + timedelta(minutes=minutes),
                phrase=phrase,
                timer=f"{minutes} {support.ENGINE.plural(text='minute', count=minutes)}",
            )
            return
    elif "hour" in phrase:
        if hours := util.extract_nos(input_=phrase, method=int):
            create_alarm(
                alarm_time=datetime.now() + timedelta(hours=hours),
                phrase=phrase,
                timer=f"{hours} {support.ENGINE.plural(text='hour', count=hours)}",
            )
            return
    if extracted_time := util.extract_time(input_=phrase) or word_match.word_match(
        phrase=phrase, match_list=("noon", "midnight", "mid night")
    ):
        if "noon" in phrase:
            extracted_time = ["12:00 PM"]
        elif "night" in phrase:
            extracted_time = ["12:00 AM"]
        hour, minute, am_pm = util.split_time(input_=extracted_time[0])
        if int(hour) <= 12 and int(minute) <= 59:
            datetime_obj = datetime.strptime(f"{hour}:{minute} {am_pm}", "%I:%M %p")
            if day := word_match.word_match(
                phrase=phrase,
                match_list=(
                    "sunday",
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sundays",
                    "mondays",
                    "tuesdays",
                    "wednesdays",
                    "thursdays",
                    "fridays",
                    "saturdays",
                ),
            ):
                create_alarm(
                    phrase=phrase,
                    alarm_time=datetime_obj,
                    day=string.capwords(day),
                    repeat=True,
                )
            elif word_match.word_match(
                phrase=phrase, match_list=("everyday", "every day", "daily")
            ):
                create_alarm(phrase=phrase, alarm_time=datetime_obj, repeat=True)
            else:
                create_alarm(phrase=phrase, alarm_time=datetime_obj)
        else:
            speaker.speak(
                text=f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                "I don't think a time like that exists on Earth."
            )
    else:
        if word_match.word_match(
            phrase=phrase,
            match_list=(
                "get",
                "what",
                "send",
                "list",
                "exist",
                "existing",
                "do",
                "have",
                "i",
            ),
        ):
            if alarm_states := get_alarm_state():
                if len(alarm_states) > 1:
                    speaker.speak(
                        text=f"Your alarms are at, {util.comma_separator(alarm_states)}."
                    )
                else:
                    speaker.speak(
                        text=f"You have an alarm at, {util.comma_separator(alarm_states)}."
                    )
            else:
                speaker.speak(text=f"You don't have any alarms set {models.env.title}!")
            return
        speaker.speak(text=f"Please tell me a time {models.env.title}!")
        if shared.called_by_offline:
            return
        speaker.speak(run=True)
        if converted := listener.listen():
            if "exit" in converted or "quit" in converted or "Xzibit" in converted:
                return
            else:
                set_alarm(converted)


def get_alarm_state(alarm_time: str = None) -> List[str]:
    """Frames a response text with all the alarms present.

    Returns:
        List[str]:
        Returns a list of alarms framed as a response.
    """
    _alarms = files.get_alarms()
    if alarm_time:
        _alarms = [_alarm for _alarm in _alarms if _alarm["alarm_time"] == alarm_time]
    response = []
    for _alarm in _alarms:
        if _alarm["repeat"]:
            response.append(
                f"{_alarm['alarm_time']} on every {_alarm.get('day', 'day')}"
            )
        else:
            response.append(_alarm["alarm_time"])
    return response


def more_than_one_alarm_to_kill(
    alarms: List[Dict[str, str | bool]], phrase: str, alarm_states: List[str]
) -> None:
    """Helper function for kill alarm, if there are multiple alarms set at the same time with different days.

    Args:
        alarms: All existing alarms.
        phrase: Takes the phrase spoken as an argument.
        alarm_states: Alarms that were converted as response.
    """
    if day := word_match.word_match(
        phrase=phrase,
        match_list=(
            "sunday",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sundays",
            "mondays",
            "tuesdays",
            "wednesdays",
            "thursdays",
            "fridays",
            "saturdays",
        ),
    ):
        del_alarm = None
        for __alarm in alarms:
            if __alarm.get("day", "").lower() == day.lower():
                del_alarm = __alarm
                break
        if del_alarm:
            if del_alarm["repeat"]:
                speaker.speak(
                    text=f"Your alarm at {del_alarm['alarm_time']} on every "
                    f"{del_alarm.get('day', 'day')} has been silenced {models.env.title}!"
                )
            else:
                speaker.speak(
                    text=f"Your alarm at {del_alarm['alarm_time']} "
                    f"has been silenced {models.env.title}!"
                )
            alarms.remove(del_alarm)
            files.put_alarms(alarms)
        else:
            speaker.speak(text=f"There are no such alarms setup {models.env.title}!")
    else:
        speaker.speak(
            f"You have {len(alarm_states)} alarms matching the same time {models.env.title}! "
            f"{util.comma_separator(alarm_states)}. Please be more specific."
        )


def kill_alarm(phrase: str) -> None:
    """Removes the entry from the alarms' mapping file.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    word = "timer" if "timer" in phrase else "alarm"
    alarms = files.get_alarms()
    if not alarms:
        speaker.speak(text=f"You have no {word}s set {models.env.title}!")
        return
    if len(alarms) == 1:
        _alarm = alarms[0]
        response = f"Your {word} at {_alarm['alarm_time']} "
        if _alarm["repeat"]:
            response += f"on every {_alarm.get('day', 'day')} "
        response += f"has been silenced {models.env.title}!"
        speaker.speak(text=response)
        alarms.clear()
        files.put_alarms(data=alarms)
        return
    if "all" in phrase.split():
        speaker.speak(
            text=f"I have silenced {len(alarms)} of your alarms {models.env.title}!"
        )
        alarms.clear()
        files.put_alarms(data=alarms)
        return
    if extracted_time := util.extract_time(input_=phrase) or word_match.word_match(
        phrase=phrase, match_list=("noon", "midnight", "mid night")
    ):
        if "noon" in phrase:
            extracted_time = ["12:00 PM"]
        elif "night" in phrase:
            extracted_time = ["12:00 AM"]
        hour, minute, am_pm = util.split_time(extracted_time[0])
        if int(hour) <= 12 and int(minute) <= 59:
            chosen_alarm = f"{hour}:{minute} {am_pm}"
            if chosen_alarm in [_alarm["alarm_time"] for _alarm in alarms]:
                # construct response before updating the base file
                alarm_states = get_alarm_state(alarm_time=chosen_alarm)
                if len(alarm_states) > 1:
                    more_than_one_alarm_to_kill(alarms, phrase, alarm_states)
                    return
                response = f"Your alarm at {alarm_states[0]} has been silenced {models.env.title}!"
                files.put_alarms(
                    data=[
                        _alarm
                        for _alarm in alarms
                        if _alarm["alarm_time"] != chosen_alarm
                    ]
                )
                speaker.speak(text=response)
            else:
                speaker.speak(
                    text=f"There are no such alarms setup {models.env.title}!"
                )
        else:
            speaker.speak(text="Such an alarm time is impossible!")
    else:
        alarm_states = get_alarm_state()
        response = (
            f"Your alarms are at, {util.comma_separator(alarm_states)}. "
            "Please let me know which one I should delete."
        )
        speaker.speak(text=response)


def executor() -> None:
    """Runs the ``alarm.mp3`` file at max volume and reverts the volume after 3 minutes."""
    pyvolume.increase(logger)
    if models.settings.os != enums.SupportedPlatforms.windows:
        subprocess.call(["open", models.indicators.alarm])
    else:
        os.system(f"start wmplayer {models.indicators.alarm}")
    time.sleep(200)
    pyvolume.custom(models.env.volume, logger)
