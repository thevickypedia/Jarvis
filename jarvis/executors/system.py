from datetime import datetime
from multiprocessing.pool import ThreadPool

import psutil

from jarvis.executors import word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.models import models
from jarvis.modules.utils import support, util


def system_info(phrase: str) -> None:
    """Tells the system configuration and current statistics."""
    vitals = word_match.word_match(
        phrase=phrase, match_list=keywords.keywords["system_vitals"]
    )

    if vitals:
        cpu_percent = ThreadPool(processes=1).apply_async(
            psutil.cpu_percent, kwds={"interval": 3}
        )

    if models.settings.distro.get("distributor_id") and models.settings.distro.get(
        "release"
    ):
        system = f"{models.settings.distro['distributor_id']} {models.settings.distro['release']}"
    else:
        system = f"{models.settings.os_name} {models.settings.os_version}"

    restart_time = datetime.fromtimestamp(psutil.boot_time())
    second = (datetime.now() - restart_time).total_seconds()
    restart_time = datetime.strftime(restart_time, "%A, %B %d, at %I:%M %p")
    restart_duration = support.time_converter(second=second)

    if models.settings.physical_cores == models.settings.logical_cores:
        output = (
            f"You're running {system}, with {models.settings.physical_cores} "
            f"physical cores, and {models.settings.logical_cores} logical cores. "
        )
    else:
        output = f"You're running {system}, with {models.settings.physical_cores} CPU cores. "

    ram = support.size_converter(models.settings.ram)
    disk = support.size_converter(models.settings.disk)

    if vitals:
        ram_used = support.size_converter(psutil.virtual_memory().used)
        ram_percent = f"{util.format_nos(psutil.virtual_memory().percent)}%"
        disk_used = support.size_converter(psutil.disk_usage("/").used)
        disk_percent = f"{util.format_nos(psutil.disk_usage('/').percent)}%"
        output += (
            f"Your drive capacity is {disk}. You have used up {disk_used} at {disk_percent}. "
            f"Your RAM capacity is {ram}. You are currently utilizing {ram_used} at {ram_percent}. "
        )
        # noinspection PyUnboundLocalVariable
        output += f"Your CPU usage is at {cpu_percent.get()}%. "
    else:
        output += f"Your drive capacity is {disk}. Your RAM capacity is {ram}. "

    output += (
        f"Your {models.settings.device} was last booted on {restart_time}. "
        f"Current boot time is: {restart_duration}. "
    )

    support.write_screen(text=output)
    speaker.speak(text=output)
