import subprocess
from threading import Thread
import time


class Alarm(Thread):
    def __init__(self, hours, minutes):
        super(Alarm, self).__init__()
        self.hours = int(hours)
        self.minutes = int(minutes)
        self.alarm_state = True

    def run(self):
        while self.alarm_state:
            now = time.localtime()
            if now.tm_hour == self.hours and now.tm_min == self.minutes:
                subprocess.call(["open", "Early Riser.mp3"])
                return


if __name__ == '__main__':
    Alarm(10, 10).start()
