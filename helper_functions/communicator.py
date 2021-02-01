"""todo: remove the whole thing below and make it as an SQS subscription.
   todo: Using that the current pull model can be changed to push model."""

import email
import imaplib
import socket
import sys

from logger import logger


def gmail_offline(username, password, commander):
    """Reads UNREAD emails from the dedicated account for offline communication with Jarvis"""
    socket.setdefaulttimeout(10)  # set default timeout for new socket connections to 10 seconds
    # noinspection PyBroadException
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(username, password)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError as TimeOut:
        logger.fatal(f"Offline Communicator::TimeOut Error. Current TimeOut: {socket.getdefaulttimeout()}\n{TimeOut}")
        return 'TimeOut ERROR'
    except:  # live with bad way of exception handling as imaplib doesn't have a method/function for "imaplib.error"
        imap_error = sys.exc_info()[0]
        logger.fatal(f'Offline Communicator::Login Error.\n{imap_error}')
        return 'Login ERROR'
    socket.setdefaulttimeout(None)  # revert default timeout for new socket connections to None

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')
    if return_code == 'OK':
        for _ in messages[0].split():
            n = n + 1
    elif return_code != 'OK':
        logger.fatal(f"Offline Communicator::Search Error.\n{return_code}")
        return 'Search ERROR'
    if n == 0:
        return
    else:
        for bytecode in messages[0].split():
            ignore, mail_data = mail.fetch(bytecode, '(RFC822)')
            for response_part in mail_data:
                if isinstance(response_part, tuple):
                    original_email = email.message_from_bytes(response_part[1])
                    sender = (original_email['From']).split('<')[-1].split('>')[0].strip()
                    if sender == commander:
                        # noinspection PyUnresolvedReferences
                        email_message = email.message_from_string(mail_data[0][1].decode('utf-8'))
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                                body = part.get_payload(decode=True).decode('utf-8').strip()
                                mail.store(bytecode, "+FLAGS", "\\Deleted")  # marks email as deleted
                                mail.expunge()  # DELETES (not send to Trash) the email permanently
                                mail.close()  # closes imap lib
                                mail.logout()
                                return body
                    else:
                        logger.fatal(f'Email was received from {sender}')


if __name__ == '__main__':
    import os

    offline_receive_user = os.getenv('offline_receive_user')
    offline_receive_pass = os.getenv('offline_receive_pass')
    offline_sender = os.getenv('offline_sender')
    print(gmail_offline(offline_receive_user, offline_receive_pass, offline_sender))
