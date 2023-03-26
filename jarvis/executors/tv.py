import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

import yaml

from jarvis.executors import internet, tv_controls, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support
from jarvis.modules.wakeonlan import wakeonlan


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

    if not os.path.isfile(models.fileio.smart_devices):
        logger.warning("%s not found.", models.fileio.smart_devices)
        support.no_env_vars()
        return

    try:
        with open(models.fileio.smart_devices) as file:
            smart_devices = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
            if smart_devices:
                smart_devices = {key: value for key, value in smart_devices.items() if 'tv' in key.lower()}
    except yaml.YAMLError as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I was unable to read your TV's source information.")
        return

    if not any(smart_devices):
        logger.warning("%s is empty for TV.", models.fileio.smart_devices)
        support.no_env_vars()
        return

    tvs = list(smart_devices.keys())
    if len(tvs) == 1:
        target_tv = tvs[0]
    elif not (target_tv := word_match.word_match(phrase=phrase, match_list=tvs)):
        speaker.speak(text=f"You have {len(tvs)} TVs added {models.env.title}! "
                           "Please specify which TV I should access.")
        return

    tv_name = smart_devices[target_tv].get('hostname')
    tv_mac = smart_devices[target_tv].get('mac_address')
    tv_client_key = smart_devices[target_tv].get('client_key')

    if not all((tv_name, tv_mac)):
        speaker.speak(text=f"I'm sorry {models.env.title}! I was unable to find the {target_tv}'s name or MAC address.")
        return

    if 'lg' in tv_name.lower() or 'roku' in tv_name.lower():
        logger.debug("'%s' is supported.", tv_name)
    else:
        logger.error("tv's name [%s] is not supported.", tv_name)
        speaker.speak(text=f"I'm sorry {models.env.title}! Your {target_tv}'s name is neither LG or Roku."
                           "So, I will not be able to control the television.")
        return

    if 'lg' in tv_name.lower() and not tv_client_key:
        speaker.speak(text="LG televisions require a client key, but that seems to be missing. "
                           "Proceeding without it, user confirmation on TV screen may be required, for the first time.")

    tv_ip_list = support.hostname_to_ip(hostname=tv_name)
    tv_ip_list = list(filter(None, tv_ip_list))
    if not tv_ip_list:
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to get the IP address of your {target_tv}.")
        return

    if isinstance(tv_mac, str):
        tv_mac = [tv_mac]

    if 'turn off' in phrase.lower() or 'shutdown' in phrase.lower() or 'shut down' in phrase.lower():
        if not (tv_ip := tv_status(tv_ip_list=tv_ip_list)):
            speaker.speak(text=f"I wasn't able to connect to your {target_tv} {models.env.title}! "
                               "I guess your TV is powered off already.")
            return
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
            return

    # Instantiate dictionary if not present
    if not shared.tv.get(target_tv):
        shared.tv[target_tv] = None
    logger.debug("TV database: %s", shared.tv)
    if 'lg' in tv_name.lower():
        tv_controls.tv_controller(phrase=phrase, tv_ip=tv_ip, identifier='LG',
                                  client_key=tv_client_key, nickname=target_tv)
    else:
        tv_controls.tv_controller(phrase=phrase, tv_ip=tv_ip, identifier='ROKU', nickname=target_tv)
