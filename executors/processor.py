import os
from multiprocessing import Process
from typing import Dict, List, NoReturn, Tuple, Union

import psutil

from api.server import trigger_api
from executors.offline import automator, initiate_tunneling
from executors.telegram import handler
from modules.audio.speech_synthesis import synthesizer
from modules.database import database
from modules.logger.custom_logger import logger
from modules.models import models
from modules.retry import retry
from modules.utils import shared, support

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
        for table, column in models.TABLES.items():
            if table == "vpn" or table == "party" or table == "stock":
                continue
            logger.info(f"Deleting data from {table}: {cursor.execute(f'SELECT * FROM {table}').fetchall()}")
            cursor.execute(f"DELETE FROM {table}")


def start_processes(func_name: str = None) -> Union[Process, Dict[str, Process]]:
    """Initiates multiple background processes to achieve parallelization.

    Methods
        - poll_for_messages: Initiates polling for messages on the telegram bot.
        - trigger_api: Initiates Jarvis API using uvicorn server to receive offline commands.
        - automator: Initiates automator that executes offline commands and certain functions at said time.
        - initiate_tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - speech_synthesis: Initiates larynx docker image.
        - playsound: Plays a start-up sound.
    """
    processes = {
        "handler": Process(target=handler),
        "trigger_api": Process(target=trigger_api),
        "automator": Process(target=automator),
        "initiate_tunneling": Process(target=initiate_tunneling),
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
        for child in models.TABLES["children"]:
            children[child]: List[Tuple[Union[None, str]]] = cursor.execute(f"SELECT {child} FROM children").fetchall()
    logger.info(children)
    for category, pids in children.items():
        for pid in pids:
            pid = pid[0]
            if not pid:
                continue
            try:
                proc = psutil.Process(pid=pid)
            except psutil.NoSuchProcess:
                # Occurs commonly since child processes run only for a short time
                logger.debug(f"Process [{category}] PID not found {pid}")
                continue
            logger.info(f"Stopping process [{category}] with PID: {pid}")
            support.stop_process(pid=proc.pid)


def stop_processes(func_name: str = None) -> NoReturn:
    """Stops all background processes initiated during startup and removes database source file."""
    stop_child_processes() if not func_name or func_name in ["automator"] else None
    for func, process in shared.processes.items():
        if func_name and func_name != func:
            continue
        logger.info(f"Stopping process [{func}] with PID: {process.pid}")
        support.stop_process(pid=process.pid)
