import os
from multiprocessing import Process
from typing import Dict, List, NoReturn, Tuple, Union

import psutil

from api.server import trigger_api
from executors.location import write_current_location
from executors.logger import logger
from executors.offline import automator, initiate_tunneling
from executors.telegram import handler
from modules.audio.speech_synthesis import synthesizer
from modules.database import database
from modules.models import models
from modules.retry import retry
from modules.utils import shared

db = database.Database(database=models.fileio.base_db)


@retry.retry(attempts=3, interval=2, warn=True)
def delete_db() -> NoReturn:
    """Delete base db if exists. Called upon restart or shut down."""
    if os.path.isfile(models.fileio.base_db):
        logger.info(f"Removing {models.fileio.base_db}")
        os.remove(models.fileio.base_db)
    if os.path.isfile(models.fileio.base_db):
        raise FileExistsError(
            f"{models.fileio.base_db} still exists!"
        )
    return


def clear_db() -> NoReturn:
    """Deletes entries from all databases except for VPN."""
    with db.connection:
        cursor = db.connection.cursor()
        logger.info(f"Deleting data from {models.env.event_app}: "
                    f"{cursor.execute(f'SELECT * FROM {models.env.event_app}').fetchall()}")
        cursor.execute(f"DELETE FROM {models.env.event_app}")
        logger.info(f"Deleting data from ics: {cursor.execute(f'SELECT * FROM ics').fetchall()}")
        cursor.execute("DELETE FROM ics")
        logger.info(f"Deleting data from stopper: {cursor.execute(f'SELECT * FROM stopper').fetchall()}")
        cursor.execute("DELETE FROM stopper")
        logger.info(f"Deleting data from restart: {cursor.execute(f'SELECT * FROM restart').fetchall()}")
        cursor.execute("DELETE FROM restart")
        logger.info(f"Deleting data from children: {cursor.execute(f'SELECT * FROM children').fetchall()}")
        cursor.execute("DELETE FROM children")


def start_processes(func_name: str = None) -> Union[Process, Dict[str, Process]]:
    """Initiates multiple background processes to achieve parallelization.

    Methods
        - poll_for_messages: Initiates polling for messages on the telegram bot.
        - trigger_api: Initiates Jarvis API using uvicorn server to receive offline commands.
        - automator: Initiates automator that executes offline commands and certain functions at said time.
        - initiate_tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - write_current_location: Writes current location details into a yaml file.
        - speech_synthesis: Initiates larynx docker image.
        - playsound: Plays a start-up sound.
    """
    processes = {
        "handler": Process(target=handler),
        "trigger_api": Process(target=trigger_api),
        "automator": Process(target=automator),
        "initiate_tunneling": Process(target=initiate_tunneling),
        "write_current_location": Process(target=write_current_location),
        "synthesizer": Process(target=synthesizer)
    }
    if func_name:
        processes = {func_name: processes[func_name]}
    for func, process in processes.items():
        process.start()
        logger.info(f"Started function: {func} {process.sentinel} with PID: {process.pid}")
    return processes[func_name] if func_name else processes


def stop_child_processes() -> NoReturn:
    """Stops sub processes (for meetings and events) triggered by child processes."""
    children = {}
    with db.connection:
        cursor = db.connection.cursor()
        # children = cursor.execute("SELECT meetings, events, crontab FROM children").fetchall()
        children['meetings']: List[Tuple[Union[None, str]]] = cursor.execute("SELECT meetings FROM children").fetchall()
        children['crontab']: List[Tuple[Union[None, str]]] = cursor.execute("SELECT events FROM children").fetchall()
        children['events']: List[Tuple[Union[None, str]]] = cursor.execute("SELECT crontab FROM children").fetchall()
    logger.info(children)
    for category, pids in children.items():
        pids = pids[0]
        if not pids:
            continue
        for pid in pids:
            if not pid:
                continue
            try:
                proc = psutil.Process(pid=pid)
            except psutil.NoSuchProcess:
                # Occurs commonly since child processes run only for a short time
                logger.debug(f"Process [{category}] PID not found {pid}")
                continue
            if proc.is_running():
                logger.info(f"Sending [SIGTERM] to child process [{category}] with PID: {pid}")
                proc.terminate()
            if proc.is_running():
                logger.info(f"Sending [SIGKILL] to child process [{category}] with PID: {pid}")
                proc.kill()


def stop_processes(func_name: str = None) -> NoReturn:
    """Stops all background processes initiated during startup and removes database source file."""
    stop_child_processes() if not func_name or func_name in ["automator"] else None
    for func, process in shared.processes.items():
        if func_name and func_name != func:
            continue
        if process.is_alive():
            logger.info(f"Sending [SIGTERM] to {func} with PID: {process.pid}")
            process.terminate()
        if process.is_alive():
            logger.info(f"Sending [SIGKILL] to {func} with PID: {process.pid}")
            process.kill()
