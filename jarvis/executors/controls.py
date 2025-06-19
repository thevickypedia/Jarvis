import os
import random
import shutil
import stat
import subprocess
import sys
import time
from datetime import timedelta
from threading import Thread, Timer
from typing import NoReturn

import psutil
import pybrightness
import pywslocker

from jarvis.executors import alarm, files, listener_controls, remind, volume, word_match
from jarvis.modules.audio import listener, speaker, voices
from jarvis.modules.conditions import conversation, keywords
from jarvis.modules.exceptions import StopSignal
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.utils import shared, support, util


def restart(ask: bool = True) -> None:
    """Restart the host machine.

    Warnings:
        - | Restarts the machine without approval when ``uptime`` is more than 2 days as the confirmation is requested
          | in `system_vitals <https://jarvis-docs.vigneshrao.com/#executors.system.system_vitals>`__.
        - This is done ONLY when the system vitals are read, and the uptime is more than 2 days.

    Args:
        ask: Boolean flag to get confirmation from user.

    Raises:
        StopSignal:
        To stop Jarvis' PID.
    """
    if ask:
        speaker.speak(
            text=f"{random.choice(conversation.confirmation)} restart your {models.settings.device or 'machine'}?",
            run=True,
        )
        converted = listener.listen()
    else:
        converted = "yes"
    if word_match.word_match(phrase=converted, match_list=keywords.keywords["ok"]):
        stop_terminals()
        if models.settings.os == enums.SupportedPlatforms.macOS:
            subprocess.call(["osascript", "-e", 'tell app "System Events" to restart'])
        elif models.settings.os == enums.SupportedPlatforms.windows:
            os.system("shutdown /r /t 1")
        else:
            if models.env.root_password:
                os.system(f"echo {models.env.root_password} | sudo -S reboot")
            else:
                support.no_env_vars()
                return
        raise StopSignal
    else:
        speaker.speak(text=f"Machine state is left intact {models.env.title}!")


def exit_process() -> None:
    """Function that holds the list of operations done upon exit."""
    if reminders := remind.get_reminder_state():
        if len(reminders) == 1:
            speaker.speak(text=f"You have a pending reminder {models.env.title}!")
        else:
            speaker.speak(
                text=f"You have {len(reminders)} pending reminders {models.env.title}!"
            )
        # No need for string.capwords as speaker runs in a new loop
        speaker.speak(text=util.comma_separator(reminders))
    if alarms := alarm.get_alarm_state():
        if len(alarms) == 1:
            speaker.speak(text="You have a pending alarm at ")
        else:
            speaker.speak(
                text=f"You have {len(alarms)} pending alarms {models.env.title}!"
            )
        speaker.speak(text=util.comma_separator(alarms))
    if reminders or alarms:
        speaker.speak(text="This will not be executed while I'm deactivated!")
    speaker.speak(text=f"Shutting down now {models.env.title}!")
    try:
        speaker.speak(text=support.exit_message(), run=True)
    except RuntimeError as error:
        logger.critical(
            "ATTENTION::Received a RuntimeError while self terminating.\n%s", error
        )
    support.write_screen(
        f"Memory consumed: {support.size_converter(0)}"
        f"\nTotal runtime: {support.time_converter(second=time.time() - shared.start_time)}\n"
    )


def sleep_control(*args) -> bool:
    """Locks the screen and reduces brightness to bare minimum."""
    Thread(target=pybrightness.decrease, args=(logger,)).start()
    pywslocker.lock(logger)
    if not shared.called["report"]:
        speaker.speak(text=random.choice(conversation.acknowledgement))
    return True


def sentry(*args) -> bool:
    """Speaks sentry mode message and sets greeting value to false."""
    speaker.speak(text=f"Activating sentry mode, enjoy yourself {models.env.title}!")
    if shared.greeting:
        shared.greeting = False
    return True


def kill(*args) -> None:
    """Kills active listener.

    Raises:
        StopSignal:
        To stop main process.
    """
    raise StopSignal


def db_restart_entry(caller: str) -> None:
    """Writes an entry to the DB to restart the caller.

    Args:
        caller: Name of the process that has to be restarted.
    """
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT or REPLACE INTO restart (flag, caller) VALUES (?,?);",
            (True, caller),
        )
        cursor.connection.commit()


def restart_control(phrase: str = None, quiet: bool = False) -> None:
    """Controls the restart functions based on the user request.

    Args:
        phrase: Takes the phrase spoken as an argument.
        quiet: Take a boolean flag to restart without warning.
    """
    if quiet:  # restarted by child processes due internal errors
        caller = sys._getframe(1).f_code.co_name  # noqa
        logger.info("Restarting '%s'", caller)
        db_restart_entry(caller=caller)
        return
    if shared.called_by_offline:
        if phrase:
            if "all" in phrase.lower().split():
                logger.info("Restarting all background processes!")
                # set as timer, so that process doesn't get restarted without returning response to user
                # without timer, the process will keep getting restarted in a loop
                Timer(
                    interval=5, function=db_restart_entry, kwargs=dict(caller="OFFLINE")
                ).start()
                speaker.speak(text="Restarting all background processes!")
                return
            if avail := list(files.get_processes().keys()):
                # cannot be restarted
                avail.remove("jarvis")
            else:
                speaker.speak(
                    text="Unable to fetch background processes. Try specifying 'all'"
                )
                return
            if func := word_match.word_match(
                phrase=phrase, match_list=avail, strict=True
            ):
                logger.info("Restarting %s", func)
                # set as timer, so that process doesn't get restarted without returning response to user
                # without timer, the process will keep getting restarted in a loop
                Timer(
                    interval=5, function=db_restart_entry, kwargs=dict(caller=func)
                ).start()
                speaker.speak(text=f"Restarting the background process {func!r}")
            else:
                speaker.speak(
                    text=f"Please specify a function name. Available: {util.comma_separator(avail)}"
                )
        else:
            speaker.speak(text="Invalid request to restart.")
        return
    if phrase:
        logger.info("Restart for %s has been requested.", models.settings.device)
        restart()
    else:
        speaker.speak(
            text="I didn't quite get that. Did you mean restart your computer?"
        )
        return


def stop_terminals(apps: tuple = ("iterm", "terminal")) -> None:
    """Stops background processes.

    Args:
        apps: Default apps that have to be shutdown when ``deep`` argument is not set.
    """
    for proc in psutil.process_iter():
        if word_match.word_match(phrase=proc.name(), match_list=apps):
            support.stop_process(pid=proc.pid)


def terminator() -> NoReturn:
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc."""
    files.delete(path=models.fileio.processes)
    files.delete(path=models.fileio.secure_send)
    proc = psutil.Process(pid=models.settings.pid)
    process_info = proc.as_dict()
    if process_info.get("environ"):
        del process_info["environ"]  # To ensure env vars are not printed in log files
    logger.debug(process_info)
    support.stop_process(pid=proc.pid)
    # noinspection PyUnresolvedReferences,PyProtectedMember
    os._exit(0)


def shutdown(*args, proceed: bool = False) -> None:
    """Gets confirmation and turns off the machine.

    Args:
        proceed: Boolean value whether to get confirmation.

    Raises:
        StopSignal: To stop Jarvis' PID.
    """
    if not proceed:
        speaker.speak(
            text=f"{random.choice(conversation.confirmation)} turn off the machine?",
            run=True,
        )
        converted = listener.listen()
    else:
        converted = "yes"
    if word_match.word_match(phrase=converted, match_list=keywords.keywords["ok"]):
        stop_terminals()
        if models.settings.os == enums.SupportedPlatforms.macOS:
            subprocess.call(
                ["osascript", "-e", 'tell app "System Events" to shut down']
            )
        elif models.settings.os == enums.SupportedPlatforms.windows:
            os.system("shutdown /s /t 1")
        else:
            if models.env.root_password:
                os.system(f"echo {models.env.root_password} | sudo -S shutdown -P now")
            else:
                support.no_env_vars()
                return
        raise StopSignal
    else:
        speaker.speak(text=f"Machine state is left intact {models.env.title}!")


def delete_logs() -> None:
    """Delete log files that were updated before the log retention period. Checks if file's inode was changed."""
    for __path, __directory, __file in os.walk("logs"):
        for file_ in __file:
            inode_modified = os.stat(os.path.join(__path, file_)).st_ctime
            if (
                timedelta(seconds=(time.time() - inode_modified)).days
                > models.env.log_retention
            ):
                logger.debug("Deleting log file: %s", os.path.join(__path, file_))
                # removes the file if it is older than log retention time
                os.remove(os.path.join(__path, file_))


def delete_pycache() -> None:
    """Deletes ``__pycache__`` folder from all sub-dir."""
    for __path, __directory, __file in os.walk(os.getcwd()):
        if "__pycache__" in __directory:
            if os.path.exists(os.path.join(__path, "__pycache__")):
                logger.debug(
                    "Deleting pycache: %s", os.path.join(__path, "__pycache__")
                )
                shutil.rmtree(os.path.join(__path, "__pycache__"))


def set_executable() -> None:
    """Modify file permissions for all the files within the fileio directory."""
    for file in os.listdir("fileio"):
        f_path = os.path.join("fileio", file)
        if not file.endswith(".cid"):
            os.chmod(f_path, os.stat(f_path).st_mode | stat.S_IEXEC)
    # [os.chmod(file, int('755', base=8) or 0o755) for file in os.listdir("fileio") if not file.endswith('.cid')]


def starter() -> None:
    """Initiates crucial functions which needs to be called during start up.

    Methods:
        - put_listener_state: To activate listener enabling voice conversations.
        - volume: To default the master volume a specific percent.
        - voices: To change the voice to default value.
        - delete_logs: To purge log files older than the set log retention time.
        - delete_pycache: To purge pycache directories.
        - set_executable: To allow access to all the files within ``fileio`` directory.
    """
    listener_controls.put_listener_state(state=True)
    volume.volume(level=models.env.volume)
    voices.voice_default()
    try:
        delete_logs()
        delete_pycache()
        set_executable()
    except Exception as error:  # can be ignored and troubleshooted later
        logger.critical("ATTENTION:: Failed at some startup steps.")
        logger.critical(error)
