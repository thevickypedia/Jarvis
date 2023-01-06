import os
import warnings
from multiprocessing import Process
from typing import Dict, List, NoReturn, Union

import psutil
import yaml

from api.server import fast_api
from executors.connection import wifi_connector
from executors.offline import automator, background_tasks, tunneling
from executors.telegram import telegram_api
from modules.audio.speech_synthesis import speech_synthesizer
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
    """Deletes entries from all databases except for the tables assigned to hold data forever."""
    with db.connection:
        cursor = db.connection.cursor()
        for table, column in models.TABLES.items():
            if table in models.KEEP_TABLES:
                continue
            # Use f-string or %s as table names cannot be parametrized
            data = cursor.execute(f'SELECT * FROM {table}').fetchall()
            logger.info(f"Deleting data from {table}: "
                        f"{support.matrix_to_flat_list([list(filter(None, d)) for d in data if any(d)])}")
            cursor.execute(f"DELETE FROM {table}")


def create_process_mapping(processes: Dict[str, Process], func_name: str = None) -> NoReturn:
    """Creates or updates the processes mapping file.

    Args:
        processes: Dictionary of process names and the process.
        func_name: Function name of each process.

    See Also:
        - This is a special function, that uses doc strings to create a python dict.

    Handles:
        - speech_synthesizer: Speech Synthesis
        - telegram_api: Telegram Bot
        - fast_api: Offline communicator, Robinhood report gatherer, Jarvis UI, Stock monitor, Surveillance
        - automator: Home automation, Alarms and Reminders, Timed sync for Meetings and Events
        - background_tasks: Cron jobs, Custom background tasks
        - tunneling: Reverse Proxy
        - wifi_connector: Wi-Fi Re-connector
    """
    impact_lib = {doc.strip().split(':')[0].lstrip('- '): doc.strip().split(':')[1].strip().split(', ')
                  for doc in create_process_mapping.__doc__.split('Handles:')[1].splitlines() if doc.strip()}
    if not func_name and list(impact_lib.keys()) != list(processes.keys()):
        warnings.warn(message=f"{list(impact_lib.keys())} does not match {list(processes.keys())}")
    if func_name:  # Assumes a processes mapping file exists already, since flag passed during process specific restart
        with open(models.fileio.processes) as file:
            dump = yaml.load(stream=file, Loader=yaml.FullLoader)
        dump[func_name] = [processes[func_name].pid, impact_lib[func_name]]
    else:
        dump = {k: [v.pid, impact_lib[k]] for k, v in processes.items()}
        dump["jarvis"] = [models.settings.pid, ["Main Process"]]
    logger.debug(f"Processes data: {dump}")
    # Remove temporary processes that doesn't need to be stored in mapping file
    if dump.get("tunneling"):
        del dump["tunneling"]
    if dump.get("speech_synthesizer"):
        del dump["speech_synthesizer"]
    with open(models.fileio.processes, 'w') as file:
        yaml.dump(stream=file, data=dump, indent=4)


def start_processes(func_name: str = None) -> Union[Process, Dict[str, Process]]:
    """Initiates multiple background processes to achieve parallelization.

    Args:
        func_name: Name of the function that has to be started.

    Returns:
        Union[Process, Dict[str, Process]]:
        Returns a process object if a function name is passed, otherwise a mapping of function name and process objects.

    See Also:
        - speech_synthesizer: Initiates larynx docker image for speech synthesis.
        - telegram_api: Initiates message polling for Telegram bot to execute offline commands.
        - fast_api: Initiates uvicorn server to process offline commands, stock monitor and robinhood report generation.
        - automator: Initiates automator that executes timed tasks, store calendar and meetings information in database.
        - background_tasks: Initiates internal background tasks and runs cron jobs.
        - tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - wifi_connector: Initiates Wi-Fi connection handler to lookout for Wi-Fi disconnections and reconnect.
    """
    process_dict = {
        speech_synthesizer.__name__: Process(target=speech_synthesizer),
        telegram_api.__name__: Process(target=telegram_api),
        fast_api.__name__: Process(target=fast_api),
        automator.__name__: Process(target=automator),
        background_tasks.__name__: Process(target=background_tasks),
        tunneling.__name__: Process(target=tunneling),
        wifi_connector.__name__: Process(target=wifi_connector)  # Run individually as socket needs timed wait
    }
    processes = {func_name: process_dict[func_name]} if func_name else process_dict
    for func, process in processes.items():
        process.start()
        logger.info(f"Started function: {func} with PID: {process.pid}")
    create_process_mapping(processes=processes, func_name=func_name)
    return processes[func_name] if func_name else processes


def stop_child_processes() -> NoReturn:
    """Stops sub processes (for meetings and events) triggered by child processes."""
    children: Dict[str, List[int]] = {}
    with db.connection:
        cursor = db.connection.cursor()
        for child in models.TABLES["children"]:
            # Use f-string or %s as condition cannot be parametrized
            data = cursor.execute(f"SELECT {child} FROM children").fetchall()
            children[child]: List[int] = support.matrix_to_flat_list([list(filter(None, d)) for d in data if any(d)])
    logger.info(children)  # Include empty lists so logs have more information but will get skipped when looping anyway
    for category, pids in children.items():
        for pid in pids:
            try:
                proc = psutil.Process(pid=pid)
            except psutil.NoSuchProcess:
                # Occurs commonly since child processes run only for a short time and `INSERT OR REPLACE` leaves dupes
                logger.debug(f"Process [{category}] PID not found {pid}")
                continue
            logger.info(f"Stopping process [{category}] with PID: {pid}")
            support.stop_process(pid=proc.pid)


def stop_processes(func_name: str = None) -> NoReturn:
    """Stops all background processes initiated during startup and removes database source file."""
    stop_child_processes() if not func_name else None
    for func, process in shared.processes.items():
        if func_name and func_name != func:
            continue
        logger.info(f"Stopping process [{func}] with PID: {process.pid}")
        support.stop_process(pid=process.pid)
