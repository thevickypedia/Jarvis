# noinspection PyUnresolvedReferences
"""Module for speech recognition listener.

>>> Listener

"""

from typing import Union

from playsound import playsound
from speech_recognition import (Microphone, Recognizer, RequestError,
                                UnknownValueError, WaitTimeoutError)

from executors.logger import logger
from modules.models import models

indicators = models.Indicators()
recognizer = Recognizer()  # initiates recognizer that uses google's translation
microphone = Microphone()  # initiates microphone as a source for audio


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
    with microphone as source:
        try:
            playsound(sound=indicators.start, block=False) if sound else None
            listened = recognizer.listen(source=source, timeout=timeout, phrase_time_limit=phrase_limit)
            playsound(sound=indicators.end, block=False) if sound else None
            recognized = recognizer.recognize_google(audio_data=listened)
            logger.info(recognized)
            return recognized
        except (UnknownValueError, RequestError, WaitTimeoutError):
            return
