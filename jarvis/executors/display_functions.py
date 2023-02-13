import random
from threading import Thread

import pybrightness

from jarvis.modules.audio import speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.utils import util


def brightness(phrase: str):
    """Pre-process to check the phrase received and call the appropriate brightness function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    speaker.speak(text=random.choice(conversation.acknowledgement))
    if 'set' in phrase:
        level = util.extract_nos(input_=phrase, method=int)
        if level is None:
            level = 50
        Thread(target=pybrightness.custom, args=[level]).start()
    elif 'decrease' in phrase or 'reduce' in phrase or 'lower' in phrase or \
            'dark' in phrase or 'dim' in phrase:
        Thread(target=pybrightness.decrease).start()
    elif 'increase' in phrase or 'bright' in phrase or 'max' in phrase or \
            'brighten' in phrase or 'light up' in phrase:
        Thread(target=pybrightness.decrease).start()
