import os
import random
from threading import Thread

from modules.audio import speaker
from modules.conditions import conversation
from modules.models import models
from modules.utils import support

env = models.env


def brightness(phrase: str):
    """Pre-process to check the phrase received and call the appropriate brightness function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not env.mac:
        support.missing_windows_features()
        return
    phrase = phrase.lower()
    speaker.speak(text=random.choice(conversation.acknowledgement))
    if 'set' in phrase:
        level = support.extract_nos(input_=phrase, method=int) or 50
        Thread(target=set_brightness, args=[level]).start()
    elif 'decrease' in phrase or 'reduce' in phrase or 'lower' in phrase or \
            'dark' in phrase or 'dim' in phrase:
        Thread(target=decrease_brightness).start()
    elif 'increase' in phrase or 'bright' in phrase or 'max' in phrase or \
            'brighten' in phrase or 'light up' in phrase:
        Thread(target=increase_brightness).start()


def increase_brightness() -> None:
    """Increases the brightness to maximum in macOS."""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def decrease_brightness() -> None:
    """Decreases the brightness to bare minimum in macOS."""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")


def set_brightness(level: int) -> None:
    """Set brightness to a custom level.

    - | Since Jarvis uses in-built apple script, the only way to achieve this is to set the brightness to absolute
      | minimum/maximum and increase/decrease the required % from there.

    Args:
        level: Percentage of brightness to be set.
    """
    level = round((32 * int(level)) / 100)
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")
    for _ in range(level):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")
