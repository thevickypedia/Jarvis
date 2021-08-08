from datetime import datetime
from os import listdir, remove, system
from threading import Thread

from gmailconnector.send_sms import Messenger

directory = 'reminder'  # dir need not be '../reminder' as the Thread is triggered by jarvis.py which is in root dir


class Reminder(Thread):
    """Class to initiate ``Reminder`` as a super class to run in background.

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
        """Triggers the reminder notification when the hours and minutes match the current time."""
        file_name = f'{self.hours}_{self.minutes}_{self.am_pm}|{self.message.replace(" ", "_")}.lock'
        files = listdir(directory)
        while True:
            now = datetime.now()
            am_pm = now.strftime("%p")
            minute = now.strftime("%M")
            hour = now.strftime("%I")
            if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                body = self.message
                subject = "REMINDER from Jarvis"
                Messenger(gmail_user=environ.get('gmail_user'), gmail_pass=environ.get('gmail_pass'),
                          phone_number=environ.get('phone'), subject=subject, message=body).send_sms()
                system(f"""osascript -e 'display notification "{body}" with title "{subject}"'""")
                remove(f"{directory}/{file_name}")
                return


if __name__ == '__main__':
    from os import environ

    from dotenv import load_dotenv

    env_file_path = '../.env'
    load_dotenv(dotenv_path=env_file_path)

    Reminder(hours=10, minutes=30, am_pm='AM', message='JARVIS::Test reminder from Reminder module.')
