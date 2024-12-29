import os
import shutil
from datetime import datetime
from multiprocessing import Process
from typing import Dict, List

import yaml

from jarvis.api.server import jarvis_api
from jarvis.executors import crontab, offline, telegram
from jarvis.modules.logger import logger
from jarvis.modules.microphone import graph_mic
from jarvis.modules.models import models


def base() -> Dict[str, Dict[str, Process | List[str]]]:
    """Creates a base mapping with all the processes handled by Jarvis.

    Returns:
        Dict[str, Dict[str, Process | List[str]]]:
        Nested dictionary of process mapping.
    """
    base_mapping = {
        # process map will not be removed
        jarvis_api.__name__: {
            "process": Process(target=jarvis_api),
            "impact": [
                "Offline communicator",
                "Robinhood portfolio report",
                "Jarvis UI",
                "Stock monitor",
                "Surveillance",
                "Telegram",
            ],
        },
        # process map will not be removed
        offline.background_tasks.__name__: {
            "process": Process(target=offline.background_tasks),
            "impact": [
                "Home automation",
                "Alarms",
                "Reminders",
                "Meetings and Events sync",
                "Wi-Fi connector",
                "Cron jobs",
                "Background tasks",
            ],
        },
        # process map will be removed if telegram bot is hosted via Jarvis API
        telegram.telegram_api.__name__: {
            "process": Process(target=telegram.telegram_api),
            "impact": ["Telegram Bot"],
        },
    }
    if models.env.plot_mic:
        statement = shutil.which(cmd="python") + " " + graph_mic.__file__
        # process map will be removed if plot_mic is disabled
        base_mapping[graph_mic.plot_mic.__name__] = {
            "process": Process(
                target=crontab.executor,
                kwargs={
                    "statement": statement,
                    "log_file": datetime.now().strftime(
                        os.path.join("logs", "mic_plotter_%d-%m-%Y.log")
                    ),
                    "process_name": graph_mic.plot_mic.__name__,
                },
            ),
            "impact": ["Realtime microphone usage plotter"],
        }
    return base_mapping


def get() -> Dict[str, Dict[int, List[str]]]:
    """Get the existing process map.

    Returns:
        Dict[str, Dict[int, List[str]]]:
        Returns the dictionary of process data and the impact information.
    """
    with open(models.fileio.processes) as file:
        return yaml.load(stream=file, Loader=yaml.FullLoader)


def add(data: Dict[str, Dict[int, List[str]]]) -> None:
    """Dumps the process map data into the mapping file.

    Args:
        data: Dictionary of process data and the impact information.
    """
    with open(models.fileio.processes, "w") as file:
        yaml.dump(stream=file, data=data)


def remove(func_name: str) -> None:
    """Remove process map for a function that has stopped running.

    Args:
        func_name: Name of the function that has to be removed from the mapping.
    """
    with open(models.fileio.processes) as file:
        process_map = yaml.load(stream=file, Loader=yaml.FullLoader)
    logger.debug(process_map)
    if process_map.get(func_name):
        logger.info(
            "%s: %s has been removed from processes mapping",
            func_name,
            process_map[func_name],
        )
        del process_map[func_name]
    logger.debug(process_map)
    with open(models.fileio.processes, "w") as file:
        yaml.dump(data=process_map, stream=file)


def update(func_name: str, old_pid: int, new_pid: int) -> None:
    """Remove process map for a function that has stopped running.

    Args:
        func_name: Name of the function that has to be removed from the mapping.
        old_pid: Old process ID that needs to be updating.
        new_pid: New process ID that needs to be updated.
    """
    with open(models.fileio.processes) as file:
        process_map = yaml.load(stream=file, Loader=yaml.FullLoader)
    logger.debug(process_map)
    if process_map.get(func_name) and process_map[func_name].get(old_pid):
        _temp = process_map[func_name][old_pid]
        del process_map[func_name][old_pid]
        process_map[func_name][new_pid] = _temp
        logger.info(
            "%s has been updated from pid '%d' to pid '%d'", func_name, old_pid, new_pid
        )
    logger.debug(process_map)
    with open(models.fileio.processes, "w") as file:
        yaml.dump(data=process_map, stream=file)
