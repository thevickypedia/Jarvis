import sys

import wikipedia

from modules.audio import listener, speaker
from modules.conditions import keywords


def wikipedia_() -> None:
    """Gets any information from wikipedia using its API."""
    speaker.speak(text="Please tell the keyword.", run=True)
    keyword = listener.listen(timeout=3, phrase_limit=5)
    if keyword != 'SR_ERROR':
        if any(word in keyword.lower() for word in keywords.exit_):
            return
        else:
            sys.stdout.write(f'\rGetting your info from Wikipedia API for {keyword}')
            try:
                result = wikipedia.summary(keyword)
            except wikipedia.DisambiguationError as e:  # checks for the right keyword in case of 1+ matches
                sys.stdout.write(f'\r{e}')
                speaker.speak(text='Your keyword has multiple results sir. Please pick any one on your screen.',
                              run=True)
                keyword1 = listener.listen(timeout=3, phrase_limit=5)
                result = wikipedia.summary(keyword1) if keyword1 != 'SR_ERROR' else None
            except wikipedia.PageError:
                speaker.speak(text=f"I'm sorry sir! I didn't get a response for the phrase: {keyword}. Try again!")
                return
            # stops with two sentences before reading whole passage
            formatted = '. '.join(result.split('. ')[0:2]) + '.'
            speaker.speak(text=f'{formatted}. Do you want me to continue sir?', run=True)
            response = listener.listen(timeout=3, phrase_limit=3)
            if response != 'SR_ERROR':
                if any(word in response.lower() for word in keywords.ok):
                    speaker.speak(text='. '.join(result.split('. ')[3:]))
