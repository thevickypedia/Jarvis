import random
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process
from typing import List

from jarvis.modules.audio import speaker
from jarvis.modules.lights import preset_values, smart_lights
from jarvis.modules.models import models
from jarvis.modules.utils import support

word_map = {
    "turn_on": ["turn on", "cool", "white"],
    "turn_off": ["turn off"],
    "party_mode": ["party mode"],
    "reset": ["reset"],
    "warm": ["warm", "yellow"],
    "set": ["set", "percentage", "percent", "%", "dim", "bright"],
}


def turn_off(host: str) -> None:
    """Turns off the device.

    Args:
        host: Takes target device's IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=1).turn_off()


def warm(host: str) -> None:
    """Sets lights to warm/yellow.

    Args:
        host: Takes target device's IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=1).update_device(
        r=0, g=0, b=0, warm_white=255
    )


def cool(host: str) -> None:
    """Sets lights to cool/white.

    Args:
        host: Takes target device's IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=2).update_device(
        r=255, g=255, b=255, warm_white=255, cool_white=255
    )


def lumen(host: str, rgb: int = 255) -> None:
    """Sets lights to custom brightness.

    Args:
        host: Takes target device's IP address as an argument.
        rgb: Red, Green andBlue values to alter the brightness.
    """
    args = {"r": 255, "g": 255, "b": 255, "warm_white": rgb}
    smart_lights.MagicHomeApi(device_ip=host, device_type=1).update_device(**args)


def preset(host: str, color: int = None, speed: int = 100) -> None:
    """Changes light colors to preset values.

    Args:
        host: Takes target device's IP address as an argument.
        color: Preset value extracted from list of color codes. Defaults to a random color code.
        speed: Speed of color change. Defaults to 100.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=2).send_preset_function(
        preset_number=color
        or random.choice(list(preset_values.PRESET_VALUES.values())),
        speed=speed,
    )


def runner(host: List[str]) -> None:
    """Runs a never ending loop setting random light IP addresses to random color preset values.

    Args:
        host: Takes list of lights' IP addresses as argument.
    """
    while True:
        with ThreadPoolExecutor(max_workers=len(host)) as executor:
            executor.map(preset, host)


def check_status() -> str | int | None:
    """Retrieve process ID from the ``party`` table.

    Returns:
        Process.pid:
        Process ID if party mode is enabled.
    """
    with models.db.connection as connection:
        cursor = connection.cursor()
        state = cursor.execute("SELECT pid FROM party").fetchone()
    return state


def remove_status() -> None:
    """Removes all entries from the ``party`` table."""
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM party")
        connection.commit()


def update_status(process: Process) -> None:
    """Update the ``children`` and ``party`` tables with process ID.

    Args:
        process: Process for which the PID has to be stored in database.
    """
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE children SET party=null")
        cursor.execute("INSERT or REPLACE INTO party (pid) VALUES (?);", (process.pid,))
        cursor.execute(
            "INSERT or REPLACE INTO children (party) VALUES (?);", (process.pid,)
        )
        connection.commit()


def party_mode(host: List[str], phrase: str) -> bool:
    """Handles party mode by altering colors in given light hostnames with random color codes.

    Args:
        host: Takes list of lights' IP addresses as argument.
        phrase: Takes the phrase spoken as an argument.

    Returns:
        bool:
        True if party mode has to be disabled.
    """
    state = check_status()
    if "enable" in phrase:
        if state:
            speaker.speak(
                text=f"Party mode has already been enabled {models.env.title}!"
            )
        else:
            speaker.speak(
                text=f"Enabling party mode! Enjoy yourself {models.env.title}!"
            )
            process = Process(target=runner, args=(host,))
            process.start()
            update_status(process=process)
    elif "disable" in phrase:
        if state:
            speaker.speak(
                text=f"Party mode has been disabled {models.env.title}! Hope you enjoyed it."
            )
            support.stop_process(pid=int(state[0]))
            remove_status()
            return True
        else:
            speaker.speak(text=f"Party mode was never enabled {models.env.title}!")
    else:
        state_ = "enabled" if state else "disabled"
        speaker.speak(
            text=f"Party mode is currently {state_} {models.env.title}! "
            "You can ask me to enable or disable party mode."
        )
