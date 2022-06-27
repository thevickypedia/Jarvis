import os
from multiprocessing import Process
from typing import Dict, NoReturn

import psutil
from playsound import playsound

from api.server import trigger_api
from executors.location import write_current_location
from executors.logger import logger
from executors.offline import automator, initiate_tunneling
from executors.telegram import handler
from modules.audio import speech_synthesis
from modules.database import database
from modules.models import models
from modules.retry import retry
from modules.utils import shared

env = models.env
fileio = models.FileIO()
indicators = models.Indicators()
db = database.Database(database=fileio.base_db)
docker_container = speech_synthesis.SpeechSynthesizer()


@retry.retry(attempts=3, interval=2, warn=True)
def delete_db() -> NoReturn:
    """Delete base db if exists. Called upon restart or shut down."""
    if os.path.isfile(fileio.base_db):
        logger.info(f"Removing {fileio.base_db}")
        os.remove(fileio.base_db)
    if os.path.isfile(fileio.base_db):
        raise FileExistsError(
            f"{fileio.base_db} still exists!"
        )
    return


def start_processes() -> Dict[str, Process]:
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
        "telegram": Process(target=handler),
        "api": Process(target=trigger_api),
        "automator": Process(target=automator),
        "ngrok": Process(target=initiate_tunneling),
        "location": Process(target=write_current_location),
        "speech_synthesis": Process(target=docker_container.synthesizer)
    }
    for func, process in processes.items():
        process.start()
        logger.info(f"Started function: {func} {process.sentinel} with PID: {process.pid}")
    playsound(sound=indicators.initialize, block=False)
    return processes


def stop_child_processes() -> NoReturn:
    """Stops sub processes (for meetings and events) triggered by child processes."""
    with db.connection:
        cursor_ = db.connection.cursor()
        children = cursor_.execute("SELECT meetings, events FROM children").fetchone()
    for pid in children:
        if not pid:
            continue
        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess as error:
            logger.error(error)
            continue
        if proc.is_running():
            logger.info(f"Sending [SIGTERM] to child process with PID: {pid}")
            proc.terminate()
        if proc.is_running():
            logger.info(f"Sending [SIGKILL] to child process with PID: {pid}")
            proc.kill()


def stop_processes() -> NoReturn:
    """Stops all background processes initiated during startup and removes database source file."""
    stop_child_processes()
    for func, process in shared.processes.items():
        if process.is_alive():
            logger.info(f"Sending [SIGTERM] to {func} with PID: {process.pid}")
            process.terminate()
        if process.is_alive():
            logger.info(f"Sending [SIGKILL] to {func} with PID: {process.pid}")
            process.kill()
    delete_db()
