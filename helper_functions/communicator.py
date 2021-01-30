"""todo: remove the whole thing below and make it as an SQS subscription.
   todo: Using that the current pull model can be changed to push model."""

import email
import imaplib
import sys

from logger import logger


def gmail_offline(username, password, commander):
    """Reads UNREAD emails from the dedicated account for offline communication with Jarvis"""
    # noinspection PyBroadException
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(username, password)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError as TimeOut:
        logger.fatal(f"Offline Communicator::TimeOut Error.\n{TimeOut}")
        return 'TimeOut ERROR'
    except:  # live with bad way of exception handling because imaplib does not have a method/function for it
        imap_error = sys.exc_info()[0]
        logger.fatal(f'Offline Communicator::Login Error.\n{imap_error}')
        return 'Login ERROR'

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')
    if return_code == 'OK':
        for _ in messages[0].split():
            n = n + 1
    elif return_code != 'OK':
        logger.fatal(f"Offline Communicator::Search Error.\n{return_code}")
        return 'Search ERROR'
    elif n == 0:
        return
    else:
        for nm in messages[0].split():
            ignore, mail_data = mail.fetch(nm, '(RFC822)')
            for response_part in mail_data:
                if isinstance(response_part, tuple):
                    original_email = email.message_from_bytes(response_part[1])
                    sender = (original_email['From']).split('<')[-1].split('>')[0].strip()
                    if sender == commander:
                        # noinspection PyUnresolvedReferences
                        email_message = email.message_from_string(mail_data[0][1].decode('utf-8'))
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode('utf-8').strip()
                                return body
                    else:
                        logger.fatal(f'Email was received from {sender}')
