# noinspection PyUnresolvedReferences
"""Module for speaker and voice options.

>>> Speaker

"""
import os
import re
import sys
from datetime import datetime
from threading import Thread
from typing import NoReturn, Union

import pynotification
import requests
from playsound import playsound

from jarvis.executors import files
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util

SS_HEADERS = {
    "Content-Type": "text/plain"
}


def speech_synthesizer(text: str,
                       timeout: Union[int, float] = None,
                       quality: str = models.env.speech_synthesis_quality,
                       voice: str = models.env.speech_synthesis_voice) -> bool:
    """Makes a post call to docker container for speech synthesis.

    Args:
        text: Takes the text that has to be spoken as an argument.
        timeout: Time to wait for the docker image to process text-to-speech request.
        quality: Quality at which the conversion is to be done.
        voice: Voice for speech synthesis.

    Returns:
        bool:
        A boolean flag to indicate whether speech synthesis has worked.
    """
    logger.info("Request for speech synthesis: %s", text)
    text = text.replace("%", " percent")
    if time_in_str := re.findall(r'(\d+:\d+\s?(?:AM|PM|am|pm:?))', text):
        for t_12 in time_in_str:
            t_24 = datetime.strftime(datetime.strptime(t_12, "%I:%M %p"), "%H:%M")
            logger.info("Converted %s -> %s", t_12, t_24)
            text = text.replace(t_12, t_24)
    if 'IP' in text.split():
        ip_new = '-'.join([i for i in text.split(' ')[-1]]).replace('-.-', ', ')  # 192.168.1.1 -> 1-9-2, 1-6-8, 1, 1
        text = text.replace(text.split(' ')[-1], ip_new).replace(' IP ', ' I.P. ')
    # Raises UnicodeDecodeError within docker container
    text = text.replace("\N{DEGREE SIGN}F", " degrees fahrenheit")
    text = text.replace("\N{DEGREE SIGN}C", " degrees celsius")
    try:
        response = requests.post(
            url=f"http://{models.env.speech_synthesis_host}:{models.env.speech_synthesis_port}/api/tts",
            headers=SS_HEADERS, params={"voice": voice, "vocoder": quality}, data=text, verify=False,
            timeout=timeout or models.env.speech_synthesis_timeout  # set timeout here as speak() sets it on demand
        )
        if response.ok:
            with open(file=models.fileio.speech_synthesis_wav, mode="wb") as file:
                file.write(response.content)
            return True
        logger.error("{code}::http://{host}:{port}/api/tts".format(code=response.status_code,
                                                                   host=models.env.speech_synthesis_host,
                                                                   port=models.env.speech_synthesis_port))
        return False
    except UnicodeError as error:
        logger.error(error)
    except EgressErrors as error:
        logger.error(error)
        logger.info("Disabling speech synthesis")
        # Purposely exclude timeout since, speech-synthesis takes more time initially to download the required voice
        if not any((isinstance(error, TimeoutError), isinstance(error, requests.Timeout))):
            models.env.speech_synthesis_timeout = 0


def speak(text: str = None, run: bool = False, block: bool = True) -> NoReturn:
    """Calls ``audio_driver.say`` to speak a statement from the received text.

    Args:
        text: Takes the text that has to be spoken as an argument.
        run: Takes a boolean flag to choose whether to run the ``audio_driver.say`` loop.
        block: Takes a boolean flag to await other tasks while speaking. [Applies only for speech-synthesis on docker]
    """
    if not models.audio_driver:
        models.env.speech_synthesis_timeout = 10
    caller = sys._getframe(1).f_code.co_name  # noqa: PyProtectedMember,PyUnresolvedReferences
    if caller != 'conditions':  # function where all the magic happens
        Thread(target=frequently_used, kwargs={"function_name": caller}).start()
    if text:
        text = text.replace('\n', '\t').strip()
        shared.text_spoken = text
        if shared.called_by_offline:
            shared.offline_caller = caller
            return
        logger.info("Response: %s", text)
        util.write_screen(text=text)
        if models.env.speech_synthesis_timeout and \
                speech_synthesizer(text=text) and \
                os.path.isfile(models.fileio.speech_synthesis_wav):
            playsound(sound=models.fileio.speech_synthesis_wav, block=block)
            os.remove(models.fileio.speech_synthesis_wav)
        elif models.audio_driver:
            models.audio_driver.say(text=text)
        else:
            support.flush_screen()
            pynotification.pynotifier(message="speech-synthesis became unavailable when audio driver was faulty\n"
                                              "resolving to on-screen response", title="AUDIO ERROR", dialog=True)
            print(text)
    if run and models.audio_driver and not shared.called_by_offline:
        logger.debug("Speaker called by: '%s'", caller)
        models.audio_driver.runAndWait()


def frequently_used(function_name: str) -> NoReturn:
    """Writes the function called and the number of times into a yaml file.

    Args:
        function_name: Name of the function that called the speaker.

    See Also:
        - This function does not have purpose, but to analyze and re-order the conditions' module at a later time.
    """
    data = files.get_frequent(func=function_name)
    try:
        data = {k: v for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)}
    except Exception as error:  # Commonly raises key error or type error but don't care, log it and remove the file
        logger.error(error)
        logger.warning(data)
        if os.path.isfile(models.fileio.frequent):
            os.remove(models.fileio.frequent)
        return
    files.put_frequent(data=data)
