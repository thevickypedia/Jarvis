# noinspection PyUnresolvedReferences
"""Module for speaker and voice options.

>>> Speaker

"""
import os.path
import sys

import pyttsx3
import yaml

from executors.logger import logger
from modules.conditions import conversation, keywords
from modules.utils.globals import text_spoken

audio_driver = pyttsx3.init()

KEYWORDS = [__keyword for __keyword in dir(keywords) if not __keyword.startswith('__')]
CONVERSATION = [__conversation for __conversation in dir(conversation) if not __conversation.startswith('__')]
FUNCTIONS_TO_TRACK = KEYWORDS + CONVERSATION


def speak(text: str = None, run: bool = False) -> None:
    """Calls ``audio_driver.say`` to speak a statement from the received text.

    Args:
        text: Takes the text that has to be spoken as an argument.
        run: Takes a boolean flag to choose whether to run the ``audio_driver.say`` loop.
    """
    caller = sys._getframe(1).f_code.co_name  # noqa
    if text:
        audio_driver.say(text=text)
        text = text.replace('\n', '\t').strip()
        logger.info(f'Response: {text}')
        logger.info(f'Speaker called by: {caller}')
        sys.stdout.write(f"\r{text}")
        text_spoken['text'] = text
    if run:
        audio_driver.runAndWait()
    frequently_used(function_name=caller) if caller in FUNCTIONS_TO_TRACK else None


def frequently_used(function_name: str) -> None:
    """Writes the function called and the number of times into a yaml file.

    Args:
        function_name: Name of the function that called the speaker.

    See Also:
        - This function does not have purpose, but to analyze and re-order the conditions' module at a later time.
    """
    if os.path.isfile('frequent.yaml'):
        with open('frequent.yaml') as file:
            data = yaml.load(stream=file, Loader=yaml.FullLoader)
        if data.get(function_name):
            data[function_name] += 1
        else:
            data[function_name] = 1
    else:
        data = {function_name: 1}
    with open('frequent.yaml', 'w') as file:
        yaml.dump(data=data, stream=file)
