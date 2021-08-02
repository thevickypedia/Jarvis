from datetime import datetime
from os import listdir, remove, system
from subprocess import call
from threading import Thread
from time import sleep

directory = 'alarm'  # dir need not be '../alarm' as the Thread is triggered by jarvis.py which is in root dir


class Alarm(Thread):
    """Class to initiate Alarm as a super class to run in background.

    >>> Alarm

    """

    def __init__(self, hours, minutes, am_pm):
        """Initiates super class.

        Args:
            hours: Hour value of current time.
            minutes: Minutes value of current time.
            am_pm: Indicates AM or PM of the day.
        """
        super(Alarm, self).__init__()
        self.hours = hours
        self.minutes = minutes
        self.am_pm = am_pm

    def run(self) -> None:
        """Plays mp3/alarm.mp3 tone when the hours and minutes match the current time."""
        music_dir = "mp3"
        tone = "alarm.mp3"
        files = listdir(directory)
        file_name = f"{self.hours}_{self.minutes}_{self.am_pm}.lock"
        while True:
            now = datetime.now()
            am_pm = now.strftime("%p")
            minute = now.strftime("%M")
            hour = now.strftime("%I")
            if hour == self.hours and minute == self.minutes and am_pm == self.am_pm and file_name in files:
                system(f'osascript -e "set Volume {round((8 * 100) / 100)}"')
                call(["open", f"{music_dir}/{tone}"])
                sleep(200)
                system(f'osascript -e "set Volume {round((8 * 50) / 100)}"')
                remove(f"{directory}/{file_name}")
                return
