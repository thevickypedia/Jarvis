import os
import random
import shutil
import stat
import subprocess
import sys
import time
from datetime import timedelta
from threading import Thread
from typing import NoReturn

import docker
import psutil
import pybrightness
import pywslocker

from jarvis.executors import listener_controls, system, volume, word_match
from jarvis.modules.audio import listener, speaker, voices
from jarvis.modules.conditions import conversation, keywords
from jarvis.modules.database import database
from jarvis.modules.exceptions import StopSignal
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support

db = database.Database(database=models.fileio.base_db)


def restart(ask: bool = True) -> NoReturn:
    """Restart the host machine.

    Warnings:
        - | Restarts the machine without approval when ``uptime`` is more than 2 days as the confirmation is requested
          | in `system_vitals <https://thevickypedia.github.io/Jarvis/#executors.system.system_vitals>`__.
        - This is done ONLY when the system vitals are read, and the uptime is more than 2 days.

    Args:
        ask: Boolean flag to get confirmation from user.

    Raises:
        StopSignal:
        To stop Jarvis' PID.
    """
    if ask:
        speaker.speak(text=f"{random.choice(conversation.confirmation)} restart your "
                           f"{shared.hosted_device.get('device', 'machine')}?",
                      run=True)
        converted = listener.listen()
    else:
        converted = 'yes'
    if word_match.word_match(phrase=converted, match_list=keywords.keywords['ok']):
        stop_terminals()
        if models.settings.os == models.supported_platforms.macOS:
            subprocess.call(['osascript', '-e', 'tell app "System Events" to restart'])
        elif models.settings.os == models.supported_platforms.windows:
            os.system("shutdown /r /t 1")
        else:
            os.system(f"echo {models.env.root_password} | sudo -S reboot")
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
        logger.info("Deleting Reminders - %s", reminders)
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
        speaker.speak(text="This will not be executed while I'm deactivated!")
    speaker.speak(text=f"Shutting down now {models.env.title}!")
    try:
        speaker.speak(text=support.exit_message(), run=True)
    except RuntimeError as error:
        logger.critical("ATTENTION::Received a RuntimeError while self terminating.\n%s", error)
    support.write_screen(f"Memory consumed: {support.size_converter(0)}"
                         f"\nTotal runtime: {support.time_converter(second=time.time() - shared.start_time)}")


def sleep_control(*args) -> bool:
    """Locks the screen and reduces brightness to bare minimum."""
    Thread(target=pybrightness.decrease).start()
    pywslocker.lock()
    if not (shared.called['report'] or shared.called['time_travel']):
        speaker.speak(text=random.choice(conversation.acknowledgement))
    return True


def sentry(*args) -> bool:
    """Speaks sentry mode message and sets greeting value to false."""
    speaker.speak(text=f"Activating sentry mode, enjoy yourself {models.env.title}!")
    if shared.greeting:
        shared.greeting = False
    return True


def kill(*args) -> NoReturn:
    """Kills active listener.

    Raises:
        StopSignal:
        To stop main process.
    """
    raise StopSignal


def db_restart_entry(caller: str) -> NoReturn:
    """Writes an entry to the DB to restart the caller.

    Args:
        caller: Name of the process that has to be restarted.
    """
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("INSERT or REPLACE INTO restart (flag, caller) VALUES (?,?);", (True, caller))
        cursor.connection.commit()


def restart_control(phrase: str = None, quiet: bool = False) -> NoReturn:
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
    if shared.called_by_offline:  # restarted ONLY via automation.yaml
        logger.info("Restarting all background processes!")
        db_restart_entry(caller="OFFLINE")
        speaker.speak(text="Restarting all background processes!")  # this is only to log the response
        return
    if phrase:
        if not shared.hosted_device.get('device'):
            system.hosted_device_info()
        logger.info("Restart for %s has been requested.", shared.hosted_device.get('device'))
        restart()
    else:
        speaker.speak(text="I didn't quite get that. Did you mean restart your computer?")
        return


def stop_terminals(apps: tuple = ("iterm", "terminal")) -> NoReturn:
    """Stops background processes.

    Args:
        apps: Default apps that have to be shutdown when ``deep`` argument is not set.
    """
    for proc in psutil.process_iter():
        if word_match.word_match(phrase=proc.name(), match_list=apps):
            support.stop_process(pid=proc.pid)


def delete_docker_container() -> NoReturn:
    """Deletes the docker container spun up (if any) for speech synthesis.

    See Also:
        - | If the intention is to keep docker running forever, start the
          | docker container with the command in README before starting Jarvis.
    """
    if not os.path.isfile(models.fileio.speech_synthesis_id):
        return
    with open(models.fileio.speech_synthesis_id) as file:
        container_id = file.read()
    with open(models.fileio.speech_synthesis_log, "a") as log_file:
        if models.settings.os == models.supported_platforms.linux:
            log_file.write(f"Stopping running container {container_id!r}\n")
            try:
                subprocess.Popen([f'echo {models.env.root_password} | sudo -S docker stop {container_id}'],
                                 shell=True, bufsize=0, stdout=log_file, stderr=log_file)
            except (subprocess.CalledProcessError, subprocess.SubprocessError, FileNotFoundError) as error:
                if isinstance(error, subprocess.CalledProcessError):
                    result = error.output.decode(encoding='UTF-8').strip()
                    log_file.write(f"[{error.returncode}]: {result}\n")
                else:
                    log_file.write(str(error) + "\n")

            log_file.write(f"Removing existing container {container_id!r}\n")
            try:
                subprocess.Popen([f'echo {models.env.root_password} | sudo -S docker rm -f {container_id}'],
                                 shell=True, bufsize=0, stdout=log_file, stderr=log_file)
            except (subprocess.CalledProcessError, subprocess.SubprocessError, FileNotFoundError) as error:
                if isinstance(error, subprocess.CalledProcessError):
                    result = error.output.decode(encoding='UTF-8').strip()
                    log_file.write(f"[{error.returncode}]: {result}\n")
                else:
                    log_file.write(str(error) + "\n")
        else:
            from docker.errors import ContainerError, DockerException
            try:
                client = docker.from_env()
            except DockerException as error:
                log_file.write(error.__str__() + "\n")
            try:
                log_file.write(f"Stopping running container {container_id!r}\n")
                client.api.kill(container_id)
                log_file.write(f"Removing existing container {container_id!r}\n")
                client.api.remove_container(container_id)
            except ContainerError as error:
                log_file.write(error.__str__() + "\n")
        log_file.write(f"Removing cid file {models.fileio.speech_synthesis_id!r}\n")
        os.remove(models.fileio.speech_synthesis_id)


def terminator() -> NoReturn:
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc."""
    delete_docker_container()
    os.remove(models.fileio.processes) if os.path.isfile(models.fileio.processes) else None
    proc = psutil.Process(pid=models.settings.pid)
    process_info = proc.as_dict()
    if process_info.get('environ'):
        del process_info['environ']  # To ensure env vars are not printed in log files
    logger.debug(process_info)
    support.stop_process(pid=proc.pid)
    os._exit(1)  # noqa


def shutdown(*args, proceed: bool = False) -> NoReturn:
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
    if word_match.word_match(phrase=converted, match_list=keywords.keywords['ok']):
        stop_terminals()
        if models.settings.os == models.supported_platforms.macOS:
            subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
        elif models.settings.os == models.supported_platforms.windows:
            os.system("shutdown /s /t 1")
        else:
            os.system(f"echo {models.env.root_password} | sudo -S shutdown -P now")
        raise StopSignal
    else:
        speaker.speak(text=f"Machine state is left intact {models.env.title}!")


def delete_logs() -> NoReturn:
    """Delete log files that were updated before the log retention period. Checks if file's inode was changed."""
    for __path, __directory, __file in os.walk('logs'):
        for file_ in __file:
            inode_modified = os.stat(os.path.join(__path, file_)).st_ctime
            if timedelta(seconds=(time.time() - inode_modified)).days > models.env.log_retention:
                logger.debug("Deleting log file: %s", os.path.join(__path, file_))
                os.remove(os.path.join(__path, file_))  # removes the file if it is older than log retention time


def delete_pycache() -> NoReturn:
    """Deletes ``__pycache__`` folder from all sub-dir."""
    for __path, __directory, __file in os.walk(os.getcwd()):
        if '__pycache__' in __directory:
            if os.path.exists(os.path.join(__path, '__pycache__')):
                logger.debug("Deleting pycache: %s", os.path.join(__path, '__pycache__'))
                shutil.rmtree(os.path.join(__path, '__pycache__'))


def set_executable() -> NoReturn:
    """Modify file permissions for all the files within the fileio directory."""
    for file in os.listdir("fileio"):
        f_path = os.path.join("fileio", file)
        if not file.endswith('.cid'):
            os.chmod(f_path, os.stat(f_path).st_mode | stat.S_IEXEC)
    # [os.chmod(file, int('755', base=8) or 0o755) for file in os.listdir("fileio") if not file.endswith('.cid')]


def starter() -> NoReturn:
    """Initiates crucial functions which needs to be called during start up.

    Methods:
        - put_listener_state: To activate listener enabling voice conversations.
        - volume: To default the master volume 50%.
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
