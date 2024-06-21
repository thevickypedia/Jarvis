# noinspection PyUnresolvedReferences
"""Module for keyword classification algorithm.

>>> KeywordClassifier

"""

from typing import List, Tuple


def reverse_lookup(lookup: str, match_list: List | Tuple) -> str | None:
    """Returns the word in phrase that matches the one in given list."""
    # extract multi worded conditions in match list
    reverse = sum([w.lower().split() for w in match_list], [])
    for word in lookup.split():  # loop through words in the phrase
        # check at least one word in phrase matches the multi worded condition
        if word in reverse:
            return word


def forward_lookup(lookup: str | List | Tuple, match_list: List | Tuple) -> str | None:
    """Returns the word in list that matches with the phrase given as string or list."""
    for word in match_list:
        if word.lower() in lookup:
            return word


def word_match(
    phrase: str, match_list: List | Tuple, strict: bool = False
) -> str | None:
    """Keyword classifier.

    Args:
        phrase: Takes the phrase spoken as an argument.
        match_list: List or tuple of words against which the phrase has to be checked.
        strict: Look for the exact word match instead of regex.

    Returns:
        str:
        Returns the word that was matched.
    """
    if not all((phrase, match_list)):
        return
    # simply check at least one string in the match list is present in phrase
    if strict:
        lookup = phrase.lower().split()
        return forward_lookup(lookup, match_list)
    else:
        lookup = phrase.lower()
        if (fl := forward_lookup(lookup, match_list)) and reverse_lookup(
            lookup, match_list
        ):
            return fl
