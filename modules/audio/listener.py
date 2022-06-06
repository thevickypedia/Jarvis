# noinspection PyUnresolvedReferences
"""Module for speech recognition listener.

>>> Listener

"""
import sys
from typing import Union

from playsound import playsound
from speech_recognition import (Recognizer, RequestError, UnknownValueError,
                                WaitTimeoutError)

from executors.logger import logger
from modules.models import models
from modules.utils import shared, support

indicators = models.Indicators()
recognizer = Recognizer()  # initiates recognizer that uses google's translation


def listen(timeout: Union[int, float], phrase_limit: Union[int, float], sound: bool = True) -> Union[str, None]:
    """Function to activate listener, this function will be called by most upcoming functions to listen to user input.

    Args:
        timeout: Time in seconds for the overall listener to be active.
        phrase_limit: Time in seconds for the listener to actively listen to a sound.
        sound: Flag whether to play the listener indicator sound. Defaults to True unless set to False.

    Returns:
        str:
         - Returns recognized statement from the microphone.
    """
    try:
        playsound(sound=indicators.start, block=False) if sound else sys.stdout.write("\rListener activated...")
        listened = recognizer.listen(source=shared.source, timeout=timeout, phrase_time_limit=phrase_limit)
        playsound(sound=indicators.end, block=False) if sound else support.flush_screen()
        recognized = recognizer.recognize_google(audio_data=listened)
        logger.info(recognized)
        return recognized
    except (UnknownValueError, RequestError, WaitTimeoutError):
        return
    except (ConnectionError, TimeoutError) as error:
        logger.error(error)
