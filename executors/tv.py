import os
import random
import sys
import time
from threading import Thread

import yaml

from executors.internet import vpn_checker
from executors.logger import logger
from modules.audio import speaker
from modules.conditions import conversation
from modules.models import models
from modules.tv.tv_controls import TV
from modules.utils import shared, support
from modules.wakeonlan import wakeonlan

env = models.env
fileio = models.fileio


def television(phrase: str) -> None:
    """Controls all actions on a TV (LG Web OS).

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

    if not all([smart_devices.get('tv_ip'), smart_devices.get('tv_mac'), env.tv_client_key]):
        support.no_env_vars()
        return

    power_controller = wakeonlan.WakeOnLan()
    phrase_exc = phrase.replace('TV', '')
    phrase_lower = phrase_exc.lower()

    def tv_status() -> int:
        """Pings the tv and returns the status. 0 if able to ping, 256 if unable to ping.

        Returns:
            int:
            Returns an integer value 0 if status succeeds else 512.
        """
        if env.mac:
            return os.system(f"ping -c 1 -t 3 {smart_devices.get('tv_ip')} >/dev/null")
        else:
            return os.system(f"ping -c 1 -t 3 {smart_devices.get('tv_ip')} > NUL")

    if ('turn off' in phrase_lower or 'shutdown' in phrase_lower or 'shut down' in phrase_lower) and tv_status() != 0:
        speaker.speak(text=f"I wasn't able to connect to your TV {env.title}! I guess your TV is powered off already.")
        return
    elif tv_status():
        if shared.called_by_offline:
            power_controller.create_packet(smart_devices.get('tv_mac'))
        else:
            Thread(target=power_controller.send_packet, args=[smart_devices.get('tv_mac')]).start()
            speaker.speak(text=f"Looks like your TV is powered off {env.title}! Let me try to turn it back on!",
                          run=True)

    for i in range(5):
        if not tv_status():
            break
        elif i == 4:  # checks if the TV is turned ON (thrice) even before launching the TV connector
            speaker.speak(text=f"I wasn't able to connect to your TV {env.title}! Please make sure you are on the "
                               "same network as your TV, and your TV is connected to a power source.")
            return
        time.sleep(1)

    if not shared.tv:
        try:
            shared.tv = TV(ip_address=smart_devices.get('tv_ip'), client_key=env.tv_client_key)
        except ConnectionResetError as error:
            logger.error(f"Failed to connect to the TV. {error}")
            speaker.speak(text=f"I was unable to connect to the TV {env.title}! It appears to be a connection issue. "
                               "You might want to try again later.")
            return
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speaker.speak(text=f"TV features have been integrated {env.title}!")
            return

    if shared.tv:
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speaker.speak(text=f'Your TV is already powered on {env.title}!')
        elif 'shutdown' in phrase_lower or 'shut down' in phrase_lower or 'turn off' in phrase_lower:
            Thread(target=shared.tv.shutdown).start()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning your TV off.')
            shared.tv = None
        elif 'increase' in phrase_lower:
            shared.tv.increase_volume()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'decrease' in phrase_lower or 'reduce' in phrase_lower:
            shared.tv.decrease_volume()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'mute' in phrase_lower:
            shared.tv.mute()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'stop' in phrase_lower and 'content' in phrase_lower:
            shared.tv.stop()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'stop' in phrase_lower or 'pause' in phrase_lower:
            shared.tv.pause()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'resume' in phrase_lower or 'play' in phrase_lower:
            shared.tv.play()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'rewind' in phrase_lower:
            shared.tv.rewind()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'forward' in phrase_lower:
            shared.tv.forward()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'set' in phrase_lower and 'volume' in phrase_lower:
            if vol := support.extract_nos(input_=phrase_lower, method=int):
                shared.tv.set_volume(target=vol)
                speaker.speak(text=f"I've set the volume to {vol}% {env.title}.")
            else:
                speaker.speak(text=f"{vol} doesn't match the right format {env.title}!")
        elif 'volume' in phrase_lower:
            speaker.speak(text=f"The current volume on your TV is, {shared.tv.get_volume()}%")
        elif 'app' in phrase_lower or 'application' in phrase_lower:
            sys.stdout.write(f'\r{shared.tv.get_apps()}')
            speaker.speak(text=f'App list on your screen {env.title}!', run=True)
            time.sleep(5)
        elif 'open' in phrase_lower or 'launch' in phrase_lower:
            cleaned = ' '.join([w for w in phrase.split() if w not in ['launch', 'open', 'tv', 'on', 'my', 'the']])
            app_name = support.get_closest_match(text=cleaned, match_list=shared.tv.get_apps())
            logger.info(f'{phrase} -> {app_name}')
            shared.tv.launch_app(app_name=app_name)
            speaker.speak(text=f"I've launched {app_name} on your TV {env.title}!")
        elif "what's" in phrase_lower or 'currently' in phrase_lower:
            speaker.speak(text=f'{shared.tv.current_app()} is running on your TV.')
        elif 'change' in phrase_lower or 'source' in phrase_lower:
            cleaned = ' '.join([word for word in phrase.split() if word not in ('set', 'the', 'source', 'on', 'my',
                                                                                'of', 'to', 'tv')])
            source = support.get_closest_match(text=cleaned, match_list=shared.tv.get_sources())
            logger.info(f'{phrase} -> {source}')
            shared.tv.set_source(val=source)
            speaker.speak(text=f"I've changed the source to {source}.")
        else:
            speaker.speak(text="I didn't quite get that.")
            Thread(target=support.unrecognized_dumper, args=[{'TV': phrase}]).start()
    else:
        phrase = phrase.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speaker.speak(text=f"I'm sorry {env.title}! I wasn't able to {phrase}, as the TV state is unknown!")
