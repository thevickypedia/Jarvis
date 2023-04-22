from typing import Union

import gmailconnector
import jinja2
from pydantic import EmailStr

from jarvis.executors import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import shared, support, util


def read_gmail() -> None:
    """Reads unread emails from the gmail account for which the credentials are stored in env variables."""
    if not all([models.env.gmail_user, models.env.gmail_pass]):
        logger.warning("Gmail username and password not found.")
        support.no_env_vars()
        return

    util.write_screen(text="Fetching unread emails..")
    reader = gmailconnector.ReadEmail(gmail_user=models.env.gmail_user, gmail_pass=models.env.gmail_pass)
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
        if not word_match.word_match(phrase=confirmation, match_list=keywords.keywords.ok):
            return
        for mail in reader.read_mail(messages=response.body, humanize_datetime=True):
            speaker.speak(text=f"You have an email from, {mail.sender}, with subject, "
                               f"{mail.subject}, {mail.date_time}", run=True)
    elif response.status == 204:
        speaker.speak(text=f"You don't have any emails to catch up {models.env.title}!")
    else:
        speaker.speak(text=f"I was unable to read your email {models.env.title}!")


def send_sms(user: str, password: str, number: Union[str, int], body: str, subject: str = None) -> Union[bool, str]:
    """Send text message through SMS gateway of destination number.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS.

    Args:
        user: Gmail username to authenticate SMTP lib.
        password: Gmail password to authenticate SMTP lib.
        number: Phone number stored as env var.
        body: Content of the message.
        subject: Takes subject as an optional argument.

    Returns:
        Union[bool, str]:
        - Boolean flag to indicate the SMS was sent successfully.
        - Error response from gmail-connector.
    """
    if not any([models.env.phone_number, number]):
        logger.error('No phone number was stored in env vars to trigger a notification.')
        return False
    if not subject:
        subject = "Message from Jarvis" if number == models.env.phone_number else f"Message from {models.env.name}"
    sms_object = gmailconnector.SendSMS(gmail_user=user, gmail_pass=password)
    response = sms_object.send_sms(phone=number or models.env.phone_number, subject=subject, message=body)
    if response.ok:
        logger.info('SMS notification has been sent.')
        return True
    else:
        logger.error('Unable to send SMS notification.')
        return response.body


def send_email(body: str, recipient: Union[EmailStr, str], subject: str = None, sender: str = None,
               gmail_user: Union[EmailStr, str] = None, gmail_pass: str = None, title: str = None) -> Union[bool, str]:
    """Sends an email using an email template formatted as html.

    Args:
        body: Message to be inserted as html body in the email.
        sender: Sender name of the email.
        subject: Subject of the email.
        recipient: Email address to which the mail has to be sent.
        gmail_user: Username for email.
        gmail_pass: Password for email.
        title: Sender name on template.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the Email.

    Returns:
        Union[bool, str]:
        - Boolean flag to indicate the email was sent successfully.
        - Error response from gmail-connector.
    """
    if not subject:
        subject = "Message from Jarvis" if recipient == models.env.recipient else f"Message from {models.env.name}"
    rendered = jinja2.Template(source=templates.email.notification).render(SENDER=title or models.env.name,
                                                                           MESSAGE=body)
    email_object = gmailconnector.SendEmail(gmail_user=gmail_user or models.env.gmail_user,
                                            gmail_pass=gmail_pass or models.env.gmail_pass)
    mail_stat = email_object.send_email(recipient=recipient, sender=sender or 'Jarvis Communicator',
                                        subject=subject, html_body=rendered)
    if mail_stat.ok:
        logger.info('Email notification has been sent')
        return True
    else:
        logger.error('Unable to send email notification.')
        return mail_stat.body
