import random
import time
import traceback
from multiprocessing import Process
from threading import Thread
from typing import Tuple, Union

from jarvis.executors import (conditions, controls, listener_controls, offline,
                              others, word_match)
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import conversation, keywords
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util


def split_phrase(phrase: str) -> 'conditions.conditions':
    """Splits the input at 'and' or 'also' and makes it multiple commands to execute if found in statement.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        conditions.conditions:
        Return value from ``conditions()``
    """
    exit_check = False  # this is specifically to catch the sleep command which should break the loop in renew()

    if ' after ' in phrase and not word_match.word_match(phrase=phrase, match_list=keywords.ignore_after):
        if delay_info := timed_delay(phrase=phrase):
            speaker.speak(text=f"I will execute it after {support.time_converter(second=delay_info[1])} "
                               f"{models.env.title}!")
            return False

    if ' and ' in phrase and not word_match.word_match(phrase=phrase, match_list=keywords.ignore_and):
        for each in phrase.split(' and '):
            exit_check = conditions.conditions(phrase=each.strip())
            speaker.speak(run=True)
    else:
        exit_check = conditions.conditions(phrase=phrase.strip())
    return exit_check


def delay_condition(phrase: str, delay: Union[int, float]) -> None:
    """Delays the execution after sleeping for the said time, after which it is sent to ``offline_communicator``.

    Args:
        phrase: Takes the phrase spoken as an argument.
        delay: Sleeps for the number of seconds.
    """
    logger.info("'%s' will be executed after %s", phrase, support.time_converter(second=delay))
    time.sleep(delay)
    logger.info("Executing '%s'", phrase)
    try:
        offline.offline_communicator(command=phrase)
    except Exception as error:
        logger.error(error)
        logger.error(traceback.format_exc())


def timed_delay(phrase: str) -> Tuple[str, Union[int, float]]:
    """Checks pre-conditions if a delay is necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        bool:
        Returns a boolean flag whether the time delay should be applied.
    """
    if not word_match.word_match(phrase=phrase, match_list=keywords.keywords['set_alarm']) and \
            not word_match.word_match(phrase=phrase, match_list=keywords.keywords['reminder']):
        split_ = phrase.split('after')
        if task := split_[0].strip():
            delay = util.delay_calculator(phrase=split_[1].strip())
            Process(target=delay_condition, kwargs={'phrase': task, 'delay': delay}).start()
            return task, delay


def initialize() -> None:
    """Awakens from sleep mode. ``greet_check`` is to ensure greeting is given only for the first function call."""
    if shared.greeting:
        speaker.speak(text="What can I do for you?")
    else:
        speaker.speak(text=f'Good {util.part_of_day()}.')
        shared.greeting = True
    speaker.speak(run=True)
    renew()


def renew() -> None:
    """Keeps listening and sends the response to ``conditions()`` function.

    Notes:
        - This function runs only for a minute.
        - split_phrase(converted) is a condition so that, loop breaks when if sleep in ``conditions()`` returns True.
    """
    for i in range(3):
        if i:
            converted = listener.listen(sound=False) or ""
        else:
            converted = listener.listen() or ""
        if word_match.word_match(phrase=converted, match_list=models.env.wake_words):
            continue
        if split_phrase(phrase=converted):  # should_return flag is not passed which will default to False
            break  # split_phrase() returns a boolean flag from conditions. conditions return True only for sleep
        speaker.speak(run=True)


def initiator(phrase: str = None) -> None:
    """When invoked by ``Activator``, checks for the right keyword to wake up and gets into action.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not phrase:
        return
    support.flush_screen()
    inactive_msg = f"My listeners are currently inactive {models.env.title}!"
    if 'good' in phrase.lower() and word_match.word_match(
            phrase=phrase, match_list=('morning', 'night', 'afternoon', 'after noon', 'evening', 'goodnight')
    ):
        if not listener_controls.get_listener_state():
            speaker.speak(text=inactive_msg)
            return
        shared.called['time_travel'] = True
        if (event := support.celebrate()) and 'night' not in phrase.lower():
            speaker.speak(text=f'Happy {event}!')
        if 'night' in phrase.split() or 'goodnight' in phrase.split():
            Thread(target=controls.sleep_control).start()
        others.time_travel()
        shared.called['time_travel'] = False
    elif 'you there' in phrase.lower() or word_match.word_match(phrase=phrase, match_list=models.env.wake_words):
        if not listener_controls.get_listener_state():
            speaker.speak(text=inactive_msg)
            return
        speaker.speak(text=random.choice(conversation.wake_up1))
        initialize()
    elif word_match.word_match(phrase=phrase, match_list=('look alive', 'wake up', 'wakeup',
                                                          'show time', 'showtime')):
        if not listener_controls.get_listener_state():
            speaker.speak(text=inactive_msg)
            return
        speaker.speak(text=random.choice(conversation.wake_up2))
        initialize()
    else:
        if phrase:
            split_phrase(phrase=phrase)
        elif listener_controls.get_listener_state():
            speaker.speak(text=random.choice(conversation.wake_up3))
            initialize()
        else:
            speaker.speak(text=inactive_msg)
