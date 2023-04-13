# noinspection PyUnresolvedReferences
"""Module for speech recognition listener.

>>> Listener

"""
from typing import Union

from playsound import playsound
from speech_recognition import (Microphone, Recognizer, RequestError,
                                UnknownValueError, WaitTimeoutError)

from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support, util

recognizer = Recognizer()
microphone = Microphone(device_index=models.env.microphone_index)

if models.env.recognizer_settings:
    recognizer.energy_threshold = models.env.recognizer_settings.energy_threshold
    recognizer.pause_threshold = models.env.recognizer_settings.pause_threshold
    recognizer.phrase_threshold = models.env.recognizer_settings.phrase_threshold
    recognizer.dynamic_energy_threshold = models.env.recognizer_settings.dynamic_energy_threshold
    recognizer.non_speaking_duration = models.env.recognizer_settings.non_speaking_duration
    models.env.phrase_limit = 10  # Override voice phrase limit when recognizer settings are available


def listen(sound: bool = True, stdout: bool = True) -> Union[str, None]:
    """Function to activate listener, this function will be called by most upcoming functions to listen to user input.

    Args:
        sound: Flag whether to play the listener indicator sound. Defaults to True unless set to False.
        stdout: Flag whether to print the listener status on screen.

    Returns:
        str:
         - Returns recognized statement from the microphone.
    """
    with microphone as source:
        try:
            playsound(sound=models.indicators.start, block=False) if sound else None
            util.write_screen(text="Listener activated...") if stdout else None
            listened = recognizer.listen(source=source, timeout=models.env.timeout,
                                         phrase_time_limit=models.env.phrase_limit)
            playsound(sound=models.indicators.end, block=False) if sound else None
            support.flush_screen()
            recognized = recognizer.recognize_google(audio_data=listened)
            logger.info(recognized)
            return recognized
        except (UnknownValueError, RequestError, WaitTimeoutError):
            return
        except EgressErrors as error:
            logger.error(error)
