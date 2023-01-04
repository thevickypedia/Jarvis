import os
import random
import sys
from threading import Timer
from typing import NoReturn

from modules.audio import speaker
from modules.conditions import conversation
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import shared, support, util
from modules.windows import win_volume


def main_volume(level: int) -> NoReturn:
    """Changes system volume.

    Args:
        level: Takes the volume level as an argument.
    """
    logger.info(f"Set system volume to {level!r}")
    if models.settings.os == "Darwin":
        os.system(f'osascript -e "set Volume {round((8 * level) / 100)}"')
    elif models.settings.os == "Windows":
        win_volume.set_volume(level=level)
    else:
        os.system(f"amixer sset 'Master' {level}% /dev/null 2>&1")


def speaker_volume(level: int) -> NoReturn:
    """Changes volume just for Jarvis' speech without disturbing the system volume.

    Args:
        level: Takes the volume level as an argument.
    """
    logger.info(f"Set jarvis' volume to {level!r}")
    models.audio_driver.setProperty('volume', level / 100)


def volume(phrase: str = None, level: int = None) -> NoReturn:
    """Controls volume from the numbers received. Defaults to 50%.

    See Also:
        SetVolume for Windows: https://rlatour.com/setvol/

    Args:
        phrase: Takes the phrase spoken as an argument.
        level: Level of volume to which the system has to set.
    """
    response = None
    reset_after = None
    if not level and phrase:
        response = random.choice(conversation.acknowledgement)
        phrase = phrase.lower()
        if 'unmute' in phrase:
            level = models.env.volume
        elif 'mute' in phrase:
            if 'for' in phrase:
                reset_after = support.delay_calculator(phrase=phrase)
                response += f" Muted for {util.time_converter(second=reset_after)}"
            level = 0
        elif 'max' in phrase or 'full' in phrase:
            level = 100
        else:
            level = support.extract_nos(input_=phrase, method=int)
    if level is None:
        level = models.env.volume
    phrase = phrase or ""
    caller = sys._getframe(1).f_code.co_name  # noqa
    if 'master' in phrase or 'main' in phrase or caller in ('alarm_executor', 'starter'):
        if reset_after:
            logger.info(f"All volume will be set to {models.env.volume} after "
                        f"{util.time_converter(second=reset_after)}")
            Timer(interval=reset_after, function=main_volume, args=(models.env.volume,)).start()
            Timer(interval=reset_after, function=speaker_volume, args=(models.env.volume,)).start()
        main_volume(level=level)
        speaker_volume(level=level)
    else:
        if shared.called_by_offline or 'system' in phrase:
            if reset_after:
                logger.info(f"Main volume will be set to {models.env.volume} after "
                            f"{util.time_converter(second=reset_after)}")
                Timer(interval=reset_after, function=main_volume, args=(models.env.volume,)).start()
            main_volume(level=level)
        else:
            if reset_after:
                logger.info(f"Jarvis' volume will be set to {models.env.volume} after "
                            f"{util.time_converter(second=reset_after)}")
                Timer(interval=reset_after, function=speaker_volume, args=(models.env.volume,)).start()
            speaker_volume(level=level)
    if response:
        speaker.speak(text=response)
