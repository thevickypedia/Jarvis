import os
import random
import re
import sys

from executors import communicator
from modules.audio import listener, speaker
from modules.conditions import conversation
from modules.models import models
from modules.utils import globals

env = models.env


def reminder(phrase: str) -> None:
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts the time and message from it.
    """
    message = re.search(' to (.*) at ', phrase) or re.search(' about (.*) at ', phrase)
    if not message:
        message = re.search(' to (.*)', phrase) or re.search(' about (.*)', phrase)
        if not message:
            speaker.speak(text='Reminder format should be::Remind me to do something, at some time.')
            sys.stdout.write('\rReminder format should be::Remind ME to do something, AT some time.')
            return
    phrase = phrase.lower()
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', phrase) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', phrase) or re.findall(r'([0-9]+\s?(?:am|pm:?))', phrase)
    if not extracted_time:
        if globals.called_by_offline['status']:
            speaker.speak(text='Reminder format should be::Remind me to do something, at some time.')
            return
        speaker.speak(text=f"When do you want to be reminded {env.title}?", run=True)
        phrase = listener.listen(timeout=3, phrase_limit=4)
        if phrase != 'SR_ERROR':
            extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', phrase) or re.findall(
                r'([0-9]+\s?(?:a.m.|p.m.:?))', phrase)
        else:
            return
    if message and extracted_time:
        to_about = 'about' if 'about' in phrase else 'to'
        message = message.group(1).strip()
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
        if int(hour) <= 12 and int(minute) <= 59:
            os.system(f'mkdir -p reminder && touch reminder/{hour}_{minute}_{am_pm}-{message.replace(" ", "_")}.lock')
            speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                               f"I will remind you {to_about} {message}, at {hour}:{minute} {am_pm}.")
        else:
            speaker.speak(text=f"A reminder at {hour}:{minute} {am_pm}? Are you an alien? "
                               f"I don't think a time like that exists on Earth.")
    else:
        speaker.speak(text='Reminder format should be::Remind me to do something, at some time.')
        sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
    return


def reminder_executor(message: str) -> None:
    """Notifies user about the reminder and displays a notification on the device.

    Args:
        message: Takes the reminder message as an argument.
    """
    communicator.notify(user=env.gmail_user, password=env.gmail_pass, number=env.phone_number, body=message,
                        subject="REMINDER from Jarvis")
    os.system(f"""osascript -e 'display notification "{message}" with title "REMINDER from Jarvis"'""")
