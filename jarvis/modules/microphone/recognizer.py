# noinspection PyUnresolvedReferences
"""Module to learn and train speech recognition settings.

>>> Recognizer

"""

import asyncio
import logging
import platform
from typing import NoReturn

import speech_recognition
import yaml

from jarvis.modules.exceptions import no_alsa_err

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

RECOGNIZER = speech_recognition.Recognizer()
if platform.system() == "Linux":
    with no_alsa_err():
        MICROPHONE = speech_recognition.Microphone()
else:
    MICROPHONE = speech_recognition.Microphone()
COMMON_ERRORS = speech_recognition.UnknownValueError, speech_recognition.RequestError, \
    speech_recognition.WaitTimeoutError, TimeoutError, ConnectionError,

defaults = dict(energy_threshold=RECOGNIZER.energy_threshold,
                dynamic_energy_threshold=RECOGNIZER.dynamic_energy_threshold,
                pause_threshold=RECOGNIZER.pause_threshold,
                phrase_threshold=RECOGNIZER.phrase_threshold,
                non_speaking_duration=RECOGNIZER.non_speaking_duration)
RECOGNIZER.energy_threshold = 300
RECOGNIZER.dynamic_energy_threshold = False
RECOGNIZER.pause_threshold = 2
RECOGNIZER.phrase_threshold = 0.1
RECOGNIZER.non_speaking_duration = 2

assert RECOGNIZER.pause_threshold >= RECOGNIZER.non_speaking_duration > 0, \
    "'pause_threshold' cannot be lower than 'non_speaking_duration' or 0"

changed = dict(energy_threshold=RECOGNIZER.energy_threshold,
               dynamic_energy_threshold=RECOGNIZER.dynamic_energy_threshold,
               pause_threshold=RECOGNIZER.pause_threshold,
               phrase_threshold=RECOGNIZER.phrase_threshold,
               non_speaking_duration=RECOGNIZER.non_speaking_duration)


async def save_for_reference() -> NoReturn:
    """Saves the original config and new config in a yaml file."""
    with open('speech_recognition_values.yaml', 'w') as file:
        yaml.dump(data={"defaults": defaults, "modified": changed}, stream=file)


async def main() -> NoReturn:
    """Initiates yaml dump in an asynchronous call and initiates listener in a never ending loop."""
    asyncio.create_task(save_for_reference())
    with MICROPHONE as source:
        while True:
            try:
                logger.info('Listening..')
                audio = RECOGNIZER.listen(source)
                logger.info('Recognizing..')
                recognized = RECOGNIZER.recognize_google(audio_data=audio)  # Requires stable internet connection
                # recognized = RECOGNIZER.recognize_sphinx(audio_data=audio)  # Requires pocketsphinx module
                print(recognized)
                if "stop" in recognized.lower().split():
                    break
            except COMMON_ERRORS as error:
                logger.debug(error)
                continue
