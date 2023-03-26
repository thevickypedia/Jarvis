from wikipedia import DisambiguationError, PageError, WikipediaPage

from jarvis.executors import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared


def wikipedia_(phrase: str) -> None:
    """Gets any information from wikipedia using its API.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    _, _, keyword = phrase.lower().partition(' keyword ')
    if keyword:
        keyword = keyword.strip()
    else:
        _, _, keyword = phrase.lower().partition(' for ')
    if keyword:
        keyword = keyword.strip()
    else:
        speaker.speak(text=f"I'm sorry {models.env.title}! I can't get the information without a keyword.")
        return
    try:
        result = WikipediaPage(keyword).summary
    except DisambiguationError as error:
        logger.error(error)
        speaker.speak(text=f"Your keyword has multiple results {models.env.title}. {' '.join(error.options)}"
                           "Please pick one and try again.")
        if shared.called_by_offline:
            return
        speaker.speak(run=True)
        if not (alt_keyword := listener.listen()) or \
                'exit' in alt_keyword or 'quit' in alt_keyword or 'Xzibit' in alt_keyword:
            return
        result = WikipediaPage(alt_keyword).summary
    except PageError as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I didn't get a response for the phrase: {keyword}.")
        return
    # stops with two sentences before reading whole passage
    formatted = ". ".join(result.split(". ")[:2]) + "."
    if shared.called_by_offline:
        # No long messages via offline communicators as Telegram API returns 400, too hard to read on FastAPI interfaces
        speaker.speak(text=formatted)
        return
    speaker.speak(text=f"{formatted}. Do you want me to continue {models.env.title}?", run=True)
    if response := listener.listen():
        if word_match.word_match(phrase=response, match_list=keywords.keywords.ok):
            speaker.speak(text=". ".join(result.split(". ")[3:]))
