# noinspection PyUnresolvedReferences
"""Module for speech recognition listener.

>>> Listener

"""

from playsound import playsound
from pydantic import PositiveFloat, PositiveInt
from speech_recognition import (
    Microphone,
    Recognizer,
    RequestError,
    UnknownValueError,
    WaitTimeoutError,
)

from jarvis.executors import files, word_match
from jarvis.modules.audio import speaker, wave
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support

recognizer = Recognizer()
spectrum = wave.Spectrum()
microphone = Microphone(device_index=models.env.microphone_index)

if models.settings.pname == "JARVIS":
    recognizer_settings = files.get_recognizer()
    recognizer.energy_threshold = recognizer_settings.energy_threshold
    recognizer.pause_threshold = recognizer_settings.pause_threshold
    recognizer.phrase_threshold = recognizer_settings.phrase_threshold
    recognizer.dynamic_energy_threshold = recognizer_settings.dynamic_energy_threshold
    recognizer.non_speaking_duration = recognizer_settings.non_speaking_duration


def listen(
    sound: bool = True,
    no_conf: bool = False,
    timeout: PositiveInt | PositiveFloat = models.env.listener_timeout,
    phrase_time_limit: PositiveInt | PositiveFloat = models.env.listener_phrase_limit,
) -> str | None:
    """Function to activate listener, this function will be called by most upcoming functions to listen to user input.

    Args:
        sound: Flag whether to play the listener indicator sound. Defaults to True unless set to False.
        no_conf: Boolean flag to skip confidence check.
        timeout: Custom timeout for functions expecting a longer wait time.
        phrase_time_limit: Custom time limit for functions expecting a longer user input.

    Returns:
        str:
         - Returns recognized statement from the microphone.
    """
    with microphone as source:
        try:
            spectrum.activate(
                sound=sound, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
            listened = recognizer.listen(
                source=source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
            spectrum.deactivate(sound=sound)
            recognized, confidence = recognizer.recognize_google(
                audio_data=listened, with_confidence=True
            )
            # SafetyNet: Should never meet the condition for called by offline
            if no_conf or shared.called_by_offline:
                logger.info(recognized)
                return recognized
            logger.info(
                "Recognized '%s' with a confidence rate '%.2f'", recognized, confidence
            )
            if confidence > models.env.recognizer_confidence:
                return recognized
            else:
                speaker.speak(text=f"Did you mean {recognized!r}?", run=True)
                if listen_recursive(source, 5, 5):
                    return recognized
        except (UnknownValueError, RequestError, WaitTimeoutError):
            return
        except EgressErrors as error:
            logger.error(error)


def listen_recursive(source: Microphone, timeout: int, phrase_time_limit: int) -> bool:
    """Process confirmation for words that were recognized with a confidence score lower than the threshold.

    Args:
        source: Microphone source.
        timeout: Custom timeout for functions expecting a longer wait time.
        phrase_time_limit: Custom time limit for functions expecting a longer user input.

    Returns:
        bool:
        True if confirmation was received from the user via voice input.
    """
    playsound(sound=models.indicators.start, block=False)
    support.write_screen(text=f"Listener activated [{timeout}: {phrase_time_limit}]")
    listened = recognizer.listen(
        source=source, timeout=timeout, phrase_time_limit=phrase_time_limit
    )
    playsound(sound=models.indicators.end, block=False)
    support.flush_screen()
    recognized = recognizer.recognize_google(audio_data=listened)
    if word_match.word_match(
        phrase=recognized, match_list=("yes", "yeah", "yep", "yeh", "indeed")
    ):
        return True
