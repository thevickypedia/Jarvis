import os
from datetime import datetime
from threading import Thread


class Reminder(Thread):
    def __init__(self, hours, minutes, am_pm):
        super(Reminder, self).__init__()
        if hours and minutes and am_pm:
            self.hours = hours
            self.minutes = minutes
            self.am_pm = am_pm
            self.reminder_state = True
        else:
            remove = os.listdir('reminder_lock')
            for file in remove:
                (os.remove(f"reminder_lock/{file}") if file != 'dummy.lock' else None)
            self.reminder_state = False
            exit(0)

    def run(self):
        try:
            while self.reminder_state:
                now = datetime.now()
                am_pm = now.strftime("%p")
                minute = now.strftime("%M")
                hour = now.strftime("%I")
                files = os.listdir('lock_files')
                file_name = f"{hour}_{minute}_{am_pm}.lock"
                if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                    # TODO: trigger reminder message through SMS gateway of destination number
                    os.remove(f"reminder_lock/{file_name}")
                    return
        except FileNotFoundError:
            return


if __name__ == '__main__':
    Reminder('05', '57', 'pm').start()
