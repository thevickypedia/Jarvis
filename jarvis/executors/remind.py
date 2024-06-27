import random
import re
import string
from datetime import datetime, timedelta
from typing import List

import pynotification

from jarvis.executors import communicator, files, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.telegram import bot
from jarvis.modules.utils import shared, support, util


def create_reminder(
    reminder_time: datetime,
    message: str,
    to_about: str,
    phrase: str,
    day: str = None,
    timer: str = None,
) -> None:
    """Updates the reminder file to set a reminder.

    Args:
        reminder_time: Time of reminder as a datetime object.
        message: Message to be reminded for.
        to_about: remind to or remind about as said in phrase.
        phrase: Phrase spoken by the user.
        day: Day to include in the response.
        timer: Number of minutes/hours to reminder.
    """
    existing_reminders = files.get_reminders()
    name = find_name(phrase)
    formatted = dict(
        name=name,
        message=message,
        date=reminder_time.date(),
        reminder_time=reminder_time.strftime("%I:%M %p"),
    )
    name = name or "you"
    if formatted in existing_reminders:
        speaker.speak(text=f"You have a duplicate reminder {models.env.title}!")
        return
    existing_reminders.append(formatted)
    files.put_reminders(data=existing_reminders)
    logger.info(
        "Reminder created for '%s' at %s", message, reminder_time.strftime("%I:%M %p")
    )
    if timer:
        response = (
            f"{random.choice(conversation.acknowledgement)}! "
            f"I will remind {name} {to_about} {message}, after {timer}."
        )
    elif day in ("today", "tonight", "tomorrow"):
        response = (
            f"{random.choice(conversation.acknowledgement)}! "
            f"I will remind {name} {to_about} {message}, {day} at {reminder_time.strftime('%I:%M %p')}."
        )
    elif reminder_time.date() == datetime.today().date():
        response = (
            f"{random.choice(conversation.acknowledgement)}! "
            f"I will remind {name} {to_about} {message}, today at {reminder_time.strftime('%I:%M %p')}."
        )
    elif day:
        response = (
            f"{random.choice(conversation.acknowledgement)}! "
            f"I will remind {name} {to_about} {message}, on {day} at {reminder_time.strftime('%I:%M %p')}."
        )
    else:
        response = (
            f"{random.choice(conversation.acknowledgement)}! "
            f"I will remind {name} {to_about} {message}, at {reminder_time.strftime('%I:%M %p')}."
        )
    if "every" in phrase:
        response += " For repeated reminders, please use the automation feature."
    speaker.speak(text=response)


def find_name(phrase: str) -> str:
    """Looks for names in contact file if there is any matching the phrase."""
    contacts = files.get_contacts()
    if (
        name := word_match.word_match(
            phrase=phrase, match_list=list(contacts.get("phone", {}).keys())
        )
    ) or (
        name := word_match.word_match(
            phrase=phrase, match_list=list(contacts.get("email", {}).keys())
        )
    ):
        logger.info("Reminder requested for third party: %s", name)
        return name


def get_reminder_state() -> List[str]:
    """Frames a response text with all the reminders present.

    Returns:
        List[str]:
        Returns a list of reminders framed as a response.
    """
    reminders = files.get_reminders()
    response = []
    for reminder_ in reminders:
        if reminder_["name"]:
            response.append(
                f"{reminder_['message']} to {reminder_['name']} at {reminder_['reminder_time']}"
            )
        else:
            response.append(f"{reminder_['message']} at {reminder_['reminder_time']}")
    return response


def reminder(phrase: str) -> None:
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if models.settings.limited:
        speaker.speak(
            text="Reminder features are currently unavailable, as you're running on restricted mode."
        )
        return
    message = (
        re.search(" to (.*) in ", phrase)
        or re.search(" about (.*) in ", phrase)
        or re.search(" to (.*) after ", phrase)
        or re.search(" about (.*) after ", phrase)
        or re.search(" to (.*) at ", phrase)
        or re.search(" about (.*) at ", phrase)
        or re.search(" to (.*)", phrase)
        or re.search(" about (.*)", phrase)
    )
    if not message:
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
            if reminder_list := get_reminder_state():
                speaker.speak(
                    text=f"You have {len(reminder_list)} reminders {models.env.title}! "
                    f"{string.capwords(util.comma_separator(reminder_list))}"
                )
            else:
                speaker.speak(text=f"You don't have any reminders {models.env.title}!")
            return
        speaker.speak(
            text="Reminder format should be::Remind me to do something, at some time."
        )
        return
    to_about = "about" if "about" in phrase else "to"
    if "minute" in phrase or "now" in phrase:
        phrase = phrase.replace("a minute", "1 minute").replace("now", "1 minute")
        if minutes := util.extract_nos(input_=phrase, method=int):
            min_ = "minutes" if minutes > 1 else "minute"
            create_reminder(
                reminder_time=datetime.now() + timedelta(minutes=minutes),
                message=message.group(1).strip(),
                timer=f"{minutes} {min_}",
                to_about=to_about,
                phrase=phrase,
            )
            return
    elif "hour" in phrase:
        if hours := util.extract_nos(input_=phrase, method=int):
            hour_ = "hours" if hours > 1 else "hour"
            create_reminder(
                reminder_time=datetime.now() + timedelta(hours=hours),
                message=message.group(1).strip(),
                timer=f"{hours} {hour_}",
                to_about=to_about,
                phrase=phrase,
            )
            return
    if not (extracted_time := util.extract_time(input_=phrase)):
        if shared.called_by_offline:
            speaker.speak(
                text="Reminder format should be::Remind me to do something, at some time."
            )
            return
        speaker.speak(
            text=f"When do you want to be reminded {models.env.title}?", run=True
        )
        if not (phrase := listener.listen()):
            return
        if not (extracted_time := util.extract_time(input_=phrase)):
            return
    message = message.group(1).strip()
    hour, minute, am_pm = util.split_time(extracted_time[0])
    if int(hour) <= 12 and int(minute) <= 59:
        reminder_time_ = f"{hour}:{minute} {am_pm}"
        try:
            reminder_date_, day, _ = support.extract_humanized_date(
                phrase=phrase, fail_past=True
            )
            datetime_obj = datetime.combine(
                reminder_date_, datetime.strptime(reminder_time_, "%I:%M %p").time()
            )
            # if user specifically mentions today or tonight with a time in the past
            if (
                datetime_obj <= datetime.now()
                and "today" in phrase
                or "tonight" in phrase
            ):
                raise ValueError(f"{datetime_obj!r} is in the past!")
        except ValueError as error:
            logger.error(error)
            speaker.speak(
                "We are not time travellers yet, so reminders in the past is not a thing."
            )
            return

        # if user doesn't specify the date but time is in the past, reminder will be defaulted for the next day
        if datetime_obj.date() == datetime.now().date() and datetime_obj.hour > 17:
            day = "tonight"
        elif datetime_obj <= datetime.now():
            datetime_obj += timedelta(days=1)
            day = "tomorrow"
        # requested for next day
        elif datetime_obj.date() == (datetime.now().date() + timedelta(days=1)):
            day = "tomorrow"

        # strip off statements like today, tomorrow, day after tomorrow from message
        message = message.replace(day, "")

        create_reminder(
            reminder_time=datetime_obj,
            to_about=to_about,
            message=message,
            phrase=phrase,
            day=day,
        )
    else:
        speaker.speak(
            text=f"A reminder at {hour}:{minute} {am_pm}? Are you an alien? "
            f"I don't think a time like that exists on Earth."
        )


def executor(message: str, contact: str = None) -> None:
    """Notifies user about the reminder (per the options set in env vars) and displays a notification on the device.

    Args:
        message: Takes the reminder message as an argument.
        contact: Name of the person to send the reminder to.

    See Also:
        - Uses phone number to send SMS notification
        - Uses recipient email address to send email notification
        - Uses telegram account ID to send a message notification
        - Uses NTFY topic to send a push notification
    """
    if enums.ReminderOptions.all in models.env.notify_reminders:
        notify_phone, notify_email, notify_telegram, ntfy = True, True, True, True
    else:
        notify_phone = enums.ReminderOptions.phone in models.env.notify_reminders
        notify_email = enums.ReminderOptions.email in models.env.notify_reminders
        notify_telegram = enums.ReminderOptions.telegram in models.env.notify_reminders
        ntfy = enums.ReminderOptions.ntfy in models.env.notify_reminders
    title = f"REMINDER from Jarvis - {datetime.now().strftime('%c')}"
    if contact:
        contacts = files.get_contacts()
        if notify_phone and (phone := contacts.get("phone", {}).get(contact)):
            communicator.send_sms(
                user=models.env.gmail_user,
                password=models.env.gmail_pass,
                number=phone,
                body=message,
                subject=title,
            )
        if notify_email and (email := contacts.get("email", {}).get(contact)):
            communicator.send_email(
                gmail_user=models.env.open_gmail_user,
                gmail_pass=models.env.open_gmail_pass,
                recipient=email,
                subject=title,
                body=message,
            )
        if notify_telegram and (chat_id := contacts.get("telegram", {}).get(contact)):
            bot.send_message(chat_id=int(chat_id), response=f"*{title}*\n\n{message}")
        if ntfy and (ntfy_topic := contacts.get("ntfy", {}).get(contact)):
            communicator.ntfy_send(topic=ntfy_topic, title=title, message=message)
        return
    if notify_phone and models.env.phone_number:
        communicator.send_sms(
            user=models.env.gmail_user,
            password=models.env.gmail_pass,
            number=models.env.phone_number,
            body=message,
            subject=title,
        )
    if notify_email and models.env.recipient:
        communicator.send_email(
            gmail_user=models.env.open_gmail_user,
            gmail_pass=models.env.open_gmail_pass,
            recipient=models.env.recipient,
            subject=title,
            body=message,
        )
    if notify_telegram and models.env.telegram_id:
        bot.send_message(
            chat_id=models.env.telegram_id, response=f"*{title}*\n\n{message}"
        )
    if ntfy and models.env.ntfy_topic:
        communicator.ntfy_send(
            topic=models.env.ntfy_topic, title=title, message=message
        )
    pynotification.pynotifier(title=title, message=message, debug=True, logger=logger)
