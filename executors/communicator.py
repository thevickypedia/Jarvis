import re
import sys

from gmailconnector.read_email import ReadEmail
from gmailconnector.send_sms import Messenger

from executors.word_match import word_match
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import shared, support


def read_gmail() -> None:
    """Reads unread emails from the gmail account for which the credentials are stored in env variables."""
    if not all([models.env.gmail_user, models.env.gmail_pass]):
        logger.warning("Gmail username and password not found.")
        support.no_env_vars()
        return

    sys.stdout.write("\rFetching unread emails..")
    reader = ReadEmail(gmail_user=models.env.gmail_user, gmail_pass=models.env.gmail_pass)
    response = reader.instantiate()
    if response.ok:
        if shared.called_by_offline:
            speaker.speak(text=f'You have {response.count} unread email {models.env.title}.') if response.count == 1 \
                else speaker.speak(text=f'You have {response.count} unread emails {models.env.title}.')
            return
        speaker.speak(text=f'You have {response.count} unread emails {models.env.title}. Do you want me to check it?',
                      run=True)
        if not (confirmation := listener.listen()):
            return
        if not word_match(phrase=confirmation, match_list=keywords.keywords.ok):
            return
        unread_emails = reader.read_email(response.body)
        for mail in list(unread_emails):
            speaker.speak(text=f"You have an email from, {mail.get('sender').strip()}, with subject, "
                               f"{mail.get('subject').strip()}, {mail.get('datetime').strip()}", run=True)
    elif response.status == 204:
        speaker.speak(text=f"You don't have any emails to catch up {models.env.title}!")
    else:
        speaker.speak(text=f"I was unable to read your email {models.env.title}!")


def send_sms(phrase: str) -> None:
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        phrase: Takes phrase spoken as an argument.
    """
    message = re.search('send (.*) to ', phrase) or re.search('Send (.*) to ', phrase)
    body = message.group(1) if message else None
    if number := support.extract_nos(input_=phrase, method=int):
        number = str(number)
    if number and body and shared.called_by_offline:
        if len(number) != 10:
            speaker.speak(text=f"I don't think that's a right number {models.env.title}! Phone numbers are 10 digits.")
            return
        notify(user=models.env.gmail_user, password=models.env.gmail_pass, number=number, body=body)
        speaker.speak(text=f"Message has been sent {models.env.title}!")
        return
    elif shared.called_by_offline:
        speaker.speak(text="Messenger format should be::send some message to some number.")
        return
    if not number:
        speaker.speak(text=f"Please tell me a number {models.env.title}!", run=True)
        if not (number := listener.listen()):
            return
        if 'exit' in number or 'quit' in number or 'Xzibit' in number:
            return
    if len(number) != 10:
        speaker.speak(text=f"I don't think that's a right number {models.env.title}! Phone numbers are 10 digits. "
                           "Try again!")
        return
    speaker.speak(text=f"What would you like to send {models.env.title}?", run=True)
    if body := listener.listen():
        speaker.speak(text=f'{body} to {number}. Do you want me to proceed?', run=True)
        if converted := listener.listen():
            if word_match(phrase=converted, match_list=keywords.keywords.ok):
                logger.info(f'{body} -> {number}')
                notify(user=models.env.gmail_user, password=models.env.gmail_pass, number=number, body=body)
                speaker.speak(text=f"Message has been sent {models.env.title}!")
            else:
                speaker.speak(text=f"Message will not be sent {models.env.title}!")


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
    if not any([models.env.phone_number, number]):
        logger.error('No phone number was stored in env vars to trigger a notification.')
        return
    if not subject:
        subject = "Message from Jarvis" if number == models.env.phone_number else f"Message from {models.env.name}"
    sms_object = Messenger(gmail_user=user, gmail_pass=password)
    auth = sms_object.authenticate
    if auth.ok:
        response = sms_object.send_sms(phone=number or models.env.phone_number, subject=subject, message=body)
        if response.ok:
            logger.info('SMS notification has been sent.')
        else:
            logger.error(f'Unable to send SMS notification.\n{response.body}')
    else:
        logger.error(f'Unable to send SMS notification.\n{auth.body}')
