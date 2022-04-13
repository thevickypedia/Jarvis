import os
from multiprocessing import Process
from typing import Dict, NoReturn

from playsound import playsound

from api.server import trigger_api
from executors.location import write_current_location
from executors.logger import logger
from executors.offline import automator, initiate_tunneling
from executors.telegram import handler
from modules.audio import speech_synthesis
from modules.models import models
from modules.utils import shared

fileio = models.fileio
docker_container = speech_synthesis.SpeechSynthesizer()


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
    playsound(sound=f"indicators{os.path.sep}initialize.mp3", block=False)
    return processes


def stop_processes() -> NoReturn:
    """Stops all background processes initiated during startup and removes database source file."""
    for func, process in shared.processes.items():
        if process.is_alive():
            logger.info(f"Sending [SIGTERM] to {func} with PID: {process.pid}")
            process.terminate()
        if process.is_alive():
            logger.info(f"Sending [SIGKILL] to {func} with PID: {process.pid}")
            process.kill()
    [os.remove(db) for db in [fileio.base_db] if os.path.isfile(db)]
