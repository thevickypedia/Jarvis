# noinspection PyUnresolvedReferences
"""Module for speaker and voice options.

>>> Speaker

"""

import random
import sys
from typing import Union

import pyttsx3

from modules.audio.listener import listen
from modules.conditions import conversation, keywords
from modules.logger.custom_logger import logger
from modules.utils.globals import text_spoken

audio_driver = pyttsx3.init()


def speak(text: str = None, run: bool = False) -> None:
    """Calls ``audio_driver.say`` to speak a statement from the received text.

    Args:
        text: Takes the text that has to be spoken as an argument.
        run: Takes a boolean flag to choose whether to run the ``audio_driver.say`` loop.
    """
    if text:
        audio_driver.say(text=text)
        text = text.replace('\n', '\t').strip()
        logger.info(f'Response: {text}')
        logger.info(f'Speaker called by: {sys._getframe(1).f_code.co_name}')  # noqa
        sys.stdout.write(f"\r{text}")
        text_spoken['text'] = text
    if run:
        audio_driver.runAndWait()


def voice_default(voice_model: str = 'Daniel') -> None:
    """Sets voice module to default.

    Args:
        voice_model: Defaults to ``Daniel`` in mac.
    """
    voices = audio_driver.getProperty("voices")  # gets the list of voices available
    for ind_d, voice_d in enumerate(voices):  # noqa
        if voice_d.name == voice_model:
            sys.stdout.write(f'\rVoice module has been configured to {ind_d}::{voice_d.name}')
            audio_driver.setProperty("voice", voices[ind_d].id)  # noqa
            return


def voice_changer(phrase: str = None) -> None:
    """Speaks to the user with available voices and prompts the user to choose one.

    Args:
        phrase: Initiates changing voices with the model name. If none, defaults to ``Daniel``
    """
    if not phrase:
        voice_default()
        return

    voices: Union[list, object] = audio_driver.getProperty("voices")  # gets the list of voices available

    choices_to_say = ['My voice module has been reconfigured. Would you like me to retain this?',
                      "Here's an example of one of my other voices. Would you like me to use this one?",
                      'How about this one?']

    for ind, voice in enumerate(voices):
        audio_driver.setProperty("voice", voices[ind].id)
        speak(text=f'I am {voice.name} sir!')
        sys.stdout.write(f'\rVoice module has been re-configured to {ind}::{voice.name}')
        speak(text=choices_to_say[ind]) if ind < len(choices_to_say) else speak(text=random.choice(choices_to_say))
        speak(run=True)
        keyword = listen(timeout=3, phrase_limit=3)
        if keyword == 'SR_ERROR':
            voice_default()
            speak(text="Sorry sir! I had trouble understanding. I'm back to my default voice.")
            return
        elif 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            voice_default()
            speak(text='Reverting the changes to default voice module sir!')
            return
        elif any(word in keyword.lower() for word in keywords.ok):
            speak(text=random.choice(conversation.acknowledgement))
            return
