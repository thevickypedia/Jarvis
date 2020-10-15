import os
import platform
import random
import subprocess
from datetime import datetime
from threading import Thread


class Alarm(Thread):
    def __init__(self, hours, minutes, am_pm):
        super(Alarm, self).__init__()
        if hours and minutes and am_pm:
            self.hours = hours
            self.minutes = minutes
            self.am_pm = am_pm
            self.alarm_state = True

    def run(self):
        try:
            operating_system = platform.system()
            directory = "mp3"
            tone = random.choice(os.listdir(directory))
            while self.alarm_state:
                now = datetime.now()
                am_pm = now.strftime("%p")
                minute = now.strftime("%M")
                hour = now.strftime("%I")
                files = os.listdir('lock_files')
                file_name = f"{hour}_{minute}_{am_pm}.lock"
                if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                    if operating_system == 'Darwin':
                        subprocess.call(["open", f"{directory}/{tone}"])
                    elif operating_system == 'Windows':
                        location = os.path.abspath(os.getcwd())
                        os.system(f'start wmplayer "{location}\\{directory}\\{tone}"')
                    os.remove(f"lock_files/{file_name}")
                    return
        except FileNotFoundError:
            return

    def kill_alarm(self):
        self.alarm_state = False


if __name__ == '__main__':
    Alarm('05', '57', 'pm').start()
