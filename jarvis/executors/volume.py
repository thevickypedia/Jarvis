import random
import sys
from typing import NoReturn

from pyvolume import pyvolume

from jarvis.modules.audio import speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, util


def main_volume(level: int) -> NoReturn:
    """Changes system volume.

    Args:
        level: Takes the volume level as an argument.
    """
    pyvolume(level=level, debug=True, logger=logger)


def speaker_volume(level: int) -> NoReturn:
    """Changes volume just for Jarvis' speech without disturbing the system volume.

    Args:
        level: Takes the volume level as an argument.
    """
    if models.audio_driver:
        logger.info("Jarvis' volume has been set to %d" % level + "%")  # % is mandatory because of string concatenation
        models.audio_driver.setProperty('volume', level / 100)
    else:
        logger.warning("Setting Jarvis' volume is not available for speech-synthesis")


def volume(phrase: str = None, level: int = None) -> NoReturn:
    """Controls volume from the numbers received. Defaults to 50%.

    See Also:
        SetVolume for Windows: https://rlatour.com/setvol/

    Args:
        phrase: Takes the phrase spoken as an argument.
        level: Level of volume to which the system has to set.
    """
    response = None
    if not level and phrase:
        response = random.choice(conversation.acknowledgement)
        phrase = phrase.lower()
        if 'unmute' in phrase:
            level = models.env.volume
        elif 'mute' in phrase:
            level = 0
        elif 'max' in phrase or 'full' in phrase:
            level = 100
        else:
            level = util.extract_nos(input_=phrase, method=int)
    if level is None:
        level = models.env.volume
    phrase = phrase or ""
    caller = sys._getframe(1).f_code.co_name  # noqa
    if 'master' in phrase or 'main' in phrase or caller in ('executor', 'starter'):
        main_volume(level=level)
        speaker_volume(level=level)
    else:
        if shared.called_by_offline or 'system' in phrase:
            main_volume(level=level)
        else:
            speaker_volume(level=level)
    if response:
        speaker.speak(text=response)
