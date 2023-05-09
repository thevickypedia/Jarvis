import re
from typing import Union

from pydantic import EmailStr

from jarvis.executors import communicator, files, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util


def extract_contacts(name: str, key: str) -> Union[int, EmailStr, str, None]:
    """Extract contact destination for ``phone`` or ``email`` from the ``contacts.yaml`` file, if present.

    Args:
        name: Name for which the contact information has to be retrieved.
        key: Takes either ``phone`` or ``email`` as an argument.

    Returns:
        Union[int, EmailStr]:
        - EmailStr: If email address is requested.
        - int: If phone number is requested.
    """
    contacts = files.get_contacts()
    if contacts.get(key):
        logger.info("Looking for '%s' in contacts file.", name)
        identifier = util.get_closest_match(text=name, match_list=list(contacts[key].keys()))
        return contacts[key][identifier]


def send_notification(phrase: str) -> None:
    """Initiates notification via SMS or email.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not all([models.env.gmail_user, models.env.gmail_pass]):
        logger.error('Gmail credentials not stored in env vars to trigger an email notification.')
        support.no_env_vars()
        return

    to_words = ['2', 'to', 'To']
    body, to = None, None
    for word in to_words:
        # Catches the last occurrence of the to word
        if msg_grouper := re.search(f'send (.*) {word}', phrase):
            body = msg_grouper.group(1)
        # Catches first occurrence of the to word, making 'to' clumpy but since regex is used for 'to' it is okay
        if to_grouper := re.search(f'{word} (.*)', phrase):
            to = to_grouper.group(1)
        if body and to:
            body, to = body.strip(), to.strip()
            break
    else:
        logger.error("Invalid message or destination: %s -> %s", body, to)
        speaker.speak(text="Messenger format should be::send some message using SMS or email to some number or name.")
        return

    method_words = ['via', 'Via', 'using', 'Using']
    for word in method_words:
        if message := re.search(f'{word} (.*)', phrase):
            method = message.group(1)
            break
    else:
        logger.debug("Message portal not in right format. Looking into phrase to skim.")
        body = None if "text message" in body else body
        if "mail" in phrase:
            method = "email"
        else:
            logger.warning("No valid portal found to send. Defaulting to SMS.") if "message" not in phrase else None
            method = "SMS"
        method_words.append(method)

    if body:
        for word in method.split() + method_words:
            if word in body:
                body = body.replace(word, '')
        body = body.strip()

    for word in method_words + to_words + ['sms', 'email', 'text message']:
        to = to.lower().replace(word, '')
    to = to.strip()

    if to[0].isdigit():
        method = "SMS"

    logger.info("'{body}' -> '{to}' via '{method}'".format(body=body, to=to, method=method))

    if "mail" in method.lower():
        initiate_email(body=body, to=to)
    else:
        initiate_sms(body=body, to=to)


def initiate_sms(body: str, to: Union[str, int]) -> None:
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        body: Message that has to be sent.
        to: Target phone number or name.
    """
    number = None
    if not to[0].isdigit():
        number = str(extract_contacts(name=to, key='phone'))
    if not number:
        number = str(util.extract_nos(input_=to, method=int))

    if number and len(number) != 10:
        speaker.speak(text=f"I don't think that's a right number {models.env.title}! Phone numbers are 10 digits.")
        return

    if number and shared.called_by_offline:  # Number is present and called by offline
        logger.info("'{body}' -> '{number}'".format(body=body, number=number))
        sms_response = communicator.send_sms(user=models.env.gmail_user, password=models.env.gmail_pass,
                                             number=number, body=body)
        if sms_response is True:
            speaker.speak(text=f"Message has been sent {models.env.title}!")
        else:
            speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to send the email. "
                               f"{sms_response}")
        return
    elif shared.called_by_offline:  # Number is not present but called by offline
        speaker.speak(text="SMS format should be::send some message to some number or name.")
        return
    if not number:  # Number is not present
        speaker.speak(text=f"Please tell me a number {models.env.title}!", run=True)
        if not (number := listener.listen()):
            return
        if 'exit' in number or 'quit' in number or 'Xzibit' in number:
            return
    if not body:
        speaker.speak(text=f"What would you like to send {models.env.title}?", run=True)
        if not (body := listener.listen()):
            return
        if 'exit' in body or 'quit' in body or 'Xzibit' in body:
            return
    speaker.speak(text=f'{body} to {number}. Do you want me to proceed?', run=True)
    if converted := listener.listen():
        if word_match.word_match(phrase=converted, match_list=keywords.keywords['ok']):
            logger.info("{body} -> {number}".format(body=body, number=number))
            sms_response = communicator.send_sms(user=models.env.gmail_user, password=models.env.gmail_pass,
                                                 number=number, body=body)
            if sms_response is True:
                speaker.speak(text=f"Message has been sent {models.env.title}!")
            else:
                speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to send the email. "
                                   f"{sms_response}")
        else:
            speaker.speak(text=f"Message will not be sent {models.env.title}!")


def initiate_email(body: str, to: str) -> None:
    """Sends an email to the contact name receive after looking it up in the contacts.yaml file.

    Args:
        body: Text that has to be sent.
        to: Target name to fetch from the contacts file..

    See Also:
          - Requires ``contacts.yaml`` to be present in ``fileio`` directory.
    """
    to = extract_contacts(name=to, key='email')
    if not to:
        logger.error("Contact file missing or '%s' not found in contact file.", to)
        support.no_env_vars()
        return

    if body and shared.called_by_offline:  # Body is present and called by offline
        logger.info("'%s' -> '%s'", body, to)
        mail_response = communicator.send_email(body=body, recipient=to)
        if mail_response is True:
            speaker.speak(text=f"Email has been sent {models.env.title}!")
        else:
            speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to send the email. "
                               f"{mail_response}")
        return
    elif shared.called_by_offline:  # Number is not present but called by offline
        speaker.speak(text="Email format should be::send some message to some email address.")
        return

    if not body:
        speaker.speak(text=f"What would you like to send {models.env.title}?", run=True)
        if not (body := listener.listen()):
            return
        if 'exit' in body or 'quit' in body or 'Xzibit' in body:
            return

    speaker.speak(text=f'{body} to {to}. Do you want me to proceed?', run=True)
    if converted := listener.listen():
        if word_match.word_match(phrase=converted, match_list=keywords.keywords['ok']):
            logger.info("'%s' -> '%s'", body, to)
            mail_response = communicator.send_email(body=body, recipient=to)
            if mail_response is True:
                speaker.speak(text=f"Email has been sent {models.env.title}!")
            else:
                speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to send the email. "
                                   f"{mail_response}")
        else:
            speaker.speak(text=f"Email will not be sent {models.env.title}!")
