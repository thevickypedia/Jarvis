import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Dict, List, Tuple, Union

from jarvis.executors import files, internet, tv_controls, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support
from jarvis.modules.wakeonlan import wakeonlan


def get_tv(data: dict) -> Tuple[Dict[str, Dict[str, Union[str, List[str]]]], str]:
    """Extract TV mapping from the data in smart devices.

    Args:
        data: Raw data from smart devices.

    Returns:
        Tuple[Dict[str, Dict[str, Union[str, List[str]]]], str]:
        Return TV information and the key name under which it was stored. The key will be used to update the file.
    """
    for key, value in data.items():
        if key.lower() in ("tv", "tvs", "television", "televisions"):
            return data[key], key


def tv_status(tv_ip_list: list, attempt: int = 0) -> str:
    """Pings the tv and returns the status. 0 if able to ping, 256 if unable to ping.

    Args:
        tv_ip_list: List of possible IP addresses for the Television.
        attempt: Takes iteration count as an argument.

    Returns:
        int:
        Returns the reachable IP address from the list.
    """
    for ip in tv_ip_list:
        if models.settings.os == models.supported_platforms.windows:
            if tv_stat := os.system(f"ping -c 1 -t 2 {ip} > NUL"):
                logger.error("Connection timed out on %s. Ping result: %s", ip, tv_stat) if not attempt else None
            else:
                return ip
        else:
            if tv_stat := os.system(f"ping -c 1 -t 2 {ip} >/dev/null 2>&1"):
                logger.error("Connection timed out on %s. Ping result: %s", ip, tv_stat) if not attempt else None
            else:
                return ip


def television(phrase: str) -> None:
    """Controls all actions on a TV (LG Web OS or Roku).

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    match_words = ['turn on', 'connect', 'shutdown', 'shut down', 'turn off', 'increase',
                   'decrease', 'reduce', 'mute', 'stop', 'content', 'stop', 'pause', 'resume', 'play',
                   'rewind', 'forward', 'set', 'volume', 'volume', 'app', 'application', 'open',
                   'launch', "what's", 'currently', 'change', 'source']
    if not word_match.word_match(phrase=phrase, match_list=match_words):
        speaker.speak(text=f"I didn't quite get that {models.env.title}! What do you want me to do to your tv?")
        Thread(target=support.unrecognized_dumper, args=[{'TV': phrase}]).start()
        return

    if not internet.vpn_checker():
        return

    smart_devices = files.get_smart_devices()
    if smart_devices is False:
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to read the source information.")
        return
    if smart_devices and (tv_mapping := get_tv(data=smart_devices)):
        tv_map, key = tv_mapping
        logger.debug("%s stored with key: '%s'", tv_map, key)
    else:
        logger.warning("%s is empty for tv.", models.fileio.smart_devices)
        support.no_env_vars()
        return

    tvs = list(tv_map.keys())
    if "all" in phrase:
        tv_iterate = tvs
    elif selected := word_match.word_match(phrase=phrase, match_list=tvs):
        tv_iterate = [selected]
    else:
        speaker.speak(text=f"You have {len(tvs)} TVs added {models.env.title}! "
                           "Please specify which TV I should access.")
        return

    logger.info("Chosen TVs: %s", tv_iterate)
    for target_tv in tv_iterate:
        logger.info("Iterating over: %s", target_tv)
        tv_name = tv_map[target_tv].get('hostname')
        tv_mac = tv_map[target_tv].get('mac_address')
        tv_client_key = tv_map[target_tv].get('client_key')

        if not all((tv_name, tv_mac)):
            speaker.speak(text=f"I'm sorry {models.env.title}! "
                               f"I was unable to find the {target_tv}'s name or MAC address.")
            continue

        if 'lg' in tv_name.lower() or 'roku' in tv_name.lower():
            logger.debug("'%s' is supported.", tv_name)
        else:
            logger.error("tv's name [%s] is not supported.", tv_name)
            speaker.speak(text=f"I'm sorry {models.env.title}! Your {target_tv}'s name is neither LG or Roku."
                               "So, I will not be able to control the television.")
            continue

        if 'lg' in tv_name.lower() and not tv_client_key:
            speaker.speak(text="LG televisions require a client key, but that seems to be missing. "
                               "Proceeding without it. User confirmation on TV screen may be required.")

        tv_ip_list = support.hostname_to_ip(hostname=tv_name)
        tv_ip_list = list(filter(None, tv_ip_list))
        if not tv_ip_list:
            speaker.speak(
                text=f"I'm sorry {models.env.title}! I wasn't able to get the IP address of your {target_tv}."
            )
            continue

        if isinstance(tv_mac, str):
            tv_mac = [tv_mac]

        if 'turn off' in phrase.lower() or 'shutdown' in phrase.lower() or 'shut down' in phrase.lower():
            if not (tv_ip := tv_status(tv_ip_list=tv_ip_list)):
                # WARNING: TV that was turned off recently might still respond to ping
                speaker.speak(text=f"I wasn't able to connect to your {target_tv} {models.env.title}! "
                                   "I guess your TV is powered off already.")
                continue
        elif not (tv_ip := tv_status(tv_ip_list=tv_ip_list)):
            logger.info("Trying to power on the device using the mac addresses: %s", tv_mac)
            power_controller = wakeonlan.WakeOnLan()
            for _ in range(3):  # REDUNDANT-Roku: Send magic packets thrice to ensure device wakes up from sleep
                with ThreadPoolExecutor(max_workers=len(tv_mac)) as executor:
                    executor.map(power_controller.send_packet, tv_mac)
            if not shared.called_by_offline:
                speaker.speak(text=f"Looks like your {target_tv} is powered off {models.env.title}! "
                                   "Let me try to turn it back on!", run=True)

        if not tv_ip:
            for i in range(5):
                if tv_ip := tv_status(tv_ip_list=tv_ip_list, attempt=i):
                    break
                time.sleep(0.5)
            else:
                speaker.speak(text=f"I wasn't able to connect to your {target_tv} {models.env.title}! "
                                   "Please make sure you are on the same network as your TV, and "
                                   "your TV is connected to a power source.")
                continue

        # Instantiate dictionary if not present
        if not shared.tv.get(target_tv):
            shared.tv[target_tv] = None
        logger.debug("TV database: %s", shared.tv)
        if 'lg' in tv_name.lower():
            tv_controls.tv_controller(phrase=phrase, tv_ip=tv_ip, identifier='LG',
                                      client_key=tv_client_key, nickname=target_tv, key=key)
        else:
            tv_controls.tv_controller(phrase=phrase, tv_ip=tv_ip, identifier='ROKU', nickname=target_tv)
