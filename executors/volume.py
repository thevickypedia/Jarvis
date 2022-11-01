import os
import random

from modules.audio import speaker
from modules.conditions import conversation
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import support
from modules.windows import win_volume


def volume(phrase: str = None, level: int = None) -> None:
    """Controls volume from the numbers received. Defaults to 50%.

    See Also:
        SetVolume for Windows: https://rlatour.com/setvol/

    Args:
        phrase: Takes the phrase spoken as an argument.
        level: Level of volume to which the system has to set.
    """
    if not level and phrase:
        if 'unmute' in phrase.lower():
            level = models.env.volume
        elif 'mute' in phrase.lower():
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
