import os
import random
import subprocess
import sys
from datetime import datetime
from threading import Thread
from time import perf_counter

from executors import meetings
from executors.display_functions import decrease_brightness
from executors.logger import logger
from modules.audio import listener, speaker, voices, volume
from modules.conditions import conversation, keywords
from modules.utils import globals, support


def restart(target: str = None, quiet: bool = False) -> None:
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
            support.stop_processes()
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
    os.system('python3 restart.py')
    exit(1)


def exit_process() -> None:
    """Function that holds the list of operations done upon exit."""
    globals.STOPPER['status'] = True
    logger.info('JARVIS::Stopping Now::STOPPER flag has been set to True')
    reminders = {}
    alarms = support.lock_files(alarm_files=True)
    if reminder_files := support.lock_files(reminder_files=True):
        for file in reminder_files:
            split_val = file.replace('.lock', '').split('-')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        logger.info(f'JARVIS::Deleting Reminders - {reminders}')
        if len(reminders) == 1:
            speaker.speak(text='You have a pending reminder sir!')
        else:
            speaker.speak(text=f'You have {len(reminders)} pending reminders sir!')
        for key, value in reminders.items():
            speaker.speak(text=f"{value.replace('_', ' ')} at "
                               f"{key.replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')}")
    if alarms:
        logger.info(f'JARVIS::Deleting Alarms - {alarms}')
        alarms = ', and '.join(alarms) if len(alarms) != 1 else ''.join(alarms)
        alarms = alarms.replace('.lock', '').replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')
        speaker.speak(text=f'You have a pending alarm at {alarms} sir!')
    if reminders or alarms:
        speaker.speak(text='This will be removed while shutting down!')
    speaker.speak(text='Shutting down now sir!')
    try:
        speaker.speak(text=support.exit_message(), run=True)
    except RuntimeError as error:
        logger.fatal(f'Received a RuntimeError while self terminating.\n{error}')
    support.remove_files()
    sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                     f"\nTotal runtime: {support.time_converter(perf_counter())}")


def pc_sleep() -> None:
    """Locks the host device using osascript and reduces brightness to bare minimum."""
    Thread(target=decrease_brightness).start()
    # os.system("""osascript -e 'tell app "System Events" to sleep'""")  # requires restarting Jarvis manually
    os.system("""osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'""")
    if not (globals.called['report'] or globals.called['time_travel']):
        speaker.speak(text=random.choice(conversation.acknowledgement))


def sleep_control(phrase: str) -> bool:
    """Controls whether to stop listening or to put the host device on sleep.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    if 'pc' in phrase or 'computer' in phrase or 'imac' in phrase or \
            'screen' in phrase:
        pc_sleep()
    else:
        speaker.speak(text="Activating sentry mode, enjoy yourself sir!")
        if globals.greet_check:
            globals.greet_check.pop('status')
    return True


def restart_control(phrase: str):
    """Controls the restart functions based on the user request.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    if 'pc' in phrase or 'computer' in phrase or 'imac' in phrase:
        logger.info(f'JARVIS::Restart for {globals.hosted_device.get("device")} has been requested.')
        restart(target='PC')
    else:
        logger.info('JARVIS::Self reboot has been requested.')
        restart()


def shutdown(proceed: bool = False) -> None:
    """Gets confirmation and turns off the machine.

    Args:
        proceed: Boolean value whether to get confirmation.

    Raises:
        KeyboardInterrupt: To stop Jarvis' PID.
    """
    if not proceed:
        speaker.speak(text=f"{random.choice(conversation.confirmation)} turn off the machine?", run=True)
        converted = listener.listen(timeout=3, phrase_limit=3)
    else:
        converted = 'yes'
    if converted != 'SR_ERROR':
        if any(word in converted.lower() for word in keywords.ok):
            support.stop_processes(deep=True)
            subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
            raise KeyboardInterrupt
        else:
            speaker.speak(text="Machine state is left intact sir!")
            return


def clear_logs() -> None:
    """Deletes log files that were updated before 48 hours."""
    [os.remove(f"logs/{file}") for file in os.listdir('logs') if int(datetime.now().timestamp()) - int(
        os.stat(f'logs/{file}').st_mtime) > 172_800] if os.path.exists('logs') else None


def starter() -> None:
    """Initiates crucial functions which needs to be called during start up.

    Loads the ``.env`` file so that all the necessary credentials and api keys can be accessed as ``ENV vars``

    Methods:
        - volume_controller: To default the master volume 50%.
        - voice_default: To change the voice to default value.
        - clear_logs: To purge log files older than 48 hours.
    """
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 10)  # increases the recursion limit by 10 times
    volume.volume(level=50)
    voices.voice_default()
    clear_logs()
    meetings.meeting_app_launcher()


def stopper() -> None:
    """Sets the key of ``STOPPER`` flag to True."""
    globals.STOPPER['status'] = True
