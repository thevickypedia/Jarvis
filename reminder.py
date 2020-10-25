import os
from datetime import datetime
from threading import Thread

directory = 'reminder'


class Reminder(Thread):
    def __init__(self, hours, minutes, am_pm, message):
        super(Reminder, self).__init__()
        if hours and minutes and am_pm:
            self.hours = hours
            self.minutes = minutes
            self.am_pm = am_pm
            self.message = message
            self.reminder_state = True
        else:
            remove = os.listdir(directory)
            for file in remove:
                (os.remove(f"{directory}/{file}") if file != 'dummy.lock' else None)
            self.reminder_state = False
            exit(0)

    def run(self):
        try:
            while self.reminder_state:
                now = datetime.now()
                am_pm = now.strftime("%p")
                minute = now.strftime("%M")
                hour = now.strftime("%I")
                files = os.listdir(directory)
                file_name = f"{hour}_{minute}_{am_pm}.lock"
                if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                    import smtplib
                    # Establish a secure session with gmail's outgoing SMTP server using your gmail account
                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(user=os.getenv('gmail_user'), password=os.getenv('gmail_pass'))
                    from_ = os.getenv('gmail_user')
                    to = f"{os.getenv('remind')}@tmomail.net"
                    body = self.message
                    subject = "REMINDER from Jarvis"
                    # Send text message through SMS gateway of destination number
                    message = (f"From: {from_}\r\n" + f"To: {to}\r\n" + f"Subject: {subject}\r\n" + "\r\r\n\n" + body)
                    server.sendmail(from_, to, message)
                    server.close()
                    os.remove(f"{directory}/{file_name}")
                    return
        except FileNotFoundError:
            return


if __name__ == '__main__':
    Reminder('01', '21', 'PM', 'Finish pending tasks').start()
