import json
import subprocess
from socket import gethostname
from typing import Union
from urllib.error import HTTPError
from urllib.request import urlopen

from speedtest import ConfigRetrievalError, Speedtest

from executors.custom_logger import logger
from modules.audio.speaker import speak
from modules.utils import support


def vpn_checker() -> str:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    ip_address = support.vpn_checker()
    if ip_address.startswith('VPN'):
        speak(text="You have your VPN turned on. Details on your screen sir! Please note that none of the home "
                   "integrations will work with VPN enabled.")
    return ip_address


def internet_checker() -> Union[Speedtest, bool]:
    """Uses speed test api to check for internet connection.

    Returns:
        ``Speedtest`` or bool:
        - On success, returns Speedtest module.
        - On failure, returns boolean False.
    """
    try:
        return Speedtest()
    except ConfigRetrievalError:
        return False


def ip_info(phrase: str) -> None:
    """Gets IP address of the host machine.

    Args:
        phrase: Takes the spoken phrase an argument and tells the public IP if requested.
    """
    if 'public' in phrase.lower():
        if not internet_checker():
            speak(text="You are not connected to the internet sir!")
            return
        if ssid := get_ssid():
            ssid = f'for the connection {ssid} '
        else:
            ssid = ''
        output = None
        try:
            output = f"My public IP {ssid}is {json.load(urlopen('https://ipinfo.io/json')).get('ip')}"
        except HTTPError as error:
            logger.error(error)
        try:
            output = output or f"My public IP {ssid}is {json.loads(urlopen('http://ip.jsontest.com').read()).get('ip')}"
        except HTTPError as error:
            logger.error(error)
        if not output:
            output = 'I was unable to fetch the public IP sir!'
    else:
        ip_address = vpn_checker().split(':')[-1]
        output = f"My local IP address for {gethostname()} is {ip_address}"
    speak(text=output)


def get_ssid() -> str:
    """Gets SSID of the network connected.

    Returns:
        str:
        Wi-Fi or Ethernet SSID.
    """
    process = subprocess.Popen(
        ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
        stdout=subprocess.PIPE)
    out, err = process.communicate()
    if error := process.returncode:
        logger.error(f"Failed to fetch SSID with exit code: {error}\n{err}")
    # noinspection PyTypeChecker
    return dict(map(str.strip, info.split(': ')) for info in out.decode('utf-8').splitlines()[:-1] if
                len(info.split()) == 2).get('SSID')
