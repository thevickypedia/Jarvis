from typing import Iterable, NoReturn, Union


def word_match(phrase: str, match_list: Iterable[str], strict: bool = False) -> Union[str, NoReturn]:
    """Matches phrase to word list given.

    Args:
        phrase: Takes the phrase spoken as an argument.
        match_list: List or tuple of words against which the phrase has to be checked.
        strict: Look for the exact word match instead of regex.

    Returns:
        str:
        Returns the word that was matched.
    """
    if not phrase:
        return
    lookup = phrase.lower().split() if strict else phrase.lower()
    for word in match_list:
        if word in lookup:
            return word
