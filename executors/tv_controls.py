import random
import sys
import time
from threading import Thread

from modules.audio import speaker
from modules.conditions import conversation
from modules.exceptions import TVError
from modules.logger.custom_logger import logger
from modules.models import models
from modules.tv import lg, roku
from modules.utils import shared, support, util


def tv_controller(phrase: str, tv_ip: str, identifier: str, nickname: str, client_key: str = None) -> None:
    """Controls all actions for Roku or LG WebOS tv.

    Args:
        phrase: Takes the voice recognized statement as argument.
        tv_ip: IP address of the television.
        identifier: String to control roku or LG WebOS.
        nickname: Name as in the source yaml file.
        client_key: Client key to connect to the LG WebOS tv.
    """
    phrase_lower = phrase.replace('TV', '').lower()

    if not shared.tv:
        try:
            if identifier == 'LG':
                shared.tv = lg.TV(ip_address=tv_ip, client_key=client_key)
            elif identifier == 'ROKU':
                shared.tv = roku.TV(ip_address=tv_ip)
                if not shared.tv.current_app():
                    shared.tv.startup()
        except TVError as error:
            logger.error(f"Failed to connect to the TV. {error}")
            speaker.speak(text=f"I was unable to connect to the {nickname} {models.env.title}! "
                               f"It appears to be a connection issue. You might want to try again later.")
            return
        else:
            if 'turn on' in phrase_lower or 'connect' in phrase_lower:
                speaker.speak(text=f"TV features have been integrated {models.env.title}!")
                return

    if shared.tv:
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speaker.speak(text=f'Your {nickname} is already powered on {models.env.title}!')
        elif 'shutdown' in phrase_lower or 'shut down' in phrase_lower or 'turn off' in phrase_lower:
            Thread(target=shared.tv.shutdown).start()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning your {nickname} off.')
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
            vol = support.extract_nos(input_=phrase_lower, method=int)
            if vol is None:
                speaker.speak(text=f"Requested volume doesn't match the right format {models.env.title}!")
            else:
                shared.tv.set_volume(target=vol)
                speaker.speak(text=f"I've set the volume to {vol}% {models.env.title}.")
        elif 'volume' in phrase_lower:
            speaker.speak(text=f"The current volume on your {nickname} is, {shared.tv.get_volume()}%")
        elif 'app' in phrase_lower or 'application' in phrase_lower:
            sys.stdout.write(f'\r{shared.tv.get_apps()}')
            speaker.speak(text=f'App list on your screen {models.env.title}!', run=True)
            time.sleep(5)
        elif 'open' in phrase_lower or 'launch' in phrase_lower:
            cleaned = ' '.join([w for w in phrase.split() if w not in ['launch', 'open', 'tv', 'on', 'my', 'the']])
            app_name = util.get_closest_match(text=cleaned, match_list=shared.tv.get_apps())
            logger.info(f'{phrase} -> {app_name}')
            shared.tv.launch_app(app_name=app_name)
            speaker.speak(text=f"I've launched {app_name} on your {nickname} {models.env.title}!")
        elif "what's" in phrase_lower or 'currently' in phrase_lower:
            speaker.speak(text=f'{shared.tv.current_app()} is running on your {nickname}.')
        elif 'change' in phrase_lower or 'source' in phrase_lower:
            cleaned = ' '.join([word for word in phrase.split() if word not in ('set', 'the', 'source', 'on', 'my',
                                                                                'of', 'to', 'tv')])
            source = util.get_closest_match(text=cleaned, match_list=shared.tv.get_sources())
            logger.info(f'{phrase} -> {source}')
            shared.tv.set_source(val=source)
            speaker.speak(text=f"I've changed the source to {source}.")
        else:
            speaker.speak(text="I didn't quite get that.")
            Thread(target=support.unrecognized_dumper, args=[{'TV': phrase}]).start()
    else:
        phrase = phrase.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to {phrase}, as the TV state is unknown!")
