import os
import subprocess
import warnings
from collections.abc import Generator
from datetime import datetime

import yaml

from jarvis.api.squire import scheduler
from jarvis.modules.crontab import expression
from jarvis.modules.exceptions import InvalidArgument
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import models

LOG_FILE = os.path.join('logs', 'cron_%d-%m-%Y.log')  # Used by api functions that run on cron schedule


def executor(statement: str, log_file: str = None) -> None:
    """Executes a cron statement.

    Args:
        statement: Cron statement to be executed.
        log_file: Log file for crontab execution logs.

    Warnings:
        - Executions done by crontab executor are not stopped when Jarvis is stopped.
        - On the bright side, almost all executions made by Jarvis are short-lived.
    """
    if not log_file:
        log_file = multiprocessing_logger(filename=LOG_FILE)
    with open(log_file, 'a') as file:
        file.write('\n')
        try:
            subprocess.call(statement, shell=True, stdout=file, stderr=file)
        except Exception as error:
            if isinstance(error, subprocess.CalledProcessError):
                result = error.output.decode(encoding='UTF-8').strip()
                file.write(f"[{error.returncode}]: {result}\n")
            else:
                file.write(f"{error}\n")


def validate_jobs(log: bool = True) -> Generator[expression.CronExpression]:
    """Validates each of the cron job.

    Args:
        log: Takes a boolean flag to suppress info level logging.

    Yields:
        CronExpression:
        CronExpression object.
    """
    if os.path.isfile(models.fileio.crontab):
        cron_info = []
        with open(models.fileio.crontab) as file:
            try:
                cron_info = yaml.load(stream=file, Loader=yaml.FullLoader) or []
            except yaml.YAMLError as error:
                logger.error(error)
                warnings.warn(
                    "CRONTAB :: Invalid file format."
                )
                # rename to avoid getting triggered in a loop
                os.rename(src=models.fileio.crontab,
                          dst=datetime.now().strftime(os.path.join(models.fileio.root, 'crontab_%d-%m-%Y.yaml')))
        for idx in cron_info:
            try:
                cron = expression.CronExpression(idx)
            except InvalidArgument as error:
                logger.error(error)
                os.rename(src=models.fileio.crontab,
                          dst=datetime.now().strftime(os.path.join(models.fileio.root, 'crontab_%d-%m-%Y.yaml')))
                continue
            if log:
                msg = f"{cron.comment!r} will be executed as per the schedule {cron.expression!r}"
                logger.info(msg)
            yield cron
    if models.env.author_mode:
        if all((models.env.robinhood_user, models.env.robinhood_pass, models.env.robinhood_pass)):
            yield scheduler.rh_cron_schedule(extended=True)
        yield scheduler.sm_cron_schedule(include_weekends=True)
