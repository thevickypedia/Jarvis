import json
import socket
import subprocess
import urllib.error
import urllib.request
from multiprocessing import Process
from typing import Dict, Union

import psutil
from speedtest import ConfigRetrievalError, Speedtest

from jarvis.executors import location
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util


def ip_address() -> Union[str, None]:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        socket_.connect(("8.8.8.8", 80))
    except OSError as error:
        logger.error(error)
        return
    ip_address_ = socket_.getsockname()[0]
    socket_.close()
    return ip_address_


def vpn_checker() -> Union[bool, str]:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        bool or str:
        Returns a ``False`` flag if VPN is detected, else the IP address.
    """
    if not (ip_address_ := ip_address()):
        speaker.speak(text=f"I was unable to connect to the internet {models.env.title}! Please check your connection.")
        return False
    if ip_address_.startswith("192") or ip_address_.startswith("127"):
        return ip_address_
    else:
        if info := public_ip_info():
            speaker.speak(text=f"You have your VPN turned on {models.env.title}! A connection has been detected to "
                               f"{info.get('ip')} at {info.get('city')} {info.get('region')}, "
                               f"maintained by {info.get('org')}. Please note that none of the home integrations will "
                               "work with VPN enabled.")
        else:
            speaker.speak(text=f"I was unable to connect to the internet {models.env.title}! "
                               "Please check your connection.")
        return False


def public_ip_info() -> Dict[str, str]:
    """Get public IP information.

    Returns:
        dict:
        Public IP information.
    """
    try:
        return json.load(urllib.request.urlopen(url='https://ipinfo.io/json'))
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        logger.error(error)
    try:
        return json.loads(urllib.request.urlopen(url='http://ip.jsontest.com').read())
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        logger.error(error)


def ip_info(phrase: str) -> None:
    """Gets IP address of the host machine.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "public" in phrase.lower():
        if not ip_address():
            speaker.speak(text=f"You are not connected to the internet {models.env.title}!")
            return
        if ssid := get_connection_info():
            ssid = f"for the connection {ssid} "
        else:
            ssid = ""
        if public_ip := public_ip_info():
            output = f"My public IP {ssid}is {public_ip.get('ip')}"
        else:
            output = f"I was unable to fetch the public IP {models.env.title}!"
    else:
        output = f"My local IP address for {socket.gethostname().split('.')[0]} is {ip_address()}"
    speaker.speak(text=output)


def get_connection_info(target: str = "SSID") -> Union[str, None]:
    """Gets information about the network connected.

    Returns:
        str:
        Wi-Fi or Ethernet SSID or Name.
    """
    try:
        if models.settings.os == models.supported_platforms.macOS:
            process = subprocess.Popen(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                stdout=subprocess.PIPE
            )
        elif models.settings.os == models.supported_platforms.windows:
            process = subprocess.check_output("netsh wlan show interfaces", shell=True)
        else:
            process = subprocess.check_output("nmcli -t -f name connection show --active | head -n 1", shell=True)
    except (subprocess.CalledProcessError, subprocess.CalledProcessError, FileNotFoundError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            result = error.output.decode(encoding='UTF-8').strip()
            logger.error("[%d]: %s", error.returncode, result)
        else:
            logger.error(error)
        return
    if models.settings.os == models.supported_platforms.macOS:
        out, err = process.communicate()
        if error := process.returncode:
            logger.error("Failed to fetch %s with exit code [%s]: %s", target, error, err)
            return
        # noinspection PyTypeChecker
        return dict(map(str.strip, info.split(": ")) for info in out.decode("utf-8").splitlines()[:-1] if
                    len(info.split()) == 2).get(target)
    elif models.settings.os == models.supported_platforms.windows:
        if result := [i.decode().strip() for i in process.splitlines() if
                      i.decode().strip().startswith(target)]:
            return result[0].split(':')[-1].strip()
        else:
            logger.error("Failed to fetch %s", target)
    else:
        if process:
            return process.decode(encoding='UTF-8').strip()


def speed_test() -> None:
    """Initiates speed test and says the ping rate, download and upload speed.

    References:
        Number of threads per core: https://psutil.readthedocs.io/en/latest/#psutil.cpu_count
    """
    try:
        st = Speedtest()
    except ConfigRetrievalError as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to connect to the speed test server.")
        return
    client_location = location.get_location_from_coordinates(coordinates=st.lat_lon)
    city = client_location.get("city") or client_location.get("residential") or \
        client_location.get("hamlet") or client_location.get("county")
    state = client_location.get("state")
    isp = st.results.client.get("isp").replace(",", "").replace(".", "")
    threads_per_core = int(psutil.cpu_count() / psutil.cpu_count(logical=False))
    upload_process = Process(target=st.upload, kwargs={"threads": threads_per_core})
    download_process = Process(target=st.download, kwargs={"threads": threads_per_core})
    upload_process.start()
    download_process.start()
    if not shared.called_by_offline:
        speaker.speak(text=f"Starting speed test {models.env.title}! I.S.P: {isp}. Location: {city} {state}", run=True)
    upload_process.join()
    download_process.join()
    ping = round(st.results.ping)
    download = support.size_converter(byte_size=st.results.download)
    upload = support.size_converter(byte_size=st.results.upload)
    util.write_screen(text=f"Ping: {ping}m/s\tDownload: {download}\tUpload: {upload}")
    speaker.speak(text=f"Ping rate: {ping} milli seconds. "
                       f"Download speed: {download} per second. "
                       f"Upload speed: {upload} per second.")
