# noinspection PyUnresolvedReferences
"""Module for speaker and voice options.

>>> Speaker

"""
import os.path
import sys
from threading import Thread
from typing import NoReturn

import pyttsx3
import requests
import yaml
from playsound import playsound

from executors.logger import logger
from modules.conditions import conversation, keywords
from modules.models import models
from modules.utils import shared

fileio = models.FileIO()
env = models.env

audio_driver = pyttsx3.init()

KEYWORDS = [__keyword for __keyword in dir(keywords) if not __keyword.startswith('__')]
CONVERSATION = [__conversation for __conversation in dir(conversation) if not __conversation.startswith('__')]
FUNCTIONS_TO_TRACK = KEYWORDS + CONVERSATION


def speech_synthesizer(text: str, timeout: int = env.speech_synthesis_timeout) -> bool:
    """Makes a post call to docker container running on localhost for speech synthesis.

    Args:
        text: Takes the text that has to be spoken as an argument.
        timeout: Time to wait for the docker image to process text-to-speech request.

    Returns:
        bool:
        A boolean flag to indicate whether speech synthesis has worked.
    """
    try:
        response = requests.post(url=f"http://localhost:{env.speech_synthesis_port}/api/tts",
                                 headers={"Content-Type": "text/plain"},
                                 params={"voice": "en-us_northern_english_male-glow_tts", "quality": "medium"},
                                 data=text, verify=False, timeout=timeout)
        logger.error(f"{response.status_code}::http://localhost:{env.speech_synthesis_port}/api/tts")
        if not response.ok:
            return False
        with open(file=fileio.speech_synthesis_wav, mode="wb") as file:
            file.write(response.content)
        return True
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout) as error:
        # Timeout exception covers both connection timeout and read timeout
        logger.error(error)


def speak(text: str = None, run: bool = False, block: bool = True) -> NoReturn:
    """Calls ``audio_driver.say`` to speak a statement from the received text.

    Args:
        text: Takes the text that has to be spoken as an argument.
        run: Takes a boolean flag to choose whether to run the ``audio_driver.say`` loop.
        block: Takes a boolean flag to wait other tasks while speaking. [Applies only for larynx running on docker]
    """
    caller = sys._getframe(1).f_code.co_name  # noqa
    if text:
        text = text.replace('\n', '\t').strip()
        logger.info(f'Response: {text}')
        logger.info(f'Speaker called by: {caller}')
        sys.stdout.write(f"\r{text}")
        shared.text_spoken = text
        if shared.called_by_offline:
            shared.offline_caller = caller
        else:
            if env.speech_synthesis_timeout and \
                    speech_synthesizer(text=text) and \
                    os.path.isfile(fileio.speech_synthesis_wav):
                playsound(sound=fileio.speech_synthesis_wav, block=block)
                os.remove(fileio.speech_synthesis_wav)
            else:
                audio_driver.say(text=text)
    if run:
        audio_driver.runAndWait()
    Thread(target=frequently_used, kwargs={"function_name": caller}).start() if caller in FUNCTIONS_TO_TRACK else None


def frequently_used(function_name: str) -> NoReturn:
    """Writes the function called and the number of times into a yaml file.

    Args:
        function_name: Name of the function that called the speaker.

    See Also:
        - This function does not have purpose, but to analyze and re-order the conditions' module at a later time.
    """
    if os.path.isfile(fileio.frequent):
        try:
            with open(fileio.frequent) as file:
                data = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
        except yaml.YAMLError as error:
            data = {}
            logger.error(error)
        if data.get(function_name):
            data[function_name] += 1
        else:
            data[function_name] = 1
    else:
        data = {function_name: 1}
    with open(fileio.frequent, 'w') as file:
        yaml.dump(data={k: v for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)},
                  stream=file, sort_keys=False)
