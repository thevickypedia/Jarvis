from datetime import datetime
from os import listdir, remove, system
from smtplib import SMTP
from threading import Thread

from creds import Credentials

directory = 'reminder'  # dir need not be '../reminder' as the Thread is triggered by jarvis.py which is in root dir


class Reminder(Thread):
    """Class to initiate Alarm as a super class to run in background.

    >>> Reminder

    """

    def __init__(self, hours, minutes, am_pm, message):
        """Initiates super class.

        Args:
            hours: Hour value of current time.
            minutes: Minutes value of current time.
            am_pm: Indicates AM or PM of the day.
            message: Message that has to be reminded with.
        """
        super(Reminder, self).__init__()
        self.hours = hours
        self.minutes = minutes
        self.am_pm = am_pm
        self.message = message

    def run(self) -> None:
        """Triggers the Reminder class in a thread."""
        file_name = f'{self.hours}_{self.minutes}_{self.am_pm}|{self.message.replace(" ", "_")}.lock'
        files = listdir(directory)
        while True:
            now = datetime.now()
            am_pm = now.strftime("%p")
            minute = now.strftime("%M")
            hour = now.strftime("%I")
            if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                cred = Credentials().get()
                # Establish a secure session with gmail's outgoing SMTP server using your gmail account
                server = SMTP("smtp.gmail.com", 587)
                server.starttls()
                gmail_user = cred.get('gmail_user')
                gmail_pass = cred.get('gmail_pass')
                remind = cred.get('phone')
                server.login(user=gmail_user, password=gmail_pass)
                from_ = gmail_user
                to = f"{remind}@tmomail.net"
                body = self.message
                subject = "REMINDER from Jarvis"
                # Send text message through SMS gateway of destination number
                message = (f"From: {from_}\n" + f"To: {to}\n" + f"Subject: {subject}\n" + "\n\n" + body)
                server.sendmail(from_, to, message)
                server.close()
                system(f"""osascript -e 'display notification "{body}" with title "{subject}"'""")
                remove(f"{directory}/{file_name}")
                return
