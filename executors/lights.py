import os.path
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import Callable, NoReturn, Union

import yaml

from executors.internet import vpn_checker
from executors.logger import logger
from modules.audio import speaker
from modules.conditions import conversation
from modules.lights import preset_values, smart_lights
from modules.models import models
from modules.utils import shared, support

env = models.env
fileio = models.fileio


def lights(phrase: str) -> Union[None, NoReturn]:
    """Controller for smart lights.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    if not vpn_checker():
        return

    if not os.path.isfile(fileio.smart_devices):
        support.no_env_vars()
        return

    with open(fileio.smart_devices) as file:
        smart_devices = yaml.load(stream=file, Loader=yaml.FullLoader)

    if not any(smart_devices):
        support.no_env_vars()
        return

    phrase = phrase.lower()

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

    def preset(host: str, value: int) -> NoReturn:
        """Changes light colors to preset values.

        Args:
            host: Takes target device IP address as an argument.
            value: Preset value extracted from list of verified values.
        """
        smart_lights.MagicHomeApi(device_ip=host, device_type=2,
                                  operation='Preset Values').send_preset_function(preset_number=value, speed=101)

    def lumen(host: str, rgb: int = 255) -> NoReturn:
        """Sets lights to custom brightness.

        Args:
            host: Takes target device IP address as an argument.
            rgb: Red, Green andBlue values to alter the brightness.
        """
        args = {'r': 255, 'g': 255, 'b': 255, 'warm_white': rgb}
        smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Custom Brightness').update_device(**args)

    if 'all' in phrase:
        host_ip = [value for key, value in smart_devices.items()
                   if isinstance(value, list)]  # Checking for list since lights are inserted as a list and tv as string
    else:
        host_ip = [smart_devices.get(each) for each in list(smart_devices.keys())
                   if any(word in phrase.lower() for word in each.replace('_', ' ').replace('room', '').split())]

    if not host_ip:
        Thread(target=support.unrecognized_dumper, args=[{'LIGHTS': phrase}]).start()
        speaker.speak(text=f"I'm not sure which lights you meant {env.title}!")
        return
    host_ip = support.matrix_to_flat_list(input_=host_ip)

    def avail_check(function_to_call: Callable) -> NoReturn:
        """Speaks an error message if any of the lights aren't reachable.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        status = ThreadPool(processes=1).apply_async(func=thread_worker, args=[function_to_call])
        speaker.speak(run=True)
        if failed := status.get(timeout=5):
            plural_ = "lights aren't available right now!" if failed > 1 else "light isn't available right now!"
            speaker.speak(text=f"I'm sorry sir! {support.number_to_words(input_=failed, capitalize=True)} {plural_}")

    def thread_worker(function_to_call: Callable) -> int:
        """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        futures = {}
        executor = ThreadPoolExecutor(max_workers=len(host_ip))
        with executor:
            for iterator in host_ip:
                future = executor.submit(function_to_call, iterator)
                futures[future] = iterator

        thread_except = 0
        for future in as_completed(futures):
            if future.exception():
                thread_except += 1
                logger.error(f'Thread processing for {iterator} received an exception: {future.exception()}')
        return thread_except

    plural = 'lights!' if len(host_ip) > 1 else 'light!'
    if 'turn on' in phrase or 'cool' in phrase or 'white' in phrase:
        tone = 'white' if 'white' in phrase else 'cool'
        if 'turn on' in phrase:
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning on {len(host_ip)} {plural}')
        else:
            speaker.speak(
                text=f'{random.choice(conversation.acknowledgement)}! Setting {len(host_ip)} {plural} to {tone}!'
            )
        Thread(target=thread_worker, args=[cool]).start() if shared.called_by_offline else \
            avail_check(function_to_call=cool)
    elif 'turn off' in phrase:
        speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning off {len(host_ip)} {plural}')
        Thread(target=thread_worker, args=[cool]).run()
        Thread(target=thread_worker, args=[turn_off]).start() if shared.called_by_offline else \
            avail_check(function_to_call=turn_off)
    elif 'warm' in phrase or 'yellow' in phrase:
        if 'yellow' in phrase:
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! '
                               f'Setting {len(host_ip)} {plural} to yellow!')
        else:
            speaker.speak(text=f'Sure {env.title}! Setting {len(host_ip)} {plural} to warm!')
        Thread(target=thread_worker, args=[warm]).start() if shared.called_by_offline else \
            avail_check(function_to_call=warm)
    elif any(word in phrase for word in list(preset_values.PRESET_VALUES.keys())):
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I've changed {len(host_ip)} {plural} to red!")
        for light_ip in host_ip:
            preset(host=light_ip,
                   value=[preset_values.PRESET_VALUES[_type] for _type in
                          list(preset_values.PRESET_VALUES.keys()) if _type in phrase][0])
    elif 'set' in phrase or 'percentage' in phrase or '%' in phrase or 'dim' in phrase \
            or 'bright' in phrase:
        if 'bright' in phrase:
            level = 100
        elif 'dim' in phrase:
            level = 50
        else:
            level = support.extract_nos(input_=phrase, method=int) or 100
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I've set {len(host_ip)} {plural} to {level}%!")
        level = round((255 * level) / 100)
        for light_ip in host_ip:
            lumen(host=light_ip, rgb=level)
    else:
        speaker.speak(text=f"I didn't quite get that {env.title}! What do you want me to do to your {plural}?")
        Thread(target=support.unrecognized_dumper, args=[{'LIGHTS': phrase}]).start()
