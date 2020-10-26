import os
import platform
import random
import subprocess
from datetime import datetime
from threading import Thread

directory = 'alarm'


class Alarm(Thread):
    def __init__(self, hours, minutes, am_pm):
        super(Alarm, self).__init__()
        if hours and minutes and am_pm:
            self.hours = hours
            self.minutes = minutes
            self.am_pm = am_pm
            self.alarm_state = True
        else:
            [os.remove(f"{directory}/{file}") if file != 'dummy.lock' else None for file in os.listdir(directory)]
            self.alarm_state = False
            os._exit(0)

    def run(self):
        try:
            operating_system = platform.system()
            music_dir = "mp3"
            tone = random.choice(os.listdir(music_dir))
            while self.alarm_state:
                now = datetime.now()
                am_pm = now.strftime("%p")
                minute = now.strftime("%M")
                hour = now.strftime("%I")
                files = os.listdir(directory)
                file_name = f"{hour}_{minute}_{am_pm}.lock"
                if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                    if operating_system == 'Darwin':
                        subprocess.call(["open", f"{music_dir}/{tone}"])
                    elif operating_system == 'Windows':
                        location = os.path.abspath(os.getcwd())
                        os.system(f'start wmplayer "{location}\\{music_dir}\\{tone}"')
                    os.remove(f"{directory}/{file_name}")
                    return
        except FileNotFoundError:
            return


if __name__ == '__main__':
    Alarm('05', '57', 'pm').start()
