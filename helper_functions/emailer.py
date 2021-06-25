from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import path

from boto3 import client


class Emailer:
    """Initiates Emailer object to send an email to defined recipient from a defined sender with or without attachments.

    >>> Emailer

    """

    def __init__(self, sender, recipient):
        """Initiates sender and recipient to initiate the class.

        Args:
            sender: Sender email address verified in AWS SES.
            recipient: Sender email address verified in AWS SES.
        """
        self.sender = sender
        self.recipients = recipient

    def create_multipart_message(self, title: str, text: str = None, html: str = None,
                                 attachments: list = None) -> MIMEMultipart:
        """Creates an email message with multiple parts.

        Args:
            title: Subject line on the email.
            text: Body of the email.
            html: HTML format of the email.
            attachments: Attachment that has to be added to the email.

        Returns:
            Created multipart message.

        """
        multipart_content_subtype = 'alternative' if text and html else 'mixed'
        msg = MIMEMultipart(multipart_content_subtype)
        msg['Subject'] = title
        msg['From'] = f"Jarvis <{self.sender}>"
        recipients = [self.recipients]
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

    def send_mail(self, title: str, text: str = None, html: str = None, attachments: list = None) -> dict:
        """Sends an mail to all recipients. The sender needs to be a verified email in SES.

        Args:
            title: Subject line on the email.
            text: Body of the email.
            html: HTML format of the email.
            attachments: Attachment that has to be added to the email.
        """
        msg = self.create_multipart_message(title, text, html, attachments)
        ses_client = client('ses')  # Use your settings here
        return ses_client.send_raw_email(
            Source=msg.get('From'),
            Destinations=[msg.get('To')],
            RawMessage={'Data': msg.as_string()}
        )
