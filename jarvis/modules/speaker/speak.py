# noinspection PyUnresolvedReferences
"""Module to learn and train speech controls.

>>> Speak

"""

import logging
from collections.abc import Generator
from typing import Dict, NoReturn, Union

import pyttsx3

handler = logging.StreamHandler()
default_format = logging.Formatter(
    datefmt='%b-%d-%Y %I:%M:%S %p',
    fmt='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'
)
handler.setFormatter(fmt=default_format)

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logger.addHandler(hdlr=handler)

SAMPLE_TEXT = 'Neutron stars are one of the most extreme and violent things in the universe. ' \
              'Giant atomic nuclei, only a few kilometers in diameter, but as massive as stars. ' \
              'And they owe their existence to the death of something majestic.'


class Speaker:
    """Initiates speaker object to test the speaker's voice and rate.

    >>> Speaker

    """

    def __init__(self):
        """Instantiates the speaker engine and loads the voices available in the hosting machine."""
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty("voices")  # gets the list of voices available

    # noinspection PyTypeChecker
    def get_all_voices(self) -> Generator[Dict[str, Union[str, int]]]:
        """Yields all the available voices, converting attributes into dict."""
        logger.info('Getting all voice attributes.')
        for index, voice in enumerate(self.voices):
            yield {'index': index, 'id': voice.id, 'name': voice.name, 'gender': voice.gender}

    # noinspection PyTypeChecker
    def get_english_voices(self) -> Generator[Dict[str, Union[str, int]]]:
        """Yields all the available voices for english language, converting attributes into dict."""
        logger.info('Getting voice attributes for english language.')
        for index, voice in enumerate(self.voices):
            if 'en_US' in voice.languages:
                yield {'index': index, 'id': voice.id, 'name': voice.name, 'gender': voice.gender}

    # noinspection PyTypeChecker
    def get_voice_by_language(self, lang_code: str) -> Generator[Dict[str, Union[str, int]]]:
        """Yields all the available voices for the given language, converting attributes into dict."""
        logger.info("Getting voice for the language code: '%s'", lang_code)
        for index, voice in enumerate(self.voices):
            if lang_code in voice.languages:
                yield {'index': index, 'id': voice.id, 'name': voice.name, 'gender': voice.gender}

    def get_voice_by_index(self, index: int) -> Dict[str, Union[str, int]]:
        """Yields all the available voices for the given index, converting attributes into dict."""
        logger.info("Getting voice for the index: '%s'", index)
        for voice in self.get_all_voices():
            if voice['index'] == index:
                return voice

    def get_voice_by_name(self, name: str) -> Generator[Dict[str, Union[str, int]]]:
        """Yields all the available voices matching the given name, converting attributes into dict."""
        logger.info("Getting voices for the name: %s", name)
        for voice in self.get_all_voices():
            if name.lower() in voice['name'].lower():
                yield voice

    def get_voice_by_gender(self, gender: str) -> Generator[Dict[str, Union[str, int]]]:
        """Yields all the available voices matching the given gender, converting attributes into dict."""
        gender = "VoiceGenderMale" if gender.lower() == 'male' else "VoiceGenderFemale"
        logger.info("Getting voices for the gender: %s", gender)
        for voice in self.get_all_voices():
            if gender == voice['gender']:
                yield voice

    # noinspection PyUnresolvedReferences
    def set_voice(self, voice_index: int, rate: int = 200) -> NoReturn:
        """Set voice attributes per given values.

        Args:
            voice_index: Index of the voice that has to be used.
            rate: Rate at which the voice should speak.
        """
        logger.debug("Setting voice index to %d and speech rate to '%d'", voice_index, rate)
        self.engine.setProperty("voice", self.voices[voice_index].id)
        self.engine.setProperty("rate", rate)

    def speak_all_voices(self) -> NoReturn:
        """Speaks the voice name in all available voices."""
        for voice in self.get_all_voices():
            self.set_voice(voice_index=voice['index'])
            logger.info("Speaker voice [%s]: '%s'", voice['index'], voice['name'])
            self.run(text=f"Hello, I am {voice['name']}. This is my voice.")

    def speak_english_voices(self) -> NoReturn:
        """Speaks the voice name in all available english voices."""
        for voice in self.get_english_voices():
            self.set_voice(voice_index=voice['index'])
            logger.info("Speaker voice [%s]: '%s'", voice['index'], voice['name'])
            self.run(text=f"Hello, I am {voice['name']}. This is my voice.")

    def run(self, text: str = None) -> NoReturn:
        """Speaks the given text in the voice set.

        Args:
            text: Text that has to be spoken. Defaults to a sample text.
        """
        if text is None:
            text = SAMPLE_TEXT
        self.engine.say(text)
        self.engine.runAndWait()
