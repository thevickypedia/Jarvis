# noinspection PyUnresolvedReferences
"""Module for speaker and voice options.

>>> Speaker

"""
import os
import re
import sys
from datetime import datetime
from threading import Thread
from urllib.parse import urljoin

import pynotification
import requests
from playsound import playsound

from jarvis.executors import files
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support


def speech_synthesizer(
    text: str,
    timeout: int | float = None,
    quality: str = models.env.speech_synthesis_quality,
    voice: str = models.env.speech_synthesis_voice,
) -> bool:
    """Makes a post call to the speech-synthesis API for text-to-speech.

    Args:
        text: Takes the text that has to be spoken as an argument.
        timeout: Time to wait for the speech-synthesis API to process the text-to-speech request.
        quality: Quality at which the conversion is to be done.
        voice: Voice for speech synthesis.

    Returns:
        bool:
        A boolean flag to indicate whether speech synthesis has worked.
    """
    logger.info("Request for speech synthesis: %s", text)
    text = text.replace("%", " percent")
    if time_in_str := re.findall(r"(\d+:\d+\s?(?:AM|PM|am|pm:?))", text):
        for t_12 in time_in_str:
            t_24 = datetime.strftime(datetime.strptime(t_12, "%I:%M %p"), "%H:%M")
            logger.info("Converted %s -> %s", t_12, t_24)
            text = text.replace(t_12, t_24)
    if "IP" in text.split():
        # 192.168.1.1 -> 1-9-2, 1-6-8, 1, 1
        ip_new = "-".join([i for i in text.split(" ")[-1]]).replace("-.-", ", ")
        text = text.replace(text.split(" ")[-1], ip_new).replace(" IP ", " I.P. ")
    # Raises UnicodeDecodeError within docker container
    text = text.replace("\N{DEGREE SIGN}F", " degrees fahrenheit")
    text = text.replace("\N{DEGREE SIGN}C", " degrees celsius")
    try:
        url = urljoin(str(models.env.speech_synthesis_api), "/api/tts")
        response = requests.post(
            url=url,
            headers={"Content-Type": "text/plain"},
            params={"voice": voice, "vocoder": quality},
            data=text,
            verify=False,
            timeout=timeout
            or models.env.speech_synthesis_timeout,  # set timeout here as speak() sets it on demand
        )
        if response.ok:
            with open(file=models.fileio.speech_synthesis_wav, mode="wb") as file:
                file.write(response.content)
                file.flush()
            return True
        logger.error("%s::%s", response.status_code, url)
        return False
    except UnicodeError as error:
        logger.error(error)
    except EgressErrors as error:
        logger.error(error)
        logger.info("Disabling speech synthesis")
        # Purposely exclude timeout since, speech-synthesis takes more time initially to download the required voice
        if not any(
            (isinstance(error, TimeoutError), isinstance(error, requests.Timeout))
        ):
            models.env.speech_synthesis_timeout = 0


def speak(text: str = None, run: bool = False, block: bool = True) -> None:
    """Speaks a statement from the received text.

    Args:
        text: Takes the text that has to be spoken as an argument.
        run: Takes a boolean flag to choose whether to run the loop.
        block: Takes a boolean flag to await other tasks while speaking. [Applies only for speech-synthesis on docker]
    """
    if not models.AUDIO_DRIVER:
        models.env.speech_synthesis_timeout = 10
    caller = sys._getframe(1).f_code.co_name  # noqa
    # function where all the magic happens
    if caller not in (
        "conditions",
        "custom_conditions",
    ):
        Thread(target=frequently_used, kwargs={"function_name": caller}).start()
    if text:
        text = text.replace("\n", "\t").strip()
        shared.text_spoken = text
        if shared.called_by_offline:
            logger.debug("Speaker called by: '%s' with text: '%s'", caller, text)
            shared.offline_caller = caller
            return
        logger.info("Response: %s", text)
        support.write_screen(text=text)
        if (
            models.env.speech_synthesis_timeout
            and models.env.speech_synthesis_api
            and speech_synthesizer(text=text)
            and os.path.isfile(models.fileio.speech_synthesis_wav)
        ):
            playsound(sound=models.fileio.speech_synthesis_wav, block=block)
            os.remove(models.fileio.speech_synthesis_wav)
        elif models.AUDIO_DRIVER:
            models.AUDIO_DRIVER.say(text=text)
        else:
            support.flush_screen()
            pynotification.pynotifier(
                message="speech-synthesis became unavailable when audio driver was faulty\n"
                "resolving to on-screen response",
                title="AUDIO ERROR",
                dialog=True,
            )
            print(text)
    if run and models.AUDIO_DRIVER and not shared.called_by_offline:
        logger.debug("Speaker called by: '%s'", caller)
        models.AUDIO_DRIVER.runAndWait()


def frequently_used(function_name: str) -> None:
    """Writes the function called and the number of times into a yaml file.

    Args:
        function_name: Name of the function that called the speaker.

    See Also:
        - This function does not have purpose, but to analyze and re-order the conditions' module at a later time.
    """
    data = files.get_frequent()
    data = {k: v for k, v in data.items() if isinstance(v, int)}  # clean up
    if data.get(function_name):
        data[function_name] += 1
    else:
        data[function_name] = 1
    data = {
        k: v for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)
    }  # sort by size
    files.put_frequent(data=data)
