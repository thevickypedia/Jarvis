# noinspection PyUnresolvedReferences
"""Module for keyword classification algorithm.

>>> KeywordClassifier

"""

from typing import List, NoReturn, Tuple, Union


def reverse_lookup(lookup: str,
                   match_list: Union[List, Tuple]) -> Union[str, NoReturn]:
    """Returns the word in phrase that matches the one in given list."""
    reverse = sum([w.lower().split() for w in match_list], [])  # extract multi worded conditions in match list
    for word in lookup.split():  # loop through words in the phrase
        if word in reverse:  # check at least one word in phrase matches the multi worded condition
            return word


def forward_lookup(lookup: Union[str, List, Tuple],
                   match_list: Union[List, Tuple]) -> Union[str, NoReturn]:
    """Returns the word in list that matches with the phrase given as string or list."""
    for word in match_list:
        if word.lower() in lookup:
            return word


def word_match(phrase: str,
               match_list: Union[List, Tuple],
               strict: bool = False) -> Union[str, NoReturn]:
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
    if strict:  # simply check at least one string in the match list is present in phrase
        lookup = phrase.lower().split()
        return forward_lookup(lookup, match_list)
    else:
        lookup = phrase.lower()
        if (fl := forward_lookup(lookup, match_list)) and reverse_lookup(lookup, match_list):
            return fl
