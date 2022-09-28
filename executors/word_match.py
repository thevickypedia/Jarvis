import sys
from typing import Iterable, NoReturn, Union

from executors.logger import logger


def word_match(phrase: str, match_list: Iterable[str]) -> Union[str, NoReturn]:
    """Matches phrase to word list given.

    Args:
        phrase: Takes the spoken phrase in the form of list as an argument.
        match_list: List or tuple of words against which the phrase has to be checked.

    Returns:
        str:
        Returns the word that was matched.
    """
    for word in match_list:
        if word in phrase.lower():  # include .split() for an exact match of words instead of a regex
            caller = sys._getframe(1).f_code.co_name  # noqa
            if caller == 'auto_helper':
                return word
            logger.debug(f'Matching word: {word}')
            logger.debug(f'Called by {caller}')
            return word
