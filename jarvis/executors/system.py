import os
import platform
import re
import shutil
import subprocess
from datetime import datetime
from typing import Dict, NoReturn

import packaging.version
import psutil

from jarvis.executors import controls, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.temperature import temperature
from jarvis.modules.utils import shared, support, util


def system_info() -> NoReturn:
    """Tells the system configuration."""
    disk_usage = shutil.disk_usage("/")
    total = support.size_converter(byte_size=disk_usage.total)
    used = support.size_converter(byte_size=disk_usage.used)
    free = support.size_converter(byte_size=disk_usage.free)
    ram = support.size_converter(byte_size=models.settings.ram).replace('.0', '')
    ram_used = support.size_converter(byte_size=psutil.virtual_memory().percent).replace(' B', ' %')
    system = None
    if models.settings.os == models.supported_platforms.linux:
        mapping = get_distributor_info_linux()
        if mapping.get('distributor_id') and mapping.get('release'):
            system = f"{mapping['distributor_id']} {mapping['release']}"
    if not system:
        if not shared.hosted_device.get('os_version'):
            logger.warning("hosted_device information was not loaded during startup. Reloading now.")
            shared.hosted_device = hosted_device_info()
        system = f"{shared.hosted_device.get('os_name', models.settings.os)} " \
                 f"{shared.hosted_device.get('os_version', '')}"
    speaker.speak(text=f"You're running {system}, with {models.settings.physical_cores} "
                       f"physical cores and {models.settings.logical_cores} logical cores. Your physical drive "
                       f"capacity is {total}. You have used up {used} of space. Your free space is {free}. Your "
                       f"RAM capacity is {ram}. You are currently utilizing {ram_used} of your memory.")


def system_vitals() -> None:
    """Reads system vitals.

    See Also:
        - Jarvis will suggest a reboot if the system uptime is more than 2 days.
        - If confirmed, invokes `restart <https://thevickypedia.github.io/Jarvis/#jarvis.restart>`__ function.
    """
    output = ""
    if models.settings.os == models.supported_platforms.macOS:
        if not models.env.root_password:
            speaker.speak(text=f"You haven't provided a root password for me to read system vitals {models.env.title}! "
                               "Add the root password as an environment variable for me to read.")
            return

        logger.info('Fetching system vitals')
        cpu_temp, gpu_temp, fan_speed, output = None, None, None, ""

        # Tested on 10.13, 10.14, 11.6 and 12.3 versions
        if not shared.hosted_device.get('os_version'):
            logger.warning("hosted_device information was not loaded during startup. Reloading now.")
            shared.hosted_device = hosted_device_info()
        if packaging.version.parse(shared.hosted_device.get('os_version')) > packaging.version.parse('10.14'):
            critical_info = [each.strip() for each in (os.popen(
                f'echo {models.env.root_password} | sudo -S powermetrics --samplers smc -i1 -n1'
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
                f'echo {models.env.root_password} | sudo -S spindump 1 1 -file /tmp/spindump.txt > /dev/null 2>&1;grep '
                f'"Fan speed" /tmp/spindump.txt;sudo rm /tmp/spindump.txt', shell=True
            ).decode('utf-8')

        if cpu_temp:
            cpu = f'Your current average CPU temperature is ' \
                  f'{util.format_nos(input_=temperature.c2f(arg=util.extract_nos(input_=cpu_temp)))}' \
                  f'\N{DEGREE SIGN}F. '
            output += cpu
            speaker.speak(text=cpu)
        if gpu_temp:
            gpu = f'GPU temperature is {util.format_nos(temperature.c2f(util.extract_nos(gpu_temp)))}' \
                  f'\N{DEGREE SIGN}F. '
            output += gpu
            speaker.speak(text=gpu)
        if fan_speed:
            fan = f'Current fan speed is {util.format_nos(util.extract_nos(fan_speed))} RPM. '
            output += fan
            speaker.speak(text=fan)

    restart_time = datetime.fromtimestamp(psutil.boot_time())
    second = (datetime.now() - restart_time).total_seconds()
    restart_time = datetime.strftime(restart_time, "%A, %B %d, at %I:%M %p")
    restart_duration = support.time_converter(second=second)
    output += f'Restarted on: {restart_time} - {restart_duration} ago from now.'
    if shared.called_by_offline:
        speaker.speak(text=output)
        return
    util.write_screen(text=output)
    speaker.speak(text=f"Your {shared.hosted_device.get('device')} was last booted on {restart_time}. "
                       f"Current boot time is: {restart_duration}.")
    if second >= 259_200:  # 3 days
        if boot_extreme := re.search('(.*) days', restart_duration):
            warn = int(boot_extreme.group().replace(' days', '').strip())
            speaker.speak(text=f"{models.env.title}! your {shared.hosted_device.get('device')} has been running for "
                               f"more than {warn} days. You must consider a reboot for better performance. Would you "
                               f"like me to restart it for you {models.env.title}?",
                          run=True)
            response = listener.listen()
            if word_match.word_match(phrase=response.lower(), match_list=keywords.keywords.ok):
                logger.info("JARVIS::Restarting %s", shared.hosted_device.get('device'))
                controls.restart(ask=False)


def get_distributor_info_linux() -> Dict[str, str]:
    """Returns distributor information (i.e., Ubuntu) for Linux based systems.

    Returns:
        dict:
        A dictionary of key-value pairs with distributor id, name and version.
    """
    try:
        result = subprocess.check_output('lsb_release -a', shell=True, stderr=subprocess.DEVNULL)
        return {i.split(':')[0].strip().lower().replace(' ', '_'): i.split(':')[1].strip()
                for i in result.decode(encoding="UTF-8").splitlines() if ':' in i}
    except (subprocess.SubprocessError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            result = error.output.decode(encoding='UTF-8').strip()
            logger.error("[%d]: %s", error.returncode, result)
        else:
            logger.error(error)
        return {}


def hosted_device_info() -> Dict[str, str]:
    """Gets basic information of the hosted device.

    Returns:
        dict:
        A dictionary of key-value pairs with device type, operating system, os version.
    """
    if models.settings.os == models.supported_platforms.macOS:
        system_kernel = subprocess.check_output("sysctl hw.model", shell=True).decode('utf-8').splitlines()
        device = util.extract_str(system_kernel[0].split(':')[1])
    elif models.settings.os == models.supported_platforms.windows:
        device = subprocess.getoutput("WMIC CSPRODUCT GET VENDOR").replace('Vendor', '').strip()
    else:
        device = subprocess.check_output("cat /sys/devices/virtual/dmi/id/product_name",
                                         shell=True).decode('utf-8').strip()
    platform_info = platform.platform(terse=True).split('-')
    return {'device': device, 'os_name': platform_info[0], 'os_version': platform_info[1]}
