import difflib
import warnings
from collections import OrderedDict
from multiprocessing.pool import ThreadPool
from typing import Callable

from jarvis.executors import files
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.utils import shared


def custom_conditions(phrase: str, function_map: OrderedDict[str, Callable]) -> bool:
    """Execute one or many functions based on custom conditions."""
    # todo:
    #   - make both async and non async requests as sent by offline
    #   - create internal flag to set/unset `called_by_offline` status
    #   - INVESTIGATE: 31:46: execution error: System Events got an error: Connection is invalid. (-609)
    #       - block and release print for events did not work, so it might not be the culprit
    if not (custom_mapping := files.get_custom_conditions()):
        return False
    executed = False
    for custom_phrase, task_map in custom_mapping.items():
        match = difflib.SequenceMatcher(a=phrase.lower(), b=custom_phrase.lower()).ratio()
        if match < 0.95:
            continue
        logger.info("'%s' matches with the custom condition '%s' at the rate: %.2f", phrase, custom_phrase, match)
        process_pool = []
        for function_, task_ in task_map.get('map', {}).items():
            if function_map.get(function_):
                executed = True
                if task_map.get('async', False):  # todo: async might not be possible in offline communicator
                    shared.called_by_offline = True  # silence speaker response for async request
                    process_pool.append(ThreadPool(processes=1).apply_async(func=function_map[function_],
                                                                            args=(task_,)))
                else:
                    function_map[function_](task_)  # todo: offline communicator will only get the last execution result
            else:
                warnings.warn("Custom condition map was found with incorrect function name: '%s'" % function_)
        if process_pool:
            results = []
            for process in process_pool:
                process.get()
                results.append(shared.text_spoken)
                shared.text_spoken = ""
            shared.called_by_offline = False  # release speaker functionality once results are gathered
            speaker.speak(text=". ".join(results))
    if executed:
        return True
    logger.debug("Custom map was present but did not match with the current request.")
