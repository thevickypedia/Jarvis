# noinspection PyUnresolvedReferences
"""Module for speaker and voice options.

>>> Speaker

"""

import sys

import pyttsx3

from executors.custom_logger import logger
from modules.utils.globals import text_spoken

audio_driver = pyttsx3.init()


def speak(text: str = None, run: bool = False) -> None:
    """Calls ``audio_driver.say`` to speak a statement from the received text.

    Args:
        text: Takes the text that has to be spoken as an argument.
        run: Takes a boolean flag to choose whether to run the ``audio_driver.say`` loop.
    """
    if text:
        audio_driver.say(text=text)
        text = text.replace('\n', '\t').strip()
        logger.info(f'Response: {text}')
        logger.info(f'Speaker called by: {sys._getframe(1).f_code.co_name}')  # noqa
        sys.stdout.write(f"\r{text}")
        text_spoken['text'] = text
    if run:
        audio_driver.runAndWait()
