import os
import random
import re
import sys
from threading import Thread
from time import sleep

from wakeonlan import send_magic_packet

from executors.internet import vpn_checker
from executors.logger import logger
from modules.audio import speaker
from modules.conditions import conversation
from modules.tv.tv_controls import TV
from modules.utils import globals, support

env = globals.ENV


def television(phrase: str) -> None:
    """Controls all actions on a TV (LG Web OS).

    Notes:
        - In the ``__main__`` method tv is set to None.
        - Jarvis will try to ping the TV and then power it on if the host is unreachable initially.
        - Once the tv is turned on, the TV class is also initiated and assigned to tv variable.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    if not all([globals.smart_devices.get('tv_ip'), globals.smart_devices.get('tv_mac'), env.tv_client_key]):
        support.no_env_vars()
        return

    phrase_exc = phrase.replace('TV', '')
    phrase_lower = phrase_exc.lower()

    def tv_status() -> int:
        """Pings the tv and returns the status. 0 if able to ping, 256 if unable to ping."""
        return os.system(f"ping -c 1 -t 3 {globals.smart_devices.get('tv_ip')} >/dev/null")

    if vpn_checker().startswith('VPN'):
        return
    elif ('turn off' in phrase_lower or 'shutdown' in phrase_lower or 'shut down' in phrase_lower) and tv_status() != 0:
        speaker.speak(text="I wasn't able to connect to your TV sir! I guess your TV is powered off already.")
        return
    elif tv_status():
        if globals.called_by_offline['status']:
            send_magic_packet(globals.smart_devices.get('tv_mac'))
        else:
            Thread(target=send_magic_packet, args=[globals.smart_devices.get('tv_mac')]).start()
            speaker.speak(text="Looks like your TV is powered off sir! Let me try to turn it back on!", run=True)

    for i in range(5):
        if not tv_status():
            break
        elif i == 4:  # checks if the TV is turned ON (thrice) even before launching the TV connector
            speaker.speak(text="I wasn't able to connect to your TV sir! Please make sure you are on the "
                               "same network as your TV, and your TV is connected to a power source.")
            return
        sleep(1)

    if not globals.tv:
        try:
            globals.tv = TV(ip_address=globals.smart_devices.get('tv_ip'), client_key=env.tv_client_key)
        except ConnectionResetError as error:
            logger.error(f"Failed to connect to the TV. {error}")
            speaker.speak(text="I was unable to connect to the TV sir! It appears to be a connection issue. "
                               "You might want to try again later.")
            return
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speaker.speak(text="TV features have been integrated sir!")
            return

    if globals.tv:
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speaker.speak(text='Your TV is already powered on sir!')
        elif 'increase' in phrase_lower:
            globals.tv.increase_volume()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'decrease' in phrase_lower or 'reduce' in phrase_lower:
            globals.tv.decrease_volume()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'mute' in phrase_lower:
            globals.tv.mute()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'pause' in phrase_lower or 'boss' in phrase_lower or 'pass' in phrase_lower or 'hold' in phrase_lower:
            globals.tv.pause()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'resume' in phrase_lower or 'play' in phrase_lower:
            globals.tv.play()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'rewind' in phrase_lower:
            globals.tv.rewind()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'forward' in phrase_lower:
            globals.tv.forward()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'stop' in phrase_lower:
            globals.tv.stop()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'set' in phrase_lower and 'volume' in phrase_lower:
            vol = int(''.join([str(s) for s in re.findall(r'\b\d+\b', phrase_exc)]))
            if vol:
                globals.tv.set_volume(target=vol)
                speaker.speak(text=f"I've set the volume to {vol}% sir.")
            else:
                speaker.speak(text=f"{vol} doesn't match the right format sir!")
        elif 'volume' in phrase_lower:
            speaker.speak(text=f"The current volume on your TV is, {globals.tv.get_volume()}%")
        elif 'app' in phrase_lower or 'application' in phrase_lower:
            sys.stdout.write(f'\r{globals.tv.get_apps()}')
            speaker.speak(text='App list on your screen sir!', run=True)
            sleep(5)
        elif 'open' in phrase_lower or 'launch' in phrase_lower:
            cleaned = ' '.join([w for w in phrase.split() if w not in ['launch', 'open', 'tv', 'on', 'my', 'the']])
            app_name = support.get_closest_match(text=cleaned, match_list=globals.tv.get_apps())
            logger.info(f'{phrase} -> {app_name}')
            globals.tv.launch_app(app_name=app_name)
            speaker.speak(text=f"I've launched {app_name} on your TV sir!")
        elif "what's" in phrase_lower or 'currently' in phrase_lower:
            speaker.speak(text=f'{globals.tv.current_app()} is running on your TV.')
        elif 'change' in phrase_lower or 'source' in phrase_lower:
            cleaned = ' '.join([word for word in phrase.split() if word not in ('set', 'the', 'source', 'on', 'my',
                                                                                'of', 'to', 'tv')])
            source = support.get_closest_match(text=cleaned, match_list=globals.tv.get_sources())
            logger.info(f'{phrase} -> {source}')
            globals.tv.set_source(val=source)
            speaker.speak(text=f"I've changed the source to {source}.")
        elif 'shutdown' in phrase_lower or 'shut down' in phrase_lower or 'turn off' in phrase_lower:
            Thread(target=globals.tv.shutdown).start()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning your TV off.')
            globals.tv = None
        else:
            speaker.speak(text="I didn't quite get that.")
            Thread(target=support.unrecognized_dumper, args=[{'TV': phrase}]).start()
    else:
        phrase = phrase.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speaker.speak(text=f"I'm sorry sir! I wasn't able to {phrase}, as the TV state is unknown!")
