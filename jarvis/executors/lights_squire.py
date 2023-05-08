import random
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process
from typing import List, NoReturn, Union

from jarvis.modules.audio import speaker
from jarvis.modules.database import database
from jarvis.modules.lights import preset_values, smart_lights
from jarvis.modules.models import models
from jarvis.modules.utils import support

db = database.Database(database=models.fileio.base_db)


def turn_off(host: str) -> NoReturn:
    """Turns off the device.

    Args:
        host: Takes target device IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Turn Off').turn_off()


def warm(host: str) -> NoReturn:
    """Sets lights to warm/yellow.

    Args:
        host: Takes target device IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=1,
                              operation='Warm Lights').update_device(r=0, g=0, b=0, warm_white=255)


def cool(host: str) -> NoReturn:
    """Sets lights to cool/white.

    Args:
        host: Takes target device IP address as an argument.
    """
    smart_lights.MagicHomeApi(device_ip=host, device_type=2,
                              operation='Cool Lights').update_device(r=255, g=255, b=255, warm_white=255,
                                                                     cool_white=255)


def lumen(host: str, rgb: int = 255) -> NoReturn:
    """Sets lights to custom brightness.

    Args:
        host: Takes target device IP address as an argument.
        rgb: Red, Green andBlue values to alter the brightness.
    """
    args = {'r': 255, 'g': 255, 'b': 255, 'warm_white': rgb}
    smart_lights.MagicHomeApi(device_ip=host, device_type=1, operation='Custom Brightness').update_device(**args)


def preset(device_ip, color: int = None, speed: int = 100) -> NoReturn:
    """Changes light colors to preset values.

    Args:
        device_ip: Takes target device IP address as an argument.
        color: Preset value extracted from list of color codes. Defaults to a random color code.
        speed: Speed of color change. Defaults to 100.
    """
    smart_lights.MagicHomeApi(device_ip=device_ip, operation='Preset Values', device_type=2).send_preset_function(
        preset_number=color or random.choice(list(preset_values.PRESET_VALUES.values())), speed=speed
    )


def runner(host_ip: List[str]) -> NoReturn:
    """Runs a never ending loop setting random light IP addresses to random color preset values.

    Args:
        host_ip: Takes list of light IP addresses as argument.
    """
    while True:
        with ThreadPoolExecutor(max_workers=len(host_ip)) as executor:
            executor.map(preset, host_ip)


def check_status() -> Union[str, int, None]:
    """Retrieve process ID from the ``party`` table.

    Returns:
        Process.pid:
        Process ID if party mode is enabled.
    """
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT pid FROM party").fetchone()
    return state


def remove_status() -> NoReturn:
    """Removes all entries from the ``party`` table."""
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM party")
        db.connection.commit()


def update_status(process: Process) -> NoReturn:
    """Update the ``children`` and ``party`` tables with process ID.

    Args:
        process: Process for which the PID has to be stored in database.
    """
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("UPDATE children SET party=null")
        cursor.execute("INSERT or REPLACE INTO party (pid) VALUES (?);", (process.pid,))
        cursor.execute("INSERT or REPLACE INTO children (party) VALUES (?);", (process.pid,))
        db.connection.commit()


def party_mode(host_ip: List[str], phrase: str) -> bool:
    """Handles party mode by altering colors in given light hostnames with random color codes.

    Args:
        host_ip: List of light IP addresses.
        phrase: Takes the phrase spoken as an argument.

    Returns:
        bool:
        True if party mode has to be disabled.
    """
    state = check_status()
    if 'enable' in phrase:
        if state:
            speaker.speak(text=f'Party mode has already been enabled {models.env.title}!')
        else:
            speaker.speak(text=f'Enabling party mode! Enjoy yourself {models.env.title}!')
            process = Process(target=runner, args=(host_ip,))
            process.start()
            update_status(process=process)
    elif 'disable' in phrase:
        if state:
            speaker.speak(text=f'Party mode has been disabled {models.env.title}! Hope you enjoyed it.')
            support.stop_process(pid=int(state[0]))
            remove_status()
            return True
        else:
            speaker.speak(text=f'Party mode was never enabled {models.env.title}!')
    else:
        state_ = 'enabled' if state else 'disabled'
        speaker.speak(text=f"Party mode is currently {state_} {models.env.title}! "
                           "You can ask me to enable or disable party mode.")
