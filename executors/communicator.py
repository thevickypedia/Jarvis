import sys

from gmailconnector.read_email import ReadEmail
from gmailconnector.send_sms import Messenger

from executors.logger import logger
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.models import models
from modules.utils import shared, support

env = models.env


def read_gmail() -> None:
    """Reads unread emails from the gmail account for which the credentials are stored in env variables."""
    if not all([env.gmail_user, env.gmail_pass]):
        support.no_env_vars()
        return
    sys.stdout.write("\rFetching unread emails..")
    reader = ReadEmail(gmail_user=env.gmail_user, gmail_pass=env.gmail_pass)
    response = reader.instantiate()
    if response.ok:
        if shared.called_by_offline:
            speaker.speak(text=f'You have {response.count} unread email {env.title}.') if response.count == 1 else \
                speaker.speak(text=f'You have {response.count} unread emails {env.title}.')
            return
        speaker.speak(text=f'You have {response.count} unread emails {env.title}. Do you want me to check it?',
                      run=True)
        confirmation = listener.listen(timeout=3, phrase_limit=3)
        if confirmation == 'SR_ERROR':
            return
        if not any(word in confirmation.lower() for word in keywords.ok):
            return
        unread_emails = reader.read_email(response.body)
        for mail in list(unread_emails):
            speaker.speak(text=f"You have an email from, {mail.get('sender').strip()}, with subject, "
                               f"{mail.get('subject').strip()}, {mail.get('datetime').strip()}", run=True)
    elif response.status == 204:
        speaker.speak(text=f"You don't have any emails to catch up {env.title}!")
    else:
        speaker.speak(text=f"I was unable to read your email {env.title}!")


def send_sms(phrase: str) -> None:
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        phrase: Takes phrase spoken as an argument.
    """
    if number := support.extract_nos(input_=phrase, method=int):
        number = str(number)
    else:
        speaker.speak(text=f"Please tell me a number {env.title}!", run=True)
        number = listener.listen(timeout=3, phrase_limit=7)
        if number != 'SR_ERROR':
            if 'exit' in number or 'quit' in number or 'Xzibit' in number:
                return
    if len(number) != 10:
        speaker.speak(text=f"I don't think that's a right number {env.title}! Phone numbers are 10 digits. Try again!")
        return
    speaker.speak(text=f"What would you like to send {env.title}?", run=True)
    body = listener.listen(timeout=3, phrase_limit=5)
    if body != 'SR_ERROR':
        speaker.speak(text=f'{body} to {number}. Do you want me to proceed?', run=True)
        converted = listener.listen(timeout=3, phrase_limit=3)
        if converted != 'SR_ERROR':
            if any(word in converted.lower() for word in keywords.ok):
                logger.info(f'{body} -> {number}')
                notify(user=env.gmail_user, password=env.gmail_pass, number=number, body=body)
                speaker.speak(text=f"Message has been sent {env.title}!")
            else:
                speaker.speak(text=f"Message will not be sent {env.title}!")


def notify(user: str, password: str, number: str, body: str, subject: str = None) -> None:
    """Send text message through SMS gateway of destination number.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS.

    Args:
        user: Gmail username to authenticate SMTP lib.
        password: Gmail password to authenticate SMTP lib.
        number: Phone number stored as env var.
        body: Content of the message.
        subject: Takes subject as an optional argument.
    """
    if not any([env.phone_number, number]):
        logger.error('No phone number was stored in env vars to trigger a notification.')
        return
    if not subject:
        subject = "Message from Jarvis" if number == env.phone_number else f"Jarvis::Message from {env.name}"
    response = Messenger(gmail_user=user, gmail_pass=password, phone=number, subject=subject,
                         message=body).send_sms()
    if response.ok and response.status == 200:
        logger.info('SMS notification has been sent.')
    else:
        logger.error(f'Unable to send SMS notification.\n{response.body}')
