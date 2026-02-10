import logging
import os
import pathlib
import shutil
import sys
from datetime import datetime
from typing import List

import dotenv
import psutil
import yaml

dotenv.load_dotenv(".keep.env", override=True)


def get_env(keys: List[str], default: str = None) -> str | None:
    """Get environment variables with case insensitivity.

    Args:
        keys: Options for the key.
        default: Default value.

    Returns:
        str:
        Returns the value for the given key.
    """
    for _key, _value in os.environ.items():
        if _key.lower() in keys:
            return _value
    return default


LOGS_PATH = get_env(["LOGS_PATH"], os.path.join(os.path.expanduser("~"), "KeepAlive"))
ENTRYPOINT = get_env(["ENTRYPOINT"], "temp_trigger.py")

BASE_PATH = pathlib.Path(__file__).parent.parent
LOGGER = logging.getLogger(__name__)
os.makedirs(LOGS_PATH, exist_ok=True)
LOGFILE_PATH = datetime.now().strftime(os.path.join(LOGS_PATH, "jarvis_%d-%m-%Y.log"))
handler = logging.FileHandler(filename=LOGFILE_PATH)
handler.setFormatter(
    fmt=logging.Formatter(
        datefmt="%b-%d-%Y %I:%M:%S %p",
        fmt="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
    )
)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)


def check_processes() -> bool | None:
    """Check processes.yaml file to get the PID and check if it is running.

    Returns:
        bool:
        Returns a boolean flag to indicate if the process is running.
    """
    processes = BASE_PATH / "fileio" / "processes.yaml"
    try:
        data = yaml.load(processes.open(), Loader=yaml.FullLoader) or {}
    except FileNotFoundError as warning:
        LOGGER.warning(warning)
        return False
    try:
        for pid, _ in data["jarvis"].items():
            process = psutil.Process(pid)
            assert process.is_running(), f"Process {pid} is NOT running!"
            LOGGER.info(f"JARVIS [{pid}] is running. Source: {processes.name!r}")
            return True
    except (KeyError, psutil.NoSuchProcess, AssertionError) as warning:
        LOGGER.warning(warning)
        return False


def check_running_processes() -> bool:
    """Check all running processes using psutil to check if Jarvis is running.

    Returns:
        bool:
        Returns a boolean flag to indicate if Jarvis' entrypoint is running.
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        if "python" in proc.info["name"].lower():
            if ENTRYPOINT in proc.info["cmdline"]:
                LOGGER.info(f"JARVIS [{proc.pid}] is running. Source: {ENTRYPOINT!r}")
                return True
    return False


def run_in_terminal() -> None:
    """Triggers the entrypoint in a new terminal."""
    LOGGER.info("Initiating Jarvis.")
    python = shutil.which("python") or sys.executable
    pyenv = python.replace("/bin/python", "/bin/activate")
    initiate = f"cd {BASE_PATH} && source {pyenv} && python {ENTRYPOINT}"
    os.system(f"""osascript -e 'tell application "Terminal" to do script "{initiate}"' > /dev/null""")


def main() -> None:
    """Check and trigger Jarvis if not running already."""
    LOGGER.info("Checking processes.yaml")
    if check_processes():
        return
    LOGGER.info("Checking all processes")
    if check_running_processes():
        return
    LOGGER.info("Initiating Jarvis")
    run_in_terminal()
    with open(LOGFILE_PATH, "a") as file:
        file.write("\n\n")


if __name__ == "__main__":
    main()
