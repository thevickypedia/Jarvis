import os
import random
import subprocess
import time
from threading import Thread


class Alarm(Thread):
    def __init__(self, hours, minutes):
        super(Alarm, self).__init__()
        if hours and minutes:
            self.hours = int(hours)
            self.minutes = int(minutes)
            self.alarm_state = True

    def run(self):
        try:
            directory = "mp3"
            tone = random.choice(os.listdir(directory))
            while self.alarm_state:
                now = time.localtime()
                if now.tm_hour == self.hours and now.tm_min == self.minutes:
                    subprocess.call(["open", f"{directory}/{tone}"])
                    return
        except FileNotFoundError:
            return

    def kill_alarm(self):
        self.alarm_state = False


if __name__ == '__main__':
    Alarm(10, 10).start()
