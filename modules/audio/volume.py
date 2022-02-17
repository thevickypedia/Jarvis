import os
import random
import re
from datetime import datetime
from threading import Thread

from executors import display_functions
from modules.audio import speaker
from modules.conditions import conversation
from modules.utils import support


def switch_volumes() -> None:
    """Automatically puts the Mac on sleep and sets the volume to 25% at 9 PM and 50% at 6 AM."""
    hour = int(datetime.now().strftime('%H'))
    locker = """osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'"""
    if 20 >= hour >= 7:
        volume(level=50)
    elif hour >= 21 or hour <= 6:
        volume(level=30)
        Thread(target=display_functions.decrease_brightness).start()
        os.system(locker)


def volume(phrase: str = None, level: int = None) -> None:
    """Controls volume from the numbers received. Defaults to 50%.

    Args:
        phrase: Takes the phrase spoken as an argument.
        level: Level of volume to which the system has to set.
    """
    if not level:
        phrase_lower = phrase.lower()
        if 'mute' in phrase_lower:
            level = 0
        elif 'max' in phrase_lower or 'full' in phrase_lower:
            level = 100
        else:
            level = re.findall(r'\b\d+\b', phrase)  # gets integers from string as a list
            level = int(level[0]) if level else 50  # converted to int for volume
    support.flush_screen()
    level = round((8 * level) / 100)
    os.system(f'osascript -e "set Volume {level}"')
    if phrase:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}!")
