import logging
from typing import Dict, Iterable, NoReturn

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
    def get_all_voices(self) -> Iterable[Dict]:
        """Yields all the available voices, converting attributes into dict."""
        logger.info('Getting all voice attributes.')
        for index, voice in enumerate(self.voices):
            yield {'index': index, 'id': voice.id, 'name': voice.name, 'gender': voice.gender}

    # noinspection PyTypeChecker
    def get_english_voices(self) -> Iterable[Dict]:
        """Yields all the available voices for english language, converting attributes into dict."""
        logger.info('Getting voice attributes for english language.')
        for index, voice in enumerate(self.voices):
            if 'en_US' in voice.languages:
                yield {'index': index, 'id': voice.id, 'name': voice.name, 'gender': voice.gender}

    # noinspection PyTypeChecker
    def get_voice_by_language(self, lang_code: str) -> Iterable[Dict]:
        """Yields all the available voices for the given language, converting attributes into dict."""
        logger.info(f'Getting voice for the language code: {lang_code!r}')
        for index, voice in enumerate(self.voices):
            if lang_code in voice.languages:
                yield {'index': index, 'id': voice.id, 'name': voice.name, 'gender': voice.gender}

    def get_voice_by_index(self, index: int) -> Dict:
        """Yields all the available voices for the given index, converting attributes into dict."""
        logger.info(f'Getting voice for the index: {index}')
        for voice in self.get_all_voices():
            if voice['index'] == index:
                return voice

    def get_voice_by_name(self, name: str) -> Iterable[Dict]:
        """Yields all the available voices matching the given name, converting attributes into dict."""
        logger.info(f'Getting voices for the name: {name}')
        for voice in self.get_all_voices():
            if name.lower() in voice['name'].lower():
                yield voice

    def get_voice_by_gender(self, gender: str) -> Iterable[Dict]:
        """Yields all the available voices matching the given gender, converting attributes into dict."""
        gender = "VoiceGenderMale" if gender.lower() == 'male' else "VoiceGenderFemale"
        logger.info(f'Getting voices for the gender: {gender}')
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
        logger.debug(f'Setting voice index to {voice_index} and speech rate to {rate!r}')
        self.engine.setProperty("voice", self.voices[voice_index].id)
        self.engine.setProperty("rate", rate)

    def speak_all_voices(self) -> NoReturn:
        """Speaks the voice name in all available voices."""
        for voice in self.get_all_voices():
            self.set_voice(voice_index=voice['index'])
            logger.info(f"Speaker voice [{voice['index']}]: {voice['name']!r}")
            self.run(text=f"Hello, I am {voice['name']}. This is my voice.")

    def speak_english_voices(self) -> NoReturn:
        """Speaks the voice name in all available english voices."""
        for voice in self.get_english_voices():
            self.set_voice(voice_index=voice['index'])
            logger.info(f"Speaker voice [{voice['index']}]: {voice['name']!r}")
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
