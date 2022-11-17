import ctypes
import os
import random
import shutil
import stat
import subprocess
import sys
import time
from threading import Thread
from typing import NoReturn

import psutil

from executors.display_functions import decrease_brightness
from executors.volume import volume
from executors.word_match import word_match
from modules.audio import listener, speaker, voices
from modules.conditions import conversation, keywords
from modules.database import database
from modules.exceptions import StopSignal
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import shared, support

db = database.Database(database=models.fileio.base_db)
ram = support.size_converter(byte_size=models.settings.ram).replace('.0', '')


def restart(ask: bool = True) -> NoReturn:
    """Restart the host machine.

    Warnings:
        - | Restarts the machine without approval when ``uptime`` is more than 2 days as the confirmation is requested
          | in `system_vitals <https://thevickypedia.github.io/Jarvis/#executors.system.system_vitals>`__.
        - This is done ONLY when the system vitals are read, and the uptime is more than 2 days.

    Args:
        ask: Boolean flag to get confirmation from user.

    Raises:
        StopSignal: To stop Jarvis' PID.
    """
    if ask:
        speaker.speak(text=f"{random.choice(conversation.confirmation)} restart your "
                           f"{shared.hosted_device.get('device', 'machine')}?",
                      run=True)
        converted = listener.listen()
    else:
        converted = 'yes'
    if word_match(phrase=converted, match_list=keywords.keywords.ok):
        stop_terminals()
        if models.settings.macos:
            subprocess.call(['osascript', '-e', 'tell app "System Events" to restart'])
        else:
            os.system("shutdown /r /t 1")
        raise StopSignal
    else:
        speaker.speak(text=f"Machine state is left intact {models.env.title}!")


def exit_process() -> NoReturn:
    """Function that holds the list of operations done upon exit."""
    reminders = {}
    alarms = support.lock_files(alarm_files=True)
    if reminder_files := support.lock_files(reminder_files=True):
        for file in reminder_files:
            split_val = file.replace('.lock', '').split('|')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        logger.info(f'JARVIS::Deleting Reminders - {reminders}')
        if len(reminders) == 1:
            speaker.speak(text=f'You have a pending reminder {models.env.title}!')
        else:
            speaker.speak(text=f'You have {len(reminders)} pending reminders {models.env.title}!')
        for key, value in reminders.items():
            speaker.speak(text=f"{value.replace('_', ' ')} at {key.lstrip('0').replace('00', '').replace('_', ' ')}")
    if alarms:
        alarms = ', and '.join(alarms) if len(alarms) != 1 else ''.join(alarms)
        alarms = alarms.replace('.lock', '').replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')
        speaker.speak(text=f"You have a pending alarm at {alarms} {models.env.title}!")
    if reminders or alarms:
        speaker.speak(text="This will not be executed while I'm asleep!")
    speaker.speak(text=f"Shutting down now {models.env.title}!")
    try:
        speaker.speak(text=support.exit_message(), run=True)
    except RuntimeError as error:
        logger.critical(f"Received a RuntimeError while self terminating.\n{error}")
    sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                     f"\nTotal runtime: {support.time_converter(time.perf_counter())}")


def sleep_control() -> bool:
    """Locks the screen and reduces brightness to bare minimum."""
    Thread(target=decrease_brightness).start()
    # os.system("""osascript -e 'tell app "System Events" to sleep'""")  # requires restarting Jarvis manually
    # subprocess.call('rundll32.exe user32.dll, LockWorkStation')
    if models.settings.macos:
        os.system(
            """osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'"""
        )
    else:
        ctypes.windll.user32.LockWorkStation()
    if not (shared.called['report'] or shared.called['time_travel']):
        speaker.speak(text=random.choice(conversation.acknowledgement))
    return True


def check_memory_leak() -> NoReturn:
    """Check memory utilization."""
    for func, process in shared.processes.items():
        if not process.is_alive():
            logger.warning(f"{func}[{process.pid}] is not running anymore.")
            return func
        try:
            proc = psutil.Process(pid=process.pid)
            percent_raw = int(proc.as_dict().get('memory_percent', 1))
            if percent_raw > 20:
                percent = support.size_converter(byte_size=percent_raw).replace(' B', ' %')
                ram_used = support.size_converter(byte_size=proc.memory_info().rss)
                logger.info(f"{process.pid}: {ram_used}/{ram} :: {percent}")
                with db.connection:
                    cursor = db.connection.cursor()
                    cursor.execute("INSERT or REPLACE INTO restart (flag, caller) VALUES (?,?);", (True, func))
                    cursor.connection.commit()
        except psutil.NoSuchProcess:
            logger.warning(f"{func}[{process.pid}] is not running anymore.")
            return func


def sentry() -> bool:
    """Speaks sentry mode message and sets greeting value to false."""
    speaker.speak(text=f"Activating sentry mode, enjoy yourself {models.env.title}!")
    if shared.greeting:
        shared.greeting = False
    return True


def restart_control(phrase: str = None, quiet: bool = False) -> NoReturn:
    """Controls the restart functions based on the user request.

    Args:
        phrase: Takes the phrase spoken as an argument.
        quiet: Take a boolean flag to restart without warning.
    """
    if phrase and ('pc' in phrase.lower() or 'computer' in phrase.lower() or 'machine' in phrase.lower()):
        logger.info(f'JARVIS::Restart for {shared.hosted_device.get("device")} has been requested.')
        restart()
    else:
        caller = sys._getframe(1).f_code.co_name  # noqa
        logger.info(f'Called by {caller!r}')
        if quiet:  # restarted due internal errors
            logger.info(f"Restarting {caller!r}")
        elif shared.called_by_offline:  # restarted via automator
            logger.info("Restarting all background processes!")
            caller = "OFFLINE"
        else:
            speaker.speak(text="I didn't quite get that. Did you mean restart your computer?")
            return
        with db.connection:
            cursor = db.connection.cursor()
            cursor.execute("INSERT or REPLACE INTO restart (flag, caller) VALUES (?,?);", (True, caller))
            cursor.connection.commit()


def stop_terminals(apps: tuple = ("iterm", "terminal")) -> NoReturn:
    """Stops background processes.

    Args:
        apps: Default apps that have to be shutdown when ``deep`` argument is not set.
    """
    for proc in psutil.process_iter():
        if word_match(phrase=proc.name(), match_list=apps):
            support.stop_process(pid=proc.pid)


def terminator() -> NoReturn:
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc.

    Using this, eliminates the hassle of forcing multiple threads to stop.
    """
    proc = psutil.Process(pid=models.settings.pid)
    process_info = proc.as_dict()
    if process_info.get('environ'):
        del process_info['environ']
    logger.info(process_info)
    support.stop_process(pid=proc.pid)
    os._exit(1)  # noqa


def shutdown(proceed: bool = False) -> NoReturn:
    """Gets confirmation and turns off the machine.

    Args:
        proceed: Boolean value whether to get confirmation.

    Raises:
        StopSignal: To stop Jarvis' PID.
    """
    if not proceed:
        speaker.speak(text=f"{random.choice(conversation.confirmation)} turn off the machine?", run=True)
        converted = listener.listen()
    else:
        converted = 'yes'
    if converted and word_match(phrase=converted, match_list=keywords.keywords.ok):
        stop_terminals()
        if models.settings.macos:
            subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
        else:
            os.system("shutdown /s /t 1")
        raise StopSignal
    else:
        speaker.speak(text=f"Machine state is left intact {models.env.title}!")


def clear_logs() -> NoReturn:
    """Deletes log files that were updated before 48 hours."""
    for __path, __directory, __file in os.walk('logs'):
        for file_ in __file:
            if int(time.time() - os.stat(os.path.join(__path, file_)).st_mtime) > 172_800:
                os.remove(os.path.join(__path, file_))  # removes the file if it is older than 48 hours


def delete_pycache() -> NoReturn:
    """Deletes ``__pycache__`` folder from all sub-dir."""
    for __path, __directory, __file in os.walk(os.getcwd()):
        if '__pycache__' in __directory:
            deletion = os.path.join(__path, '__pycache__')
            if os.path.exists(deletion):
                shutil.rmtree(deletion)


def starter() -> NoReturn:
    """Initiates crucial functions which needs to be called during start up.

    Methods:
        - volume_controller: To default the master volume 50%.
        - voice_default: To change the voice to default value.
        - clear_logs: To purge log files older than 48 hours.
    """
    volume(level=models.env.volume)
    voices.voice_default()
    clear_logs()
    delete_pycache()
    for file in os.listdir("fileio"):
        f_path = os.path.join("fileio", file)
        os.chmod(f_path, os.stat(f_path).st_mode | stat.S_IEXEC)
    # [os.chmod(file, int('755', base=8) or 0o755) for file in os.listdir("fileio")]
