import warnings
from collections import OrderedDict
from typing import Callable

from jarvis.executors import files
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.utils import shared, util


def custom_conditions(phrase: str, function_map: OrderedDict[str, Callable]) -> bool:
    """Execute one or many functions based on custom conditions."""
    if not (custom_mapping := files.get_custom_conditions()):
        return False
    # noinspection PyTypeChecker
    closest_match = util.get_closest_match(text=phrase.lower(), match_list=custom_mapping.keys(), get_ratio=True)
    if closest_match['ratio'] < 0.9:
        return False
    custom_phrase = closest_match['text']
    task_map = custom_mapping[custom_phrase]
    logger.info("'%s' matches with the custom condition '%s' at the rate: %.2f",
                phrase, custom_phrase, closest_match['ratio'])
    executed = False
    if shared.called_by_offline:
        response = ""
        for function_, task_ in task_map.items():
            if function_map.get(function_):
                executed = True
                function_map[function_](task_)
                response += shared.text_spoken + "\n"
            else:
                warnings.warn("Custom condition map was found with incorrect function name: '%s'" % function_)
        if response:
            speaker.speak(text=response)
    else:
        for function_, task_ in task_map.items():
            if function_map.get(function_):
                executed = True
                function_map[function_](task_)
            else:
                warnings.warn("Custom condition map was found with incorrect function name: '%s'" % function_)
    if executed:
        return True
    logger.debug("Custom map was present but did not match with the current request.")
