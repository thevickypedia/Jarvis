import os
import sqlite3
from multiprocessing import Process
from typing import Dict, List

from jarvis.executors import process_map
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.retry import retry
from jarvis.modules.utils import shared, support, util


@retry.retry(attempts=3, interval=2, warn=True)
def delete_db() -> None:
    """Delete base db if exists. Called upon restart or shut down."""
    if os.path.isfile(models.fileio.base_db):
        logger.info("Removing %s", models.fileio.base_db)
        os.remove(models.fileio.base_db)
    if os.path.isfile(models.fileio.base_db):
        raise FileExistsError(f"{models.fileio.base_db} still exists!")
    return


def clear_db() -> None:
    """Deletes entries from all databases except for the tables assigned to hold data forever."""
    with models.db.connection as connection:
        cursor = connection.cursor()
        for attr in models.tables.model_fields:
            table = getattr(models.tables, attr)
            if table.keep:
                continue
            # Use f-string or %s as table names cannot be parametrized
            data = cursor.execute(f"SELECT * FROM {table.name}").fetchall()
            logger.info(
                "Deleting data from %s: %s",
                table,
                util.matrix_to_flat_list(
                    [list(filter(None, d)) for d in data if any(d)]
                ),
            )
            cursor.execute(f"DELETE FROM {table.name}")


# noinspection LongLine
def create_process_mapping(
    processes: Dict[str, Dict[str, Process | List[str]]], func_name: str = None
) -> None:
    """Creates or updates the processes mapping file.

    Args:
        processes: Dictionary of process names, process id and their impact.
        func_name: Function name of the process.
    """
    if func_name:
        # Assumes a processes mapping file exists already, since flag is passed during process specific restart
        dump = process_map.get()
        dump[func_name] = {
            processes[func_name]["process"].pid: processes[func_name]["impact"]
        }
    else:
        dump = {
            k: {v["process"].pid: processes[k]["impact"]} for k, v in processes.items()
        }
        dump["jarvis"] = {models.settings.pid: ["Main Process"]}
    logger.debug("Processes data: %s", dump)
    process_map.add(dump)


def start_processes(func_name: str = None) -> Process | Dict[str, Process]:
    """Initiates multiple background processes to achieve parallelization.

    Args:
        func_name: Name of the function that has to be started.

    Returns:
        Process | Dict[str, Process]:
        Returns a process object if a function name is passed, otherwise a mapping of function name and process objects.

    See Also:
        - telegram_api: Initiates polling Telegram API to execute offline commands (if no webhook config is available)
        - jarvis_api: Initiates uvicorn server to process API requests, stock monitor and robinhood report generation.
        - background_tasks: Initiates internal background tasks, cron jobs, alarms, reminders, events and meetings sync.
        - plot_mic: Initiates plotting realtime microphone usage using matplotlib.
    """
    process_dict = process_map.base()
    # Used when a single process is requested to be triggered/restarted
    if func_name:
        processes: Dict[str, Process] = {func_name: process_dict[func_name]["process"]}
    else:
        processes: Dict[str, Process] = {
            func: process_dict[func]["process"] for func in process_dict.keys()
        }
    for func, process in processes.items():
        process.name = func
        process.start()
        logger.info(
            "Started function: {func} with PID: {pid}".format(
                func=func, pid=process.pid
            )
        )
    create_process_mapping(process_dict, func_name)
    return processes[func_name] if func_name else processes


def stop_child_processes() -> None:
    """Stops sub processes (for meetings and events) triggered by child processes."""
    children: Dict[str, List[int]] = {}
    with models.db.connection as connection:
        cursor = connection.cursor()
        for child in models.tables.children.columns:
            try:
                # Use f-string or %s as condition cannot be parametrized
                data = cursor.execute(f"SELECT {child} FROM children").fetchall()
                children[child]: List[int] = util.matrix_to_flat_list(
                    [list(filter(None, d)) for d in data if any(d)]
                )
            except sqlite3.OperationalError as error:
                logger.warning(error)
    # Include empty lists so logs have more information but will get skipped when looping anyway
    logger.info(children)
    for category, pids in children.items():
        for pid in pids:
            logger.debug("Stopping process [%s] with PID: %d", category, pid)
            support.stop_process(pid=pid)


def stop_processes(func_name: str = None) -> None:
    """Stops all background processes initiated during startup and removes database source file."""
    stop_child_processes() if not func_name else None
    for func, process in shared.processes.items():
        if func_name and func_name != func:
            continue
        logger.info("Stopping process [%s] with PID: %d", func, process.pid)
        support.stop_process(pid=process.pid)
