import ipaddress
import json
import re
import socket
import subprocess
import time
import urllib.error
import urllib.request
from multiprocessing import Process
from typing import Dict

import psutil
import requests
from pydantic import HttpUrl
from speedtest import ConfigRetrievalError, Speedtest

from jarvis.executors import files, location
from jarvis.modules.audio import speaker
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.utils import shared, support


def ip_address() -> str | None:
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


def vpn_checker() -> bool | str:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        bool or str:
        Returns a ``False`` flag if VPN is detected, else the IP address.
    """
    if not (ip_address_ := ip_address()):
        speaker.speak(
            text=f"I was unable to connect to the internet {models.env.title}! Please check your connection."
        )
        return False
    if ip_address_.startswith("192") or ip_address_.startswith("127"):
        return ip_address_
    else:
        if info := public_ip_info():
            speaker.speak(
                text=f"You have your VPN turned on {models.env.title}! A connection has been detected to "
                f"{info.get('ip')} at {info.get('city')} {info.get('region')}, "
                f"maintained by {info.get('org')}. Please note that none of the home integrations will "
                "work with VPN enabled."
            )
        else:
            speaker.speak(
                text=f"I was unable to connect to the internet {models.env.title}! "
                "Please check your connection."
            )
        return False


def check_ip_version(ip_addr: str) -> bool:
    """Check if IP address is a valid IPv5 notation.

    Args:
        ip_addr: IP address as string.

    Returns:
        bool:
        Returns a boolean flag to indicate validity.
    """
    try:
        ip_obj = ipaddress.ip_address(ip_addr)
        if ip_obj.version == 4:
            return True
    except ValueError:
        logger.error("Invalid IP address: %s", ip_addr)
    return False


def get_public_ip() -> str | None:
    """Retrieves public IP address from various sources.

    Returns:
        str:
        Retrieved public IP address.
    """
    opt1 = lambda fa: fa.text.strip()  # noqa: E731
    opt2 = lambda fa: fa.json()["origin"].strip()  # noqa: E731
    mapping = {
        "https://checkip.amazonaws.com/": opt1,
        "https://api.ipify.org/": opt1,
        "https://ipinfo.io/ip/": opt1,
        "https://v4.ident.me/": opt1,
        "https://httpbin.org/ip": opt2,
        "https://myip.dnsomatic.com/": opt1,
    }
    # noinspection LongLine
    ip_regex = re.compile(
        r"""^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"""  # noqa: E501
    )
    for url, func in mapping.items():
        try:
            with requests.get(url) as response:
                ip_addr = ip_regex.findall(func(response))[0]
                if check_ip_version(ip_addr):
                    return ip_addr
        except (requests.RequestException, re.error, IndexError):
            continue


def get_and_store_ip_data(url: str, ip_addr: str) -> Dict[str, str]:
    """Retrieve IP information and store it in YAML mapping.

    Args:
        url: URL to request IP data from.
        ip_addr: IP address retrieved.

    Returns:
        Dict[str, str]:
        Public IP information.
    """
    try:
        ip_data = json.load(urllib.request.urlopen(url, timeout=3))
        # Ensure 'ip' key is always present
        ip_data["ip"] = ip_addr
        files.put_ip_info(ip_data)
        return ip_data
    except Exception as error:
        logger.error(error)


def public_ip_info() -> Dict[str, str]:
    """Get public IP information.

    Returns:
        Dict[str, str]:
        Public IP information.
    """
    if ip_data := files.get_ip_info():
        current_ts = int(time.time())
        timestamp = ip_data.get("timestamp", current_ts)
        if current_ts - timestamp < 86_400:
            return ip_data
    ip_addr = get_public_ip()
    return (
        get_and_store_ip_data("https://ipinfo.io/json", ip_addr)
        or get_and_store_ip_data(f"http://ip-api.com/json/{ip_addr}", ip_addr)
        or get_and_store_ip_data(f"https://ipinfo.io/{ip_addr}/json", ip_addr)
    )


def ip_info(phrase: str) -> None:
    """Gets IP address of the host machine.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "public" in phrase.lower():
        if not ip_address():
            speaker.speak(
                text=f"You are not connected to the internet {models.env.title}!"
            )
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


def get_connection_info(target: str = "SSID") -> str | None:
    """Gets information about the network connected.

    Returns:
        str:
        Wi-Fi or Ethernet SSID or Name.
    """
    try:
        if models.settings.os == enums.SupportedPlatforms.macOS:
            process = subprocess.Popen(
                [
                    "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                    "-I",
                ],
                stdout=subprocess.PIPE,
            )
        elif models.settings.os == enums.SupportedPlatforms.windows:
            process = subprocess.check_output("netsh wlan show interfaces", shell=True)
        else:
            process = subprocess.check_output(
                "nmcli -t -f name connection show --active | head -n 1", shell=True
            )
    except (
        subprocess.CalledProcessError,
        subprocess.SubprocessError,
        FileNotFoundError,
    ) as error:
        if isinstance(error, subprocess.CalledProcessError):
            result = error.output.decode(encoding="UTF-8").strip()
            logger.error("[%d]: %s", error.returncode, result)
        else:
            logger.error(error)
        return
    if models.settings.os == enums.SupportedPlatforms.macOS:
        out, err = process.communicate()
        if error := process.returncode:
            logger.error(
                "Failed to fetch %s with exit code [%s]: %s", target, error, err
            )
            return
        # noinspection PyTypeChecker
        return dict(
            map(str.strip, info.split(": "))
            for info in out.decode("utf-8").splitlines()[:-1]
            if len(info.split()) == 2
        ).get(target)
    elif models.settings.os == enums.SupportedPlatforms.windows:
        if result := [
            i.decode().strip()
            for i in process.splitlines()
            if i.decode().strip().startswith(target)
        ]:
            return result[0].split(":")[-1].strip()
        else:
            logger.error("Failed to fetch %s", target)
    else:
        if process:
            return process.decode(encoding="UTF-8").strip()


def speed_test(*args) -> None:
    """Initiates speed test and says the ping rate, download and upload speed.

    References:
        Number of threads per core: https://psutil.readthedocs.io/en/latest/#psutil.cpu_count
    """
    try:
        st = Speedtest()
    except ConfigRetrievalError as error:
        logger.error(error)
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to connect to the speed test server."
        )
        return
    client_location = location.get_location_from_coordinates(coordinates=st.lat_lon)
    city = (
        client_location.get("city")
        or client_location.get("residential")
        or client_location.get("hamlet")
        or client_location.get("county")
    )
    state = client_location.get("state")
    isp = st.results.client.get("isp").replace(",", "").replace(".", "")
    threads_per_core = int(psutil.cpu_count() / psutil.cpu_count(logical=False))
    upload_process = Process(target=st.upload, kwargs={"threads": threads_per_core})
    download_process = Process(target=st.download, kwargs={"threads": threads_per_core})
    upload_process.start()
    download_process.start()
    if not shared.called_by_offline:
        speaker.speak(
            text=f"Starting speed test {models.env.title}! I.S.P: {isp}. Location: {city} {state}",
            run=True,
        )
    upload_process.join()
    download_process.join()
    ping = round(st.results.ping)
    download = support.size_converter(byte_size=st.results.download)
    upload = support.size_converter(byte_size=st.results.upload)
    support.write_screen(
        text=f"Ping: {ping}m/s\tDownload: {download}\tUpload: {upload}"
    )
    speaker.speak(
        text=f"Ping rate: {ping} milli seconds. "
        f"Download speed: {download} per second. "
        f"Upload speed: {upload} per second."
    )


def get_tunnel(log: bool = True) -> HttpUrl:
    """Checks for any active public URL tunneled using Ngrok.

    Returns:
        HttpUrl:
        Ngrok public URL.
    """
    try:
        response = requests.get(url="http://localhost:4040/api/tunnels")
        if response.ok:
            tunnels = response.json().get("tunnels", [])
            protocols = list(filter(None, [tunnel.get("proto") for tunnel in tunnels]))
            for tunnel in tunnels:
                if "https" in protocols and tunnel.get("proto") != "https":
                    continue
                if hosted := tunnel.get("config", {}).get("addr"):
                    if int(hosted.split(":")[-1]) == models.env.offline_port:
                        return tunnel.get("public_url")
    except (*EgressErrors, requests.JSONDecodeError) as error:
        logger.error(error) if log else None
