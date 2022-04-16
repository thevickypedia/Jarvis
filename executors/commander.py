import random
import time
from multiprocessing import Process
from threading import Thread
from typing import Union

from executors.conditions import conditions
from executors.controls import pc_sleep
from executors.logger import logger
from executors.offline import offline_communicator
from executors.others import time_travel
from modules.audio import listener, speaker
from modules.conditions import conversation, keywords
from modules.models import models
from modules.offline import compatibles
from modules.utils import shared, support

env = models.env
offline_list = compatibles.offline_compatible()


def split_phrase(phrase: str, should_return: bool = False) -> bool:
    """Splits the input at 'and' or 'also' and makes it multiple commands to execute if found in statement.

    Args:
        phrase: Takes the phrase spoken as an argument.
        should_return: A boolean flag sent to ``conditions`` to indicate that the ``else`` part shouldn't be executed.

    Returns:
        bool:
        Return value from ``conditions()``
    """
    exit_check = False  # this is specifically to catch the sleep command which should break the while loop in renew()

    if ' after ' in phrase:
        if timed_delay(phrase=phrase):
            return False

    if ' and ' in phrase and not any(word in phrase.lower() for word in keywords.avoid):
        for each in phrase.split(' and '):
            exit_check = conditions(converted=each.strip(), should_return=should_return)
            speaker.speak(run=True)
    elif ' also ' in phrase and not any(word in phrase.lower() for word in keywords.avoid):
        for each in phrase.split(' also '):
            exit_check = conditions(converted=each.strip(), should_return=should_return)
            speaker.speak(run=True)
    else:
        exit_check = conditions(converted=phrase.strip(), should_return=should_return)
    return exit_check


def delay_calculator(phrase: str) -> Union[int, float]:
    """Calculates the delay in phrase (if any).

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        int:
        Seconds of delay.
    """
    if not (count := support.extract_nos(input_=phrase)):
        count = 1
    if 'hour' in phrase:
        delay = 3_600
    elif 'minute' in phrase:
        delay = 60
    elif 'second' in phrase:
        delay = 1
    else:
        delay = 0
    return count * delay


def delay_condition(phrase: str, delay: Union[int, float]) -> None:
    """Delays the execution after sleeping for the said time, after which it is sent to ``offline_communicator``.

    Args:
        phrase: Takes the phrase spoken as an argument.
        delay: Sleeps for the number of seconds.
    """
    logger.info(f"'{phrase}' will be executed after {support.time_converter(seconds=delay)}")
    time.sleep(delay)
    logger.info(f"Executing '{phrase}'")
    offline_communicator(command=phrase)


def timed_delay(phrase: str) -> bool:
    """Checks pre-conditions if a delay is necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        bool:
        Returns a boolean flag whether the time delay should be applied.
    """
    if any(word in phrase.lower() for word in offline_list) and \
            not any(word in phrase.lower() for word in keywords.set_alarm) and \
            not any(word in phrase.lower() for word in keywords.reminder):
        split_ = phrase.split('after')
        if split_[0].strip():
            delay = delay_calculator(phrase=split_[1].strip())
            Process(target=delay_condition, kwargs={'phrase': split_[0].strip(), 'delay': delay}).start()
            speaker.speak(text=f"I will execute it after {support.time_converter(seconds=delay)} {env.title}!")
            return True


def initialize() -> None:
    """Awakens from sleep mode. ``greet_check`` is to ensure greeting is given only for the first function call."""
    if shared.greeting:
        speaker.speak(text="What can I do for you?")
    else:
        speaker.speak(text=f'Good {support.part_of_day()}.')
        shared.greeting = True
    renew()


def renew() -> None:
    """Keeps listening and sends the response to ``conditions()`` function.

    Notes:
        - This function runs only for a minute.
        - split_phrase(converted) is a condition so that, loop breaks when if sleep in ``conditions()`` returns True.
    """
    speaker.speak(run=True)
    waiter = 0
    while waiter < 12:
        waiter += 1
        if waiter == 1:
            converted = listener.listen(timeout=3, phrase_limit=5)
        else:
            converted = listener.listen(timeout=3, phrase_limit=5, sound=False)
        if converted == 'SR_ERROR':
            continue
        remove = ['buddy', 'jarvis', 'hey', 'hello', 'sr_error']
        converted = ' '.join([i for i in converted.split() if i.lower() not in remove])
        if converted:
            if split_phrase(phrase=converted):  # should_return flag is not passed which will default to False
                break  # split_phrase() returns a boolean flag from conditions. conditions return True only for sleep
        elif any(word in converted.lower() for word in remove):
            continue
        speaker.speak(run=True)


def initiator(phrase: str, should_return: bool = False) -> None:
    """When invoked by ``Activator``, checks for the right keyword to wake up and gets into action.

    Args:
        phrase: Takes the processed string from ``SentryMode`` as input.
        should_return: Flag to return the function if nothing is heard.
    """
    if phrase == 'SR_ERROR' and should_return:
        return
    support.flush_screen()
    if [word for word in phrase.lower().split() if word in ['morning', 'night', 'afternoon',
                                                            'after noon', 'evening', 'goodnight']]:
        shared.called['time_travel'] = True
        if (event := support.celebrate()) and 'night' not in phrase.lower():
            speaker.speak(text=f'Happy {event}!')
        if 'night' in phrase.split() or 'goodnight' in phrase.split():
            Thread(target=pc_sleep).start() if env.mac else None
        time_travel()
        shared.called['time_travel'] = False
    elif 'you there' in phrase.lower() or any(word in phrase.lower() for word in env.legacy_keywords):
        speaker.speak(text=f'{random.choice(conversation.wake_up1)}')
        initialize()
    elif any(word in phrase.lower() for word in ['look alive', 'wake up', 'wakeup', 'show time', 'showtime']):
        speaker.speak(text=f'{random.choice(conversation.wake_up2)}')
        initialize()
    else:
        if phrase:
            split_phrase(phrase=phrase, should_return=should_return)
        else:
            speaker.speak(text=f'{random.choice(conversation.wake_up3)}')
            initialize()
