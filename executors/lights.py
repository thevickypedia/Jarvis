import os.path
import random
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

import yaml

from executors.internet import vpn_checker
from modules.audio import speaker
from modules.conditions import conversation
from modules.lights import preset_values, smart_lights
from modules.models import models
from modules.utils import globals, support

env = models.env


def lights(phrase: str) -> None:
    """Controller for smart lights.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    if not os.path.isfile('smart_devices.yaml'):
        support.no_env_vars()
        return

    with open('smart_devices.yaml') as file:
        smart_devices = yaml.load(stream=file, Loader=yaml.FullLoader)

    if not any([smart_devices.get('hallway_ip'), smart_devices.get('kitchen_ip'),
                smart_devices.get('bedroom_ip')]):
        support.no_env_vars()
        return

    if vpn_checker().startswith('VPN'):
        return

    phrase = phrase.lower()

    def light_switch() -> None:
        """Says a message if the physical switch is toggled off."""
        speaker.speak(text=f"I guess your light switch is turned off {env.title}! I wasn't able to read the device. "
                           "Try toggling the switch and ask me to restart myself!")

    def turn_off(host: str) -> None:
        """Turns off the device.

        Args:
            host: Takes target device IP address as an argument.
        """
        smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Turn Off').turn_off()

    def warm(host: str) -> None:
        """Sets lights to warm/yellow.

        Args:
            host: Takes target device IP address as an argument.
        """
        smart_lights.MagicHomeApi(device_ip=host, device_type=1,
                                  operation='Warm Lights').update_device(r=0, g=0, b=0, warm_white=255)

    def cool(host: str) -> None:
        """Sets lights to cool/white.

        Args:
            host: Takes target device IP address as an argument.
        """
        smart_lights.MagicHomeApi(device_ip=host, device_type=2,
                                  operation='Cool Lights').update_device(r=255, g=255, b=255, warm_white=255,
                                                                         cool_white=255)

    def preset(host: str, value: int) -> None:
        """Changes light colors to preset values.

        Args:
            host: Takes target device IP address as an argument.
            value: Preset value extracted from list of verified values.
        """
        smart_lights.MagicHomeApi(device_ip=host, device_type=2,
                                  operation='Preset Values').send_preset_function(preset_number=value, speed=101)

    def lumen(host: str, warm_lights: bool, rgb: int = 255) -> None:
        """Sets lights to custom brightness.

        Args:
            host: Takes target device IP address as an argument.
            warm_lights: Boolean value if lights have been set to warm or cool.
            rgb: Red, Green andBlue values to alter the brightness.
        """
        args = {'r': 255, 'g': 255, 'b': 255, 'warm_white': rgb}
        if not warm_lights:
            args.update({'cool_white': rgb})
        smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Custom Brightness').update_device(**args)

    if 'hallway' in phrase:
        if not (host_ip := smart_devices.get('hallway_ip')):
            light_switch()
            return
    elif 'kitchen' in phrase:
        if not (host_ip := smart_devices.get('kitchen_ip')):
            light_switch()
            return
    elif 'bedroom' in phrase:
        if not (host_ip := smart_devices.get('bedroom_ip')):
            light_switch()
            return
    else:
        host_ip = smart_devices.get('hallway_ip') + \
                  smart_devices.get('kitchen_ip') + \
                  smart_devices.get('bedroom_ip')  # noqa: E126

    lights_count = len(host_ip)

    def thread_worker(function_to_call: staticmethod) -> None:
        """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        with ThreadPoolExecutor(max_workers=lights_count) as executor:
            executor.map(function_to_call, host_ip)

    plural = 'lights!' if lights_count > 1 else 'light!'
    if 'turn on' in phrase or 'cool' in phrase or 'white' in phrase:
        globals.warm_light.pop('status') if globals.warm_light.get('status') else None
        tone = 'white' if 'white' in phrase else 'cool'
        if 'turn on' in phrase:
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning on {lights_count} {plural}')
        else:
            speaker.speak(
                text=f'{random.choice(conversation.acknowledgement)}! Setting {lights_count} {plural} to {tone}!')
        Thread(target=thread_worker, args=[cool]).start()
    elif 'turn off' in phrase:
        speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning off {lights_count} {plural}')
        Thread(target=thread_worker, args=[turn_off]).start()
    elif 'warm' in phrase or 'yellow' in phrase:
        globals.warm_light['status'] = True
        if 'yellow' in phrase:
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! '
                               f'Setting {lights_count} {plural} to yellow!')
        else:
            speaker.speak(text=f'Sure {env.title}! Setting {lights_count} {plural} to warm!')
        Thread(target=thread_worker, args=[warm]).start()
    elif any(word in phrase for word in list(preset_values.PRESET_VALUES.keys())):
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I've changed {lights_count} {plural} to red!")
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
            if level := re.findall(r'\b\d+\b', phrase):
                level = int(level[0])
            else:
                level = 100
        speaker.speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I've set {lights_count} {plural} to {level}%!")
        level = round((255 * level) / 100)
        for light_ip in host_ip:
            lumen(host=light_ip, warm_lights=globals.warm_light.get('status'), rgb=level)
    else:
        speaker.speak(text=f"I didn't quite get that {env.title}! What do you want me to do to your {plural}?")
        Thread(target=support.unrecognized_dumper, args=[{'LIGHTS': phrase}]).start()
