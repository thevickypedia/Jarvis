import os
import random

from modules.audio import speaker
from modules.conditions import conversation
from modules.utils import support


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
            level = support.extract_nos(input_=phrase, method=int) or 50
    support.flush_screen()
    level = round((8 * level) / 100)
    os.system(f'osascript -e "set Volume {level}"')
    if phrase:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}!")
