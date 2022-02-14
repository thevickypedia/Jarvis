from os import environ

from gmailconnector.send_sms import Messenger

from executors.custom_logger import logger

phone_number = environ.get('phone_number')


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
    if not any([phone_number, number]):
        logger.error('No phone number was stored in env vars to trigger a notification.')
        return
    if not subject:
        subject = "Message from Jarvis" if number == phone_number else "Jarvis::Message from Vignesh"
    response = Messenger(gmail_user=user, gmail_pass=password, phone=number, subject=subject,
                         message=body).send_sms()
    if response.ok and response.status == 200:
        logger.info('SMS notification has been sent.')
    else:
        logger.error(f'Unable to send SMS notification.\n{response.body}')
