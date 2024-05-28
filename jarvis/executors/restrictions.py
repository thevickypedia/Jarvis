import string

from jarvis.executors import files, functions, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import InvalidArgument
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import util


def restricted(phrase: str) -> bool:
    """Check if phrase matches the category that's restricted.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        bool:
        Returns a boolean flag if the category (function name) is present in restricted functions.
    """
    if not (restricted_functions := files.get_restrictions()):
        logger.debug("No restrictions in place.")
        return False
    for category, identifiers in keywords.keywords.items():
        if word_match.word_match(phrase=phrase, match_list=identifiers):
            if category in restricted_functions:
                speaker.speak(
                    text=f"I'm sorry {models.env.title}! "
                    f"{string.capwords(category)} category is restricted via offline communicator."
                )
                return True


def get_func(phrase: str) -> str:
    """Extract function name from the phrase.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Raises:
        InvalidArgument:
        - If the phrase doesn't match any of the operations supported.

    Returns:
        str:
        Function name matching the existing function map.
    """
    phrase = phrase.replace("function", "").replace("method", "").strip()
    if "for" in phrase:
        func = phrase.split("for")[1].strip()
    elif "on" in phrase:
        func = phrase.split("on")[1].strip()
    elif "restrict" in phrase:
        func = phrase.split("restrict")[1].strip()
    elif "release" in phrase:
        func = phrase.split("release")[1].strip()
    else:
        raise InvalidArgument(
            "Please specify a valid function name to add or remove restrictions."
        )
    function_names = list(functions.function_mapping().keys())
    if func in function_names:
        return func
    raise InvalidArgument(f"No such function present. Valid: {function_names}")


def handle_restrictions(phrase: str) -> str:
    """Handles adding/removing restrictions for offline communicators.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Raises:
        InvalidArgument:
        - If the phrase doesn't match any of the operations supported.

    Returns:
        str:
        Returns the response as a string.
    """
    phrase = phrase.lower()
    current_restrictions = files.get_restrictions()
    if word_match.word_match(
        phrase=phrase, match_list=("get", "current", "exist", "present")
    ):
        if current_restrictions:
            return f"Current restrictions are: {util.comma_separator(current_restrictions)}"
        return "Currently, there are no restrictions for offline communicators."
    if "add" in phrase or "restrict" in phrase:
        func = get_func(phrase)
        if func in current_restrictions:
            return f"Restriction for {string.capwords(func)} is already in place {models.env.title}!"
        current_restrictions.append(func)
        files.put_restrictions(restrictions=current_restrictions)
        return f"{string.capwords(func)} has been added to restricted functions {models.env.title}!"
    if "release" in phrase or "remove" in phrase:
        func = get_func(phrase)
        if func in current_restrictions:
            current_restrictions.remove(func)
            files.put_restrictions(restrictions=current_restrictions)
            return f"{string.capwords(func)} has been removed from restricted functions {models.env.title}!"
        else:
            return f"Restriction for {string.capwords(func)} was never in place {models.env.title}!"
    raise InvalidArgument(
        "Please specify the function that has to be added or removed from the restrictions' list."
    )
