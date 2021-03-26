import os
from datetime import datetime
from platform import system
from random import choice
from subprocess import call
from threading import Thread

directory = 'alarm'  # dir need not be '../alarm' as the Thread is triggered by jarvis.py which is in root dir


class Alarm(Thread):
    def __init__(self, hours, minutes, am_pm):
        super(Alarm, self).__init__()
        self.hours = hours
        self.minutes = minutes
        self.am_pm = am_pm

    def run(self):
        operating_system = system()
        music_dir = "mp3"
        tone = choice(os.listdir(music_dir))
        files = os.listdir(directory)
        file_name = f"{self.hours}_{self.minutes}_{self.am_pm}.lock"
        while True:
            now = datetime.now()
            am_pm = now.strftime("%p")
            minute = now.strftime("%M")
            hour = now.strftime("%I")
            if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                if operating_system == 'Darwin':
                    call(["open", f"{music_dir}/{tone}"])
                elif operating_system == 'Windows':
                    location = os.path.abspath(os.getcwd())
                    os.system(f'start wmplayer "{location}\\{music_dir}\\{tone}"')
                os.remove(f"{directory}/{file_name}")
                return
