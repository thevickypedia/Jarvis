from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ, path

from boto3 import client

from helper_functions.aws_clients import AWSClients

aws = AWSClients()


def create_multipart_message(title: str, text: str = None, html: str = None, attachments: list = None) -> MIMEMultipart:
    """Creates an email message with multiple parts.

    Args:
        title: Subject line on the email.
        text: Body of the email.
        html: HTML format of the email.
        attachments: Attachment that has to be added to the email.

    Returns: Created multipart message.

    """
    multipart_content_subtype = 'alternative' if text and html else 'mixed'
    msg = MIMEMultipart(multipart_content_subtype)
    msg['Subject'] = title
    msg['From'] = f"Jarvis <{environ.get('gmail_user') or aws.gmail_user()}>"
    recipients = [environ.get('robinhood_user') or aws.robinhood_user()]
    msg['To'] = ', '.join(recipients)
    if text:
        part = MIMEText(text, 'plain')
        msg.attach(part)
    if html:
        part = MIMEText(html, 'html')
        msg.attach(part)
    for attachment in attachments or []:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read())
            part.add_header('Content-Disposition', 'attachment', filename=path.basename(attachment))
            msg.attach(part)
    return msg


def send_mail(title: str, text: str = None, html: str = None, attachments: list = None) -> dict:
    """Sends an mail to all recipients. The sender needs to be a verified email in SES.

    Args:
        title: Subject line on the email.
        text: Body of the email.
        html: HTML format of the email.
        attachments: Attachment that has to be added to the email.

    """
    msg = create_multipart_message(title, text, html, attachments)
    ses_client = client('ses')  # Use your settings here
    return ses_client.send_raw_email(
        Source=msg.get('From'),
        Destinations=[msg.get('To')],
        RawMessage={'Data': msg.as_string()}
    )


if __name__ == '__main__':
    # the below is only for testing purpose
    title_ = 'Intruder Alert'
    text_ = None
    body_ = """<html><head></head><body><h2>Conversation of Intruder:</h2><br>He's home alone.
               <h2>Attached is a photo of the intruder.</h2>"""
    attachments_ = ['../threat/image_of_intruder.jpg']
    response_ = send_mail(title_, text_, body_, attachments_)
    print(response_)
