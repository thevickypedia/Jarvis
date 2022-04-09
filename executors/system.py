import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import NoReturn

import packaging.version
import psutil

from executors.controls import restart
from executors.logger import logger
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.models import models
from modules.temperature import temperature
from modules.utils import shared, support

env = models.env


def system_info() -> NoReturn:
    """Tells the system configuration."""
    total, used, free = shutil.disk_usage("/")
    total = support.size_converter(byte_size=total)
    used = support.size_converter(byte_size=used)
    free = support.size_converter(byte_size=free)
    ram = support.size_converter(byte_size=psutil.virtual_memory().total).replace('.0', '')
    ram_used = support.size_converter(byte_size=psutil.virtual_memory().percent).replace(' B', ' %')
    physical = psutil.cpu_count(logical=False)
    logical = psutil.cpu_count(logical=True)
    speaker.speak(text=f"You're running {platform.platform(terse=True)}, with {physical} physical cores and "
                       f"{logical} logical cores. Your physical drive capacity is {total}. You have used up {used} of "
                       f"space. Your free space is {free}. Your RAM capacity is {ram}. You are currently utilizing "
                       f"{ram_used} of your memory.")


def system_vitals() -> None:
    """Reads system vitals on macOS.

    See Also:
        - Jarvis will suggest a reboot if the system uptime is more than 2 days.
        - If confirmed, invokes `restart <https://thevickypedia.github.io/Jarvis/#jarvis.restart>`__ function.
    """
    output = ""
    if env.mac:
        if not env.root_password:
            speaker.speak(text=f"You haven't provided a root password for me to read system vitals {env.title}! "
                               "Add the root password as an environment variable for me to read.")
            return

        logger.info('Fetching system vitals')
        cpu_temp, gpu_temp, fan_speed, output = None, None, None, ""

        # Tested on 10.13, 10.14, 11.6 and 12.3 versions
        if packaging.version.parse(shared.hosted_device.get('os_version')) > packaging.version.parse('10.14'):
            critical_info = [each.strip() for each in (os.popen(
                f'echo {env.root_password} | sudo -S powermetrics --samplers smc -i1 -n1'
            )).read().split('\n') if each != '']
            support.flush_screen()

            for info in critical_info:
                if 'CPU die temperature' in info:
                    cpu_temp = info.strip('CPU die temperature: ').replace(' C', '').strip()
                if 'GPU die temperature' in info:
                    gpu_temp = info.strip('GPU die temperature: ').replace(' C', '').strip()
                if 'Fan' in info:
                    fan_speed = info.strip('Fan: ').replace(' rpm', '').strip()
        else:
            fan_speed = subprocess.check_output(
                f'echo {env.root_password} | sudo -S spindump 1 1 -file /tmp/spindump.txt > /dev/null 2>&1;grep '
                f'"Fan speed" /tmp/spindump.txt;sudo rm /tmp/spindump.txt', shell=True
            ).decode('utf-8')

        if cpu_temp:
            cpu = f'Your current average CPU temperature is ' \
                  f'{support.format_nos(input_=temperature.c2f(arg=support.extract_nos(input_=cpu_temp)))}°F. '
            output += cpu
            speaker.speak(text=cpu)
        if gpu_temp:
            gpu = f'GPU temperature is {support.format_nos(temperature.c2f(support.extract_nos(gpu_temp)))}°F. '
            output += gpu
            speaker.speak(text=gpu)
        if fan_speed:
            fan = f'Current fan speed is {support.format_nos(support.extract_nos(fan_speed))} RPM. '
            output += fan
            speaker.speak(text=fan)

    restart_time = datetime.fromtimestamp(psutil.boot_time())
    second = (datetime.now() - restart_time).total_seconds()
    restart_time = datetime.strftime(restart_time, "%A, %B %d, at %I:%M %p")
    restart_duration = support.time_converter(seconds=second)
    output += f'Restarted on: {restart_time} - {restart_duration} ago from now.'
    if shared.called_by_offline:
        speaker.speak(text=output)
        return
    sys.stdout.write(f'\r{output}')
    speaker.speak(text=f"Your {shared.hosted_device.get('device')} was last booted on {restart_time}. "
                       f"Current boot time is: {restart_duration}.")
    if second >= 259_200:  # 3 days
        if boot_extreme := re.search('(.*) days', restart_duration):
            warn = int(boot_extreme.group().replace(' days', '').strip())
            speaker.speak(text=f"{env.title}! your {shared.hosted_device.get('device')} has been running for more "
                               f"than {warn} days. You must consider a reboot for better performance. Would you like "
                               f"me to restart it for you {env.title}?",
                          run=True)
            response = listener.listen(timeout=3, phrase_limit=3)
            if any(word in response.lower() for word in keywords.ok):
                logger.info(f'JARVIS::Restarting {shared.hosted_device.get("device")}')
                restart(target='PC_Proceed')


def hosted_device_info() -> dict:
    """Gets basic information of the hosted device.

    Returns:
        dict:
        A dictionary of key-value pairs with device type, operating system, os version.
    """
    if env.mac:
        system_kernel = subprocess.check_output("sysctl hw.model", shell=True).decode('utf-8').splitlines()
        device = support.extract_str(system_kernel[0].split(':')[1])
    else:
        device = subprocess.getoutput("WMIC CSPRODUCT GET VENDOR").replace('Vendor', '').strip()
    platform_info = platform.platform(terse=True).split('-')
    return {'device': device, 'os_name': platform_info[0], 'os_version': platform_info[1]}
