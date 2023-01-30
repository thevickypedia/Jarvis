import os
import random
import subprocess
from threading import Thread

from jarvis.modules.audio import speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.models import models
from jarvis.modules.utils import util

POWERSHELL = '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,' + '{l}' + ')'


def brightness(phrase: str):
    """Pre-process to check the phrase received and call the appropriate brightness function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    speaker.speak(text=random.choice(conversation.acknowledgement))
    if 'set' in phrase:
        level = util.extract_nos(input_=phrase, method=int)
        if level is None:
            level = 50
        Thread(target=set_brightness, args=[level]).start()
    elif 'decrease' in phrase or 'reduce' in phrase or 'lower' in phrase or \
            'dark' in phrase or 'dim' in phrase:
        Thread(target=decrease_brightness).start()
    elif 'increase' in phrase or 'bright' in phrase or 'max' in phrase or \
            'brighten' in phrase or 'light up' in phrase:
        Thread(target=increase_brightness).start()


def increase_brightness() -> None:
    """Increases the brightness to maximum in macOS."""
    if models.settings.os == "Darwin":
        for _ in range(16):
            os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")
    elif models.settings.os == "Windows":
        subprocess.run(["powershell", POWERSHELL.format(l=100)])
    else:
        os.system(f"echo {models.env.root_password} | sudo -S brightnessctl s 100 > /dev/null")


def decrease_brightness() -> None:
    """Decreases the brightness to bare minimum in macOS."""
    if models.settings.os == "Darwin":
        for _ in range(16):
            os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")
    elif models.settings.os == "Windows":
        subprocess.run(["powershell", POWERSHELL.format(l=0)])
    else:
        os.system(f"echo {models.env.root_password} | sudo -S brightnessctl s 0 > /dev/null")


def set_brightness(level: int) -> None:
    """Set brightness to a custom level.

    - | Since Jarvis uses in-built apple script (for macOS), the only way to achieve this is to set the brightness to
      | absolute minimum/maximum and increase/decrease the required % from there.

    Args:
        level: Percentage of brightness to be set.
    """
    if models.settings.os == "Darwin":
        level = round((16 * int(level)) / 100)
        decrease_brightness()
        for _ in range(level):
            os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")
    elif models.settings.os == "Windows":
        subprocess.run(["powershell", POWERSHELL.format(l=level)])
    else:
        os.system(f"echo {models.env.root_password} | sudo -S brightnessctl s {level} > /dev/null")
