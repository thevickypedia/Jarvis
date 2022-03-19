import os
import random
import subprocess
import sys
import time
from threading import Thread

import psutil
import yaml

from executors import meetings
from executors.display_functions import decrease_brightness
from executors.logger import logger
from modules.audio import listener, speaker, voices, volume
from modules.conditions import conversation, keywords
from modules.database import database
from modules.models import models
from modules.utils import globals, support

rdb = database.Database(table_name='restart', columns=['flag', 'caller'])
env = models.env
fileio = models.fileio


def restart(target: str = None, quiet: bool = False) -> None:
    """Restart triggers ``restart.py`` which in turn starts Jarvis after 5 seconds.

    Notes:
        - Doing this changes the PID to avoid any Fatal Errors occurred by long-running threads.
        - restart(PC) will restart the machine after getting confirmation.

    Warnings:
        - | Restarts the machine without approval when ``uptime`` is more than 2 days as the confirmation is requested
          | in `system_vitals <https://thevickypedia.github.io/Jarvis/#executors.system.system_vitals>`__.
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
        if target == 'PC':
            speaker.speak(text=f"{random.choice(conversation.confirmation)} restart your "
                               f"{globals.hosted_device.get('device')}?",
                          run=True)
            converted = listener.listen(timeout=3, phrase_limit=3)
        else:
            converted = 'yes'
        if any(word in converted.lower() for word in keywords.ok):
            stop_terminals()
            subprocess.call(['osascript', '-e', 'tell app "System Events" to restart'])
            raise KeyboardInterrupt
        else:
            speaker.speak(text=f"Machine state is left intact {env.title}!")
            return
    sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}\t"
                     f"Total runtime: {support.time_converter(time.perf_counter())}")
    if not quiet:
        try:
            speaker.speak(text=f'Restarting now {env.title}! I will be up and running momentarily.', run=True)
        except RuntimeError as error:
            logger.fatal(error)
    if os.path.isfile(fileio.location):
        with open(fileio.location) as file:
            data = yaml.load(stream=file, Loader=yaml.FullLoader)
        data["timestamp"] = int(time.time())
        with open(fileio.location, 'w') as file:
            yaml.dump(stream=file, data=data)
    os.system('python restart.py')
    exit(1)


def exit_process() -> None:
    """Function that holds the list of operations done upon exit."""
    reminders = {}
    alarms = support.lock_files(alarm_files=True)
    if reminder_files := support.lock_files(reminder_files=True):
        for file in reminder_files:
            split_val = file.replace('.lock', '').split('-')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        logger.info(f'JARVIS::Deleting Reminders - {reminders}')
        if len(reminders) == 1:
            speaker.speak(text=f'You have a pending reminder {env.title}!')
        else:
            speaker.speak(text=f'You have {len(reminders)} pending reminders {env.title}!')
        for key, value in reminders.items():
            speaker.speak(text=f"{value.replace('_', ' ')} at {key.lstrip('0').replace('00', '').replace('_', ' ')}")
    if alarms:
        alarms = ', and '.join(alarms) if len(alarms) != 1 else ''.join(alarms)
        alarms = alarms.replace('.lock', '').replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')
        speaker.speak(text=f"You have a pending alarm at {alarms} {env.title}!")
    if reminders or alarms:
        speaker.speak(text="This will not be executed while I'm asleep!")
    speaker.speak(text=f"Shutting down now {env.title}!")
    try:
        speaker.speak(text=support.exit_message(), run=True)
    except RuntimeError as error:
        logger.fatal(f"Received a RuntimeError while self terminating.\n{error}")
    sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                     f"\nTotal runtime: {support.time_converter(time.perf_counter())}")


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
        speaker.speak(text=f"Activating sentry mode, enjoy yourself {env.title}!")
        if globals.greet_check:
            globals.greet_check.pop('status')
    return True


def restart_control(phrase: str = 'PlaceHolder', quiet: bool = False):
    """Controls the restart functions based on the user request.

    Args:
        phrase: Takes the phrase spoken as an argument.
        quiet: Take a boolean flag to restart without warning.
    """
    phrase = phrase.lower()
    if 'pc' in phrase or 'computer' in phrase or 'imac' in phrase:
        logger.info(f'JARVIS::Restart for {globals.hosted_device.get("device")} has been requested.')
        restart(target='PC')
    else:
        caller = sys._getframe(1).f_code.co_name  # noqa
        logger.info(f'Called by {caller}')
        logger.info('JARVIS::Self reboot has been requested.')
        if quiet:  # restarted due internal errors or git update
            rdb.cursor.execute("INSERT INTO restart (flag, caller) VALUES (?,?);", (True, caller))
        else:  # restarted requested via voice command
            rdb.cursor.execute("INSERT INTO restart (flag, caller) VALUES (?,?);", (True, 'restart_control'))
        rdb.connection.commit()


def stop_terminals(apps: tuple = ("iterm", "terminal")) -> None:
    """Stops background processes.

    Args:
        apps: Default apps that have to be shutdown when ``deep`` argument is not set.
    """
    for proc in psutil.process_iter():
        if any(word in proc.name().lower() for word in apps):
            proc.terminate()
            time.sleep(0.5)
            if proc.is_running():
                proc.kill()


def terminator() -> None:
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc.

    Using this, eliminates the hassle of forcing multiple threads to stop.
    """
    pid = os.getpid()
    proc = psutil.Process(pid=pid)
    logger.info(f"Terminating process: {pid}")
    try:
        proc.wait(timeout=5)
    except psutil.TimeoutExpired:
        logger.warning(f"Failed to terminate process in 5 seconds: {pid}")
    if proc.is_running():
        logger.info(f"{pid} is still running. Killing it.")
        proc.kill()


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
            stop_terminals()
            subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
            raise KeyboardInterrupt
        else:
            speaker.speak(text=f"Machine state is left intact {env.title}!")
            return


def clear_logs() -> None:
    """Deletes log files that were updated before 48 hours."""
    for __path, __directory, __file in os.walk('logs'):
        for file_ in __file:
            if int(time.time() - os.stat(f'{__path}/{file_}').st_mtime) > 172_800:
                os.remove(f'{__path}/{file_}')  # removes the file if it is older than 48 hours


def starter() -> None:
    """Initiates crucial functions which needs to be called during start up.

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
