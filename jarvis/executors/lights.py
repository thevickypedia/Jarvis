import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import Callable, List, NoReturn, Union

import yaml

from jarvis.executors import internet, lights_squire, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.lights import preset_values, smart_lights
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support, util


def turn_off(host: str) -> NoReturn:
    """Turns off the device.

    Args:
        host: Takes target device IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Turn Off').turn_off()


def warm(host: str) -> NoReturn:
    """Sets lights to warm/yellow.

    Args:
        host: Takes target device IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=1,
                              operation='Warm Lights').update_device(r=0, g=0, b=0, warm_white=255)


def cool(host: str) -> NoReturn:
    """Sets lights to cool/white.

    Args:
        host: Takes target device IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=2,
                              operation='Cool Lights').update_device(r=255, g=255, b=255, warm_white=255,
                                                                     cool_white=255)


def lumen(host: str, rgb: int = 255) -> NoReturn:
    """Sets lights to custom brightness.

    Args:
        host: Takes target device IP address as an argument.
        rgb: Red, Green andBlue values to alter the brightness.
    """
    args = {'r': 255, 'g': 255, 'b': 255, 'warm_white': rgb}
    smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Custom Brightness').update_device(**args)


class ThreadExecutor:
    """Instantiates ``ThreadExecutor`` object to control the lights using pool of threads.

    >>> ThreadExecutor

    """

    def __init__(self, host_ip: List[str]):
        """Initializes the class and assign object members."""
        self.host_ip = host_ip

    def thread_worker(self, function_to_call: Callable) -> int:
        """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        futures = {}
        executor = ThreadPoolExecutor(max_workers=len(self.host_ip))
        with executor:
            for iterator in self.host_ip:
                future = executor.submit(function_to_call, iterator)
                futures[future] = iterator

        thread_except = 0
        for future in as_completed(futures):
            if future.exception():
                thread_except += 1
                logger.error("Thread processing for '%s' received an exception: %s", iterator, future.exception())
        return thread_except

    def avail_check(self, function_to_call: Callable) -> NoReturn:
        """Speaks an error message if any of the lights aren't reachable.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        status = ThreadPool(processes=1).apply_async(func=self.thread_worker, args=[function_to_call])
        speaker.speak(run=True)
        if failed := status.get(timeout=5):
            plural_ = "lights aren't available right now!" if failed > 1 else "light isn't available right now!"
            speaker.speak(text=f"I'm sorry sir! {support.number_to_words(input_=failed, capitalize=True)} {plural_}")


def lights(phrase: str) -> Union[None, NoReturn]:
    """Controller for smart lights.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not internet.vpn_checker():
        return

    if not os.path.isfile(models.fileio.smart_devices):
        logger.warning("%s not found.", models.fileio.smart_devices)
        support.no_env_vars()
        return

    try:
        with open(models.fileio.smart_devices) as file:
            smart_devices = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
            if smart_devices:
                smart_devices = {key: value for key, value in smart_devices.items() if 'tv' not in key.lower()}
    except yaml.YAMLError as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to read the source information. "
                           "Please check the logs.")
        return

    if not any(smart_devices):
        logger.warning("'%s' is empty for lights.", models.fileio.smart_devices)
        support.no_env_vars()
        return

    phrase = phrase.lower()

    if 'all' in phrase.split():
        # Checking for list since lights are inserted as a list and tv as string
        host_names = [value for key, value in smart_devices.items() if isinstance(value, list)]
        light_location = ""

    # # FUTURE: Works only for same operation - Implementing different operations is too much work with little to gain
    # # FUTURE: Add 'keywords' for 'lights' to 'ignore_and' var
    # elif 'and' in phrase.split():
    #     host_names, light_location = [], []
    #     for section in phrase.split(' and '):
    #         light_location_section = util.get_closest_match(text=section, match_list=list(smart_devices.keys()))
    #         host_names.append(smart_devices.get(light_location_section))
    #         light_location.append(light_location_section.replace('_', ' ').replace('-', ''))
    #     light_location = " and ".join(light_location)
    #     logger.info("Lights location: %s", light_location)

    else:
        # Get the closest matching name provided in smart_devices.yaml compared to what's requested by the user
        light_location = util.get_closest_match(text=phrase, match_list=list(smart_devices.keys()))
        logger.info("Lights location: %s", light_location)
        host_names = [smart_devices.get(light_location)]
        light_location = light_location.replace('_', ' ').replace('-', '')

    host_names = util.matrix_to_flat_list(input_=host_names)
    host_names = list(filter(None, host_names))  # remove None values
    if light_location and not host_names:
        logger.warning("No hostname values found for %s in %s", light_location, models.fileio.smart_devices)
        speaker.speak(text=f"I'm sorry {models.env.title}! You haven't mentioned the host names of {light_location!r} "
                           "lights.")
        return
    if not host_names:
        Thread(target=support.unrecognized_dumper, args=[{'LIGHTS': phrase}]).start()
        speaker.speak(text=f"I'm not sure which lights you meant {models.env.title}!")
        return

    host_names = util.remove_duplicates(input_=host_names)  # duplicates occur when party mode is present
    host_ip = [support.hostname_to_ip(hostname=hostname) for hostname in host_names]
    # host_ip = list(filter(None, host_ip))
    host_ip = util.matrix_to_flat_list(input_=host_ip)
    if not host_ip:
        plural = 'lights' if len(host_names) > 1 else 'light'
        speaker.speak(text=f"I wasn't able to connect to your {light_location} {plural} {models.env.title}! "
                           f"{support.number_to_words(input_=len(host_names), capitalize=True)} {plural} appear to be "
                           "powered off.")
        return

    executor = ThreadExecutor(host_ip=host_ip)

    plural = 'lights' if len(host_ip) > 1 else 'light'
    if 'turn on' in phrase or 'cool' in phrase or 'white' in phrase:
        tone = 'white' if 'white' in phrase else 'cool'
        if 'turn on' in phrase:
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning on {len(host_ip)} {plural}')
        else:
            speaker.speak(
                text=f'{random.choice(conversation.acknowledgement)}! Setting {len(host_ip)} {plural} to {tone}!'
            )
        executor.avail_check(function_to_call=cool)
    elif 'turn off' in phrase:
        speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning off {len(host_ip)} {plural}')
        if state := lights_squire.check_status():
            support.stop_process(pid=int(state[0]))
        if 'just' in phrase or 'simply' in phrase:
            executor.avail_check(function_to_call=turn_off)
        else:
            Thread(target=executor.thread_worker, args=[cool]).run()
            executor.avail_check(function_to_call=turn_off)
    elif 'party mode' in phrase:
        if lights_squire.party_mode(host_ip=host_ip, phrase=phrase):
            Thread(target=executor.thread_worker, args=[cool]).run()
            time.sleep(1)
            Thread(target=executor.thread_worker, args=[turn_off]).start()
    elif 'warm' in phrase or 'yellow' in phrase:
        if 'yellow' in phrase:
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! '
                               f'Setting {len(host_ip)} {plural} to yellow!')
        else:
            speaker.speak(text=f'Sure {models.env.title}! Setting {len(host_ip)} {plural} to warm!')
        executor.avail_check(function_to_call=warm)
    elif color := word_match.word_match(phrase=phrase, match_list=list(preset_values.PRESET_VALUES.keys())):
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I've changed {len(host_ip)} {plural} to {color}!")
        for light_ip in host_ip:
            lights_squire.preset(device_ip=light_ip, speed=50,
                                 color=[preset_values.PRESET_VALUES[_type] for _type in
                                        list(preset_values.PRESET_VALUES.keys()) if _type in phrase][0])
    elif 'set' in phrase or 'percentage' in phrase or '%' in phrase or 'dim' in phrase \
            or 'bright' in phrase:
        if 'bright' in phrase:
            level = 100
        elif 'dim' in phrase:
            level = 50
        else:
            level = util.extract_nos(input_=phrase, method=int)
            if level is None:
                level = 100
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I've set {len(host_ip)} {plural} to {level}%!")
        level = round((255 * level) / 100)
        Thread(target=executor.thread_worker, args=[turn_off]).run()
        time.sleep(1)
        for light_ip in host_ip:
            lumen(host=light_ip, rgb=level)
    else:
        speaker.speak(text=f"I didn't quite get that {models.env.title}! What do you want me to do to your "
                           f"{light_location} {plural}?")
        Thread(target=support.unrecognized_dumper, args=[{'LIGHTS': phrase}]).start()
