import json
import subprocess
import sys
from socket import AF_INET, SOCK_DGRAM, gethostname, socket
from threading import Thread
from typing import Union
from urllib.error import HTTPError
from urllib.request import urlopen

import psutil
from speedtest import ConfigRetrievalError, Speedtest

from executors.custom_logger import logger
from executors.location import geo_locator
from modules.audio import speaker
from modules.utils import support


def ip_address() -> str:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    socket_ = socket(AF_INET, SOCK_DGRAM)
    socket_.connect(("8.8.8.8", 80))
    ip_addr = socket_.getsockname()[0]
    socket_.close()
    return ip_addr


def vpn_checker() -> str:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    ip_addr = ip_address()
    if not (ip_addr.startswith('192') | ip_addr.startswith('127')):
        ip_addr = 'VPN:' + ip_addr
        info = json.load(urlopen('https://ipinfo.io/json'))
        sys.stdout.write(f"\rVPN connection is detected to {info.get('ip')} at {info.get('city')}, "
                         f"{info.get('region')} maintained by {info.get('org')}")

    if ip_addr.startswith('VPN'):
        speaker.speak(text="You have your VPN turned on. Details on your screen sir! Please note that none of the home "
                           "integrations will work with VPN enabled.")
    return ip_addr


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
            speaker.speak(text="You are not connected to the internet sir!")
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
        ip_addr = ip_address().split(':')[-1]
        output = f"My local IP address for {gethostname()} is {ip_addr}"
    speaker.speak(text=output)


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


def speed_test() -> None:
    """Initiates speed test and says the ping rate, download and upload speed.

    References:
        Number of threads per core: https://psutil.readthedocs.io/en/latest/#psutil.cpu_count
    """
    if not (st := internet_checker()):
        speaker.speak(text="You're not connected to the internet sir!")
        return
    client_locator = geo_locator.reverse(st.lat_lon, language='en')
    client_location = client_locator.raw['address']
    city = client_location.get('city') or client_location.get('residential') or \
        client_location.get('hamlet') or client_location.get('county')
    state = client_location.get('state')
    isp = st.results.client.get('isp').replace(',', '').replace('.', '')
    threads_per_core = int(psutil.cpu_count() / psutil.cpu_count(logical=False))
    upload_thread = Thread(target=st.upload, kwargs={'threads': threads_per_core})
    download_thread = Thread(target=st.download, kwargs={'threads': threads_per_core})
    upload_thread.start()
    download_thread.start()
    speaker.speak(text=f"Starting speed test sir! I.S.P: {isp}. Location: {city} {state}", run=True)
    upload_thread.join()
    download_thread.join()
    ping = round(st.results.ping)
    download = support.size_converter(byte_size=st.results.download)
    upload = support.size_converter(byte_size=st.results.upload)
    sys.stdout.write(f'\rPing: {ping}m/s\tDownload: {download}\tUpload: {upload}')
    speaker.speak(text=f'Ping rate: {ping} milli seconds. '
                       f'Download speed: {download} per second. '
                       f'Upload speed: {upload} per second.')
