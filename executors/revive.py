import os
import random
import subprocess
import sys
from time import perf_counter

import yaml

from executors.custom_logger import logger
from modules.audio import listener, speaker
from modules.conditions import conversation, keywords
from modules.utils import globals, support


def restart(target: str = None, quiet: bool = False, quick: bool = False) -> None:
    """Restart triggers ``restart.py`` which in turn starts Jarvis after 5 seconds.

    Notes:
        - Doing this changes the PID to avoid any Fatal Errors occurred by long-running threads.
        - restart(PC) will restart the machine after getting confirmation.

    Warnings:
        - | Restarts the machine without approval when ``uptime`` is more than 2 days as the confirmation is requested
          | in `system_vitals <https://thevickypedia.github.io/Jarvis/#jarvis.system_vitals>`__.
        - This is done ONLY when the system vitals are read, and the uptime is more than 2 days.

    Args:
        target:
            - ``None``: Restarts Jarvis to reset PID
            - ``PC``: Restarts the machine after getting confirmation.
        quiet: If a boolean ``True`` is passed, a silent restart will be performed.
        quick: If a boolean ``True`` is passed, smart device IPs are stored in ``smart_devices.yaml`` for quick re-use.

    Raises:
        KeyboardInterrupt: To stop Jarvis' PID.
    """
    if target:
        if globals.called_by_offline['status']:
            logger.warning(f"ERROR::Cannot restart {globals.hosted_device.get('device')} via offline communicator.")
            return
        if target == 'PC':
            speaker.speak(text=f"{random.choice(conversation.confirmation)} restart your "
                               f"{globals.hosted_device.get('device')}?",
                          run=True)
            converted = listener.listen(timeout=3, phrase_limit=3)
        else:
            converted = 'yes'
        if any(word in converted.lower() for word in keywords.ok):
            support.stop_terminal()
            subprocess.call(['osascript', '-e', 'tell app "System Events" to restart'])
            raise KeyboardInterrupt
        else:
            speaker.speak(text="Machine state is left intact sir!")
            return
    globals.STOPPER['status'] = True
    logger.info('JARVIS::Restarting Now::STOPPER flag has been set.')
    logger.info(f'Called by {sys._getframe(1).f_code.co_name}')  # noqa
    sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}\t"
                     f"Total runtime: {support.time_converter(perf_counter())}")
    if not quiet:
        try:
            if not globals.called_by_offline['status']:
                speaker.speak(text='Restarting now sir! I will be up and running momentarily.', run=True)
        except RuntimeError as error:
            logger.fatal(error)
    if quick:
        if not globals.smart_devices.get('SOURCE'):
            # Set restart flag so the source file will be deleted after restart
            globals.smart_devices.update({'restart': True})
        with open('smart_devices.yaml', 'w') as file:
            yaml.dump(stream=file, data=globals.smart_devices)
    os.system('python3 restart.py')
    exit(1)
