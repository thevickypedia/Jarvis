import random
import re
from datetime import datetime, timedelta
from typing import NoReturn

import pynotification

from jarvis.executors import communicator, files, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, util


def create_reminder(time: datetime, message: str, to_about: str, timer: str = None, name: str = None) -> NoReturn:
    """Creates the lock file necessary to set a reminder.

    Args:
        time: Time of reminder as a datetime object.
        message: Message to be reminded for.
        to_about: remind to or remind about as said in phrase.
        timer: Number of minutes/hours to reminder.
        name: Custom contact to remind.
    """
    existing_reminders = files.get_reminders()
    formatted = dict(
        time=time.strftime("%I:%M %p"),
        message=message,
        name=name
    )
    name = name or "you"
    if formatted in existing_reminders:
        speaker.speak(text=f"You have a duplicate reminder {models.env.title}!")
        return
    existing_reminders.append(formatted)
    files.put_reminders(data=existing_reminders)
    if timer:
        logger.info("Reminder created for '%s' at %s", message, time.strftime("%I:%M %p"))
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I will remind {name} {to_about} {message}, after {timer}.")
    else:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I will remind {name} {to_about} {message}, at {time.strftime('%I:%M %p')}.")


def find_name(phrase: str) -> str:
    """Looks for names in contact file if there is any matching the phrase."""
    contacts = files.get_contacts()
    if (name := word_match.word_match(phrase=phrase, match_list=list(contacts.get('phone', {}).keys()))) or \
            (name := word_match.word_match(phrase=phrase, match_list=list(contacts.get('email', {}).keys()))):
        logger.info("Reminder requested for third party: %s", name)
        return name


def reminder(phrase: str) -> None:
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if models.settings.limited:
        speaker.speak(text="Reminder features are currently unavailable, as you're running on restricted mode.")
        return
    message = re.search(' to (.*) at ', phrase) or re.search(' about (.*) at ', phrase) or \
        re.search(' to (.*) after ', phrase) or re.search(' about (.*) after ', phrase) or \
        re.search(' to (.*) in ', phrase) or re.search(' about (.*) in ', phrase) or \
        re.search(' to (.*)', phrase) or re.search(' about (.*)', phrase)
    if not message:
        speaker.speak(text='Reminder format should be::Remind me to do something, at some time.')
        return
    to_about = 'about' if 'about' in phrase else 'to'
    if 'minute' in phrase or "now" in phrase:
        phrase = phrase.replace("a minute", "1 minute").replace("now", "1 minute")
        if minutes := util.extract_nos(input_=phrase, method=int):
            min_ = 'minutes' if minutes > 1 else 'minute'
            create_reminder(time=datetime.now() + timedelta(minutes=minutes), message=message.group(1).strip(),
                            timer=f"{minutes} {min_}", to_about=to_about, name=find_name(phrase=phrase))
            return
    elif 'hour' in phrase:
        if hours := util.extract_nos(input_=phrase, method=int):
            hour_ = 'hours' if hours > 1 else 'hour'
            create_reminder(time=datetime.now() + timedelta(hours=hours), message=message.group(1).strip(),
                            timer=f"{hours} {hour_}", to_about=to_about, name=find_name(phrase=phrase))
            return
    if not (extracted_time := util.extract_time(input_=phrase)):
        if shared.called_by_offline:
            speaker.speak(text='Reminder format should be::Remind me to do something, at some time.')
            return
        speaker.speak(text=f"When do you want to be reminded {models.env.title}?", run=True)
        if not (phrase := listener.listen()):
            return
        if not (extracted_time := util.extract_time(input_=phrase)):
            return
    message = message.group(1).strip()
    extracted_time = extracted_time[0]
    am_pm = extracted_time.split()[-1]
    am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
    remind_time = extracted_time.split()[0]
    if ":" in extracted_time:
        hour = int(remind_time.split(":")[0])
        minute = int(remind_time.split(":")[-1])
    else:
        hour = int(remind_time.split()[0])
        minute = 0
    # makes sure hour and minutes are two digits
    hour, minute = f"{hour:02}", f"{minute:02}"
    if int(hour) <= 12 and int(minute) <= 59:
        datetime_obj = datetime.strptime(f"{hour}:{minute} {am_pm}", "%I:%M %p")
        create_reminder(time=datetime_obj, to_about=to_about, message=message, name=find_name(phrase=phrase))
    else:
        speaker.speak(text=f"A reminder at {hour}:{minute} {am_pm}? Are you an alien? "
                           f"I don't think a time like that exists on Earth.")


def executor(message: str, contact: str = None) -> NoReturn:
    """Notifies user about the reminder and displays a notification on the device.

    Args:
        message: Takes the reminder message as an argument.
        contact: Name of the person to send the reminder to.

    See Also:
        - Personalized icons for `Linux OS <https://wiki.ubuntu.com/Artwork/BreatheIconSet/Icons>`__
    """
    title = f"REMINDER from Jarvis {datetime.now().strftime('%c')}"
    if contact:
        contacts = files.get_contacts()
        if phone := contacts.get('phone', {}).get(contact):
            communicator.send_sms(user=models.env.gmail_user, password=models.env.gmail_pass,
                                  number=phone, body=message, subject=title)
        if email := contacts.get('email', {}).get(contact):
            communicator.send_email(gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass,
                                    recipient=email, subject=title, body=message)
        return
    communicator.send_sms(user=models.env.gmail_user, password=models.env.gmail_pass, number=models.env.phone_number,
                          body=message, subject=title)
    communicator.send_email(gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass,
                            recipient=models.env.recipient, subject=title, body=message)
    pynotification.pynotifier(title=title, message=message, debug=True, logger=logger)
