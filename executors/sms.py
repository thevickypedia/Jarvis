from gmailconnector.send_sms import Messenger

from executors.custom_logger import logger
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.utils import globals, support

env = globals.ENV


def send_sms(phrase: str) -> None:
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        phrase: Takes phrase spoken as an argument.
    """
    if number := support.extract_nos(input_=phrase):
        number = str(int(number))
    else:
        speaker.speak(text="Please tell me a number sir!", run=True)
        number = listener.listen(timeout=3, phrase_limit=7)
        if number != 'SR_ERROR':
            if 'exit' in number or 'quit' in number or 'Xzibit' in number:
                return
    if len(number) != 10:
        speaker.speak(text="I don't think that's a right number sir! Phone numbers are 10 digits. Try again!")
        return
    speaker.speak(text="What would you like to send sir?", run=True)
    body = listener.listen(timeout=3, phrase_limit=5)
    if body != 'SR_ERROR':
        speaker.speak(text=f'{body} to {number}. Do you want me to proceed?', run=True)
        converted = listener.listen(timeout=3, phrase_limit=3)
        if converted != 'SR_ERROR':
            if any(word in converted.lower() for word in keywords.ok):
                logger.info(f'{body} -> {number}')
                notify(user=env.gmail_user, password=env.gmail_pass, number=number, body=body)
                speaker.speak(text="Message has been sent sir!")
            else:
                speaker.speak(text="Message will not be sent sir!")


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
        subject = "Message from Jarvis" if number == env.phone_number else "Jarvis::Message from Vignesh"
    response = Messenger(gmail_user=user, gmail_pass=password, phone=number, subject=subject,
                         message=body).send_sms()
    if response.ok and response.status == 200:
        logger.info('SMS notification has been sent.')
    else:
        logger.error(f'Unable to send SMS notification.\n{response.body}')


if __name__ == '__main__':
    send_sms(phrase='send a message to 4174500189')
