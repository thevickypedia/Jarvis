# noinspection PyUnresolvedReferences
"""Module for voice changes.

>>> Voices

"""

import random
import sys
from typing import Union

from modules.audio import listener, speaker
from modules.conditions import conversation, keywords
from modules.models import models

env = models.env


def voice_default() -> None:
    """Sets voice module to default."""
    voices = speaker.audio_driver.getProperty("voices")  # gets the list of voices available
    voice_model = "Daniel" if env.mac else "David"
    for ind_d, voice_id in enumerate(voices):  # noqa
        if voice_id.name == voice_model or voice_model in voice_id.name:
            sys.stdout.write(f"\rVoice module has been configured to {ind_d}::{voice_id.name}")
            speaker.audio_driver.setProperty("voice", voices[ind_d].id)  # noqa
            return


def voice_changer(phrase: str = None) -> None:
    """Speaks to the user with available voices and prompts the user to choose one.

    Args:
        phrase: Initiates changing voices with the model name. If none, defaults to ``Daniel``
    """
    if not phrase:
        voice_default()
        return

    voices: Union[list, object] = speaker.audio_driver.getProperty("voices")  # gets the list of voices available

    choices_to_say = ["My voice module has been reconfigured. Would you like me to retain this?",
                      "Here's an example of one of my other voices. Would you like me to use this one?",
                      "How about this one?"]

    for ind, voice in enumerate(voices):
        speaker.audio_driver.setProperty("voice", voices[ind].id)
        speaker.speak(text=f"I am {voice.name} {env.title}!")
        sys.stdout.write(f"\rVoice module has been re-configured to {ind}::{voice.name}")
        if ind < len(choices_to_say):
            speaker.speak(text=choices_to_say[ind])
        else:
            speaker.speak(text=random.choice(choices_to_say))
        speaker.speak(run=True)
        keyword = listener.listen(timeout=3, phrase_limit=3)
        if keyword == "SR_ERROR":
            voice_default()
            speaker.speak(text=f"Sorry {env.title}! I had trouble understanding. I'm back to my default voice.")
            return
        elif "exit" in keyword or "quit" in keyword or "Xzibit" in keyword:
            voice_default()
            speaker.speak(text=f"Reverting the changes to default voice module {env.title}!")
            return
        elif any(word in keyword.lower() for word in keywords.ok):
            speaker.speak(text=random.choice(conversation.acknowledgement))
            return
