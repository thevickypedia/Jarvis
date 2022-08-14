import os
import random

from executors.logger import logger
from modules.audio import speaker, win_volume
from modules.conditions import conversation
from modules.models import models
from modules.utils import support


def volume(phrase: str = None, level: int = None) -> None:
    """Controls volume from the numbers received. Defaults to 50%.

    See Also:
        SetVolume for Windows: https://rlatour.com/setvol/

    Args:
        phrase: Takes the phrase spoken as an argument.
        level: Level of volume to which the system has to set.
    """
    if not level and phrase:
        if 'mute' in phrase.lower():
            level = 0
        elif 'max' in phrase.lower() or 'full' in phrase.lower():
            level = 100
        else:
            level = support.extract_nos(input_=phrase, method=int)
            if level is None:
                level = models.env.volume
    logger.info(f"Set volume to {level}")
    if models.settings.macos:
        os.system(f'osascript -e "set Volume {round((8 * level) / 100)}"')
    else:
        win_volume.set_volume(level=level)
    if phrase:
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}!")
