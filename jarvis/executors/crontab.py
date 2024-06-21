import os
import subprocess
from collections.abc import Generator

from jarvis.api.squire import scheduler
from jarvis.executors import files
from jarvis.modules.crontab import expression
from jarvis.modules.exceptions import InvalidArgument
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import models

# Used by api functions that run on cron schedule
LOG_FILE = os.path.join("logs", "cron_%d-%m-%Y.log")


def executor(statement: str, log_file: str = None, process_name: str = None) -> None:
    """Executes a cron statement.

    Args:
        statement: Cron statement to be executed.
        log_file: Log file for crontab execution logs.
        process_name: Process name for the execution.

    Warnings:
        - Executions done by crontab executor are not stopped when Jarvis is stopped.
        - On the bright side, almost all executions made by Jarvis are short-lived.
    """
    if not log_file:
        log_file = multiprocessing_logger(filename=LOG_FILE)
    if not process_name:
        process_name = "crontab_executor"
    process_name = "_".join(process_name.split())
    command = f"export PROCESS_NAME={process_name} && {statement}"
    logger.debug("Executing '%s' as '%s'", statement, command)
    with open(log_file, "a") as file:
        file.write("\n")
        try:
            subprocess.call(command, shell=True, stdout=file, stderr=file)
        except Exception as error:
            if isinstance(error, subprocess.CalledProcessError):
                result = error.output.decode(encoding="UTF-8").strip()
                file.write(f"[{error.returncode}]: {result}")
            else:
                file.write(error.__str__())


def validate_jobs(log: bool = True) -> Generator[expression.CronExpression]:
    """Validates each of the cron job.

    Args:
        log: Takes a boolean flag to suppress info level logging.

    Yields:
        CronExpression:
        CronExpression object.
    """
    for idx in files.get_crontab():
        try:
            cron = expression.CronExpression(idx)
        except InvalidArgument as error:
            logger.error(error)
            os.rename(src=models.fileio.crontab, dst=models.fileio.tmp_crontab)
            continue
        if log:
            msg = f"{cron.comment!r} will be executed as per the schedule {cron.expression!r}"
            logger.info(msg)
        yield cron
    if models.env.author_mode:
        if all(
            (
                models.env.robinhood_user,
                models.env.robinhood_pass,
                models.env.robinhood_pass,
            )
        ):
            yield scheduler.rh_cron_schedule(extended=True)
        yield scheduler.sm_cron_schedule(include_weekends=True)
