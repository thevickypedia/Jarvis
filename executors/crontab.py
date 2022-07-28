import os
import subprocess
from datetime import datetime
from typing import NoReturn


def log_file() -> str:
    """Creates a log file and writes the headers into it.

    Returns:
        str:
        Log filename.
    """
    filename = datetime.now().strftime(os.path.join('logs', 'crontab_%d-%m-%Y.log'))
    write = ''.join(['*' for _ in range(120)])
    with open(filename, 'a+') as file:
        file.seek(0)
        if not file.read():
            file.write(f"{write}\n")
        else:
            file.write(f"\n{write}\n")
    return filename


def crontab_executor(statement: str) -> NoReturn:
    """Executes a cron statement.

    Args:
        statement: Cron statement to be executed.
    """
    with open(log_file(), "a") as file:
        try:
            subprocess.call(statement, shell=True, stdout=file, stderr=file)
        except (subprocess.CalledProcessError, subprocess.SubprocessError, Exception) as error:
            file.write(error)
