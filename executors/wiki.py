import sys

import wikipedia

from executors.word_match import word_match
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.models import models
from modules.utils import shared


def wikipedia_() -> None:
    """Gets any information from wikipedia using its API."""
    speaker.speak(text="Please tell the keyword.", run=True)
    if keyword := listener.listen(timeout=3, phrase_limit=5):
        if word_match(phrase=keyword, match_list=keywords.exit_):
            return
        else:
            sys.stdout.write(f"\rGetting your info from Wikipedia API for {keyword}")
            try:
                result = wikipedia.summary(keyword)
            except wikipedia.DisambiguationError as error:
                sys.stdout.write(f"\r{error}")
                speaker.speak(text=f"Your keyword has multiple results {models.env.title}. {' '.join(error.options)}"
                                   "Please pick one and try again.")
                if shared.called_by_offline:
                    return
                speaker.speak(run=True)
                if not (keyword1 := listener.listen(timeout=3, phrase_limit=5)):
                    return
                result = wikipedia.summary(keyword1)
            except wikipedia.PageError:
                speaker.speak(text=f"I'm sorry {models.env.title}! I didn't get a response for the phrase: {keyword}.")
                return
            # stops with two sentences before reading whole passage
            formatted = ". ".join(result.split(". ")[0:2]) + "."
            speaker.speak(text=f"{formatted}. Do you want me to continue {models.env.title}?", run=True)
            if response := listener.listen(timeout=3, phrase_limit=3):
                if word_match(phrase=response, match_list=keywords.ok):
                    speaker.speak(text=". ".join(result.split(". ")[3:]))
