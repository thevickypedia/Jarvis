import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from multiprocessing import Process
from typing import Union

import psutil
from speedtest import ConfigRetrievalError, Speedtest

from executors.location import geo_locator
from executors.logger import logger
from modules.audio import speaker
from modules.models import models
from modules.utils import support

env = models.env


def ip_address() -> str:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_.connect(("8.8.8.8", 80))
    ip_address_ = socket_.getsockname()[0]
    socket_.close()
    return ip_address_


def vpn_checker() -> Union[bool, str]:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        bool or str:
        Returns a ``False`` flag if VPN is detected, else the IP address.
    """
    ip_address_ = ip_address()
    if ip_address_.startswith("192") or ip_address_.startswith("127"):
        return ip_address_
    else:
        info = json.load(urllib.request.urlopen(url="https://ipinfo.io/json"))
        speaker.speak(text=f"You have your VPN turned on {env.title}! A connection has been detected to "
                           f"{info.get('ip')} at {info.get('city')} {info.get('region')}, "
                           f"maintained by {info.get('org')}. Please note that none of the home integrations will "
                           "work with VPN enabled.")
        return False


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
    if "public" in phrase.lower():
        if not internet_checker():
            speaker.speak(text=f"You are not connected to the internet {env.title}!")
            return
        if ssid := get_ssid():
            ssid = f"for the connection {ssid} "
        else:
            ssid = ""
        output = None
        try:
            output = f"My public IP {ssid}is " \
                     f"{json.load(urllib.request.urlopen(url='https://ipinfo.io/json')).get('ip')}"
        except urllib.error.HTTPError as error:
            logger.error(error)
        try:
            output = output or f"My public IP {ssid}is " \
                               f"{json.loads(urllib.request.urlopen(url='http://ip.jsontest.com').read()).get('ip')}"
        except urllib.error.HTTPError as error:
            logger.error(error)
        if not output:
            output = f"I was unable to fetch the public IP {env.title}!"
    else:
        output = f"My local IP address for {socket.gethostname()} is {ip_address()}"
    speaker.speak(text=output)


def get_ssid() -> Union[str, None]:
    """Gets SSID of the network connected.

    Returns:
        str:
        Wi-Fi or Ethernet SSID.
    """
    if env.mac:
        process = subprocess.Popen(
            ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
            stdout=subprocess.PIPE
        )
        out, err = process.communicate()
        if error := process.returncode:
            logger.error(f"Failed to fetch SSID with exit code: {error}\n{err}")
            return
        # noinspection PyTypeChecker
        return dict(map(str.strip, info.split(": ")) for info in out.decode("utf-8").splitlines()[:-1] if
                    len(info.split()) == 2).get("SSID")
    else:
        if ssid := [i.decode().strip() for i in subprocess.check_output("netsh wlan show interfaces").splitlines() if
                    i.decode().strip().startswith('SSID')]:
            return ssid[0].split(':')[-1].strip()
        else:
            logger.error("Failed to fetch SSID")


def speed_test() -> None:
    """Initiates speed test and says the ping rate, download and upload speed.

    References:
        Number of threads per core: https://psutil.readthedocs.io/en/latest/#psutil.cpu_count
    """
    if not (st := internet_checker()):
        speaker.speak(text=f"You're not connected to the internet {env.title}!")
        return
    client_locator = geo_locator.reverse(st.lat_lon, language="en")
    client_location = client_locator.raw["address"]
    city = client_location.get("city") or client_location.get("residential") or \
        client_location.get("hamlet") or client_location.get("county")
    state = client_location.get("state")
    isp = st.results.client.get("isp").replace(",", "").replace(".", "")
    threads_per_core = int(psutil.cpu_count() / psutil.cpu_count(logical=False))
    upload_process = Process(target=st.upload, kwargs={"threads": threads_per_core})
    download_process = Process(target=st.download, kwargs={"threads": threads_per_core})
    upload_process.start()
    download_process.start()
    speaker.speak(text=f"Starting speed test {env.title}! I.S.P: {isp}. Location: {city} {state}", run=True)
    upload_process.join()
    download_process.join()
    ping = round(st.results.ping)
    download = support.size_converter(byte_size=st.results.download)
    upload = support.size_converter(byte_size=st.results.upload)
    sys.stdout.write(f"\rPing: {ping}m/s\tDownload: {download}\tUpload: {upload}")
    speaker.speak(text=f"Ping rate: {ping} milli seconds. "
                       f"Download speed: {download} per second. "
                       f"Upload speed: {upload} per second.")
