import random
import time
from threading import Thread

from jarvis.modules.audio import speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.exceptions import TVError
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.tv import lg, roku
from jarvis.modules.utils import shared, support, util


def tv_controller(phrase: str, tv_ip: str, identifier: str, nickname: str, client_key: str = None) -> None:
    """Controller for Roku or LG tv actions.

    Args:
        phrase: Takes the phrase spoken as an argument.
        tv_ip: IP address of the television.
        identifier: String to control roku or LG WebOS.
        nickname: Name as in the source yaml file.
        client_key: Client key to connect to the LG WebOS tv.
    """
    phrase_lower = phrase.replace('TV', '').lower()

    if not shared.tv[nickname]:
        try:
            if identifier == 'LG':
                shared.tv[nickname] = lg.LGWebOS(ip_address=tv_ip, client_key=client_key)
            elif identifier == 'ROKU':
                shared.tv[nickname] = roku.RokuECP(ip_address=tv_ip)
                if not shared.tv[nickname].current_app():
                    for _ in range(3):  # REDUNDANT-Roku: Launch home thrice to ensure device wakes up from sleep
                        shared.tv[nickname].startup()
        except TVError as error:
            logger.error("Failed to connect to the TV. %s", error)
            speaker.speak(text=f"I was unable to connect to the {nickname} {models.env.title}! "
                               f"It appears to be a connection issue. You might want to try again later.")
            return
        else:
            if 'turn on' in phrase_lower or 'connect' in phrase_lower:
                speaker.speak(text=f"TV features have been integrated {models.env.title}!")
                return

    if shared.tv[nickname]:
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speaker.speak(text=f'Your {nickname} is already powered on {models.env.title}!')
        elif 'shutdown' in phrase_lower or 'shut down' in phrase_lower or 'turn off' in phrase_lower:
            Thread(target=shared.tv[nickname].shutdown).start()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}! Turning your {nickname} off.')
            shared.tv.pop(nickname)
        elif 'increase' in phrase_lower:
            shared.tv[nickname].increase_volume()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'decrease' in phrase_lower or 'reduce' in phrase_lower:
            shared.tv[nickname].decrease_volume()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'mute' in phrase_lower:
            shared.tv[nickname].mute()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'stop' in phrase_lower and 'content' in phrase_lower:
            shared.tv[nickname].stop()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'stop' in phrase_lower or 'pause' in phrase_lower:
            shared.tv[nickname].pause()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'resume' in phrase_lower or 'play' in phrase_lower:
            shared.tv[nickname].play()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'rewind' in phrase_lower:
            shared.tv[nickname].rewind()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'forward' in phrase_lower:
            shared.tv[nickname].forward()
            speaker.speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'set' in phrase_lower and 'volume' in phrase_lower:
            vol = util.extract_nos(input_=phrase_lower, method=int)
            if vol is None:
                speaker.speak(text=f"Requested volume doesn't match the right format {models.env.title}!")
            else:
                shared.tv[nickname].set_volume(target=vol)
                speaker.speak(text=f"I've set the volume to {vol}% {models.env.title}.")
        elif 'volume' in phrase_lower:
            speaker.speak(text=f"The current volume on your {nickname} is, {shared.tv[nickname].get_volume()}%")
        elif 'app' in phrase_lower or 'application' in phrase_lower:
            util.write_screen(text=list(shared.tv[nickname].get_apps()))
            speaker.speak(text=f'App list on your screen {models.env.title}!', run=True)
            time.sleep(5)
        elif 'open' in phrase_lower or 'launch' in phrase_lower:
            cleaned = ' '.join([w for w in phrase.split() if w not in ['launch', 'open', 'tv', 'on', 'my', 'the']])
            app_name = util.get_closest_match(text=cleaned, match_list=list(shared.tv[nickname].get_apps()))
            logger.info("%s -> %s", phrase, app_name)
            shared.tv[nickname].launch_app(app_name=app_name)
            speaker.speak(text=f"I've launched {app_name} on your {nickname} {models.env.title}!")
        elif "what's" in phrase_lower or 'currently' in phrase_lower:
            speaker.speak(text=f'{shared.tv[nickname].current_app()} is running on your {nickname}.')
        elif 'change' in phrase_lower or 'source' in phrase_lower:
            cleaned = ' '.join([word for word in phrase.split() if word not in ('set', 'the', 'source', 'on', 'my',
                                                                                'of', 'to', 'tv')])
            source = util.get_closest_match(text=cleaned, match_list=list(shared.tv[nickname].get_sources()))
            logger.info("%s -> %s", phrase, source)
            shared.tv[nickname].set_source(val=source)
            speaker.speak(text=f"I've changed the source to {source}.")
        else:
            speaker.speak(text="I didn't quite get that.")
            Thread(target=support.unrecognized_dumper, args=[{'TV': phrase}]).start()
    else:
        phrase = phrase.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to {phrase}, as the TV state is unknown!")
