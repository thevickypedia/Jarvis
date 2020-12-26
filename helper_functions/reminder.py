import os
import platform
import smtplib
from datetime import datetime
from threading import Thread

from helper_functions.aws_clients import AWSClients

aws = AWSClients()
directory = 'reminder'  # dir need not be '../reminder' as the Thread is triggered by jarvis.py which is in root dir
operating_system = platform.system()


class Reminder(Thread):
    def __init__(self, hours, minutes, am_pm, message):
        super(Reminder, self).__init__()
        if hours and minutes and am_pm:
            self.hours = hours
            self.minutes = minutes
            self.am_pm = am_pm
            self.message = message
        else:
            os._exit(0)

    def run(self):
        file_name = f'{self.hours}_{self.minutes}_{self.am_pm}|{self.message.replace(" ", "_")}.lock'
        files = os.listdir(directory)
        while True:
            now = datetime.now()
            am_pm = now.strftime("%p")
            minute = now.strftime("%M")
            hour = now.strftime("%I")
            if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                # Establish a secure session with gmail's outgoing SMTP server using your gmail account
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                gmail_user = os.getenv('gmail_user') or aws.gmail_user()
                gmail_pass = os.getenv('gmail_pass') or aws.gmail_pass()
                remind = os.getenv('phone') or aws.phone()
                server.login(user=gmail_user, password=gmail_pass)
                from_ = gmail_user
                to = f"{remind}@tmomail.net"
                body = self.message
                subject = "REMINDER from Jarvis"
                # Send text message through SMS gateway of destination number
                message = (f"From: {from_}\r\n" + f"To: {to}\r\n" + f"Subject: {subject}\r\n" + "\r\r\n\n" + body)
                server.sendmail(from_, to, message)
                server.close()
                if operating_system == 'Darwin':
                    os.system(f"""osascript -e 'display notification "{body}" with title "{subject}"'""")
                elif operating_system == 'Windows':
                    from win10toast import ToastNotifier
                    ToastNotifier().show_toast(subject, body)
                os.remove(f"{directory}/{file_name}")
                return
