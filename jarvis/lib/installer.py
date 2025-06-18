# noinspection PyUnresolvedReferences
"""This is a special module that installs all the downstream dependencies for Jarvis.

>>> Installer

See Also:
    - Uses ``subprocess`` module to run the installation process.
    - Triggered by commandline interface using the command ``jarvis install``
    - Installs OS specific and OS-agnostic dependencies.
    - Has specific sections for main and dev dependencies.

Warnings:
    - Unlike other pypi packages, ``pip install jarvis-ironman`` will only download the package.
    - Running ``jarvis install`` is what actually installs all the dependent packages.
"""

import logging
import os
import platform
import re
import shutil
import string
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, NoReturn

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
if os.environ.get("JARVIS_VERBOSITY", "-1") == "1":
    verbose = " --verbose"
else:
    verbose = ""
uv_install = {
    "option": os.environ.get("UV_INSTALL", "-1").lower() in ("1", "true", "yes")
}


def convert_seconds(seconds: int | float, n_elem: int = 2) -> str:
    """Calculate years, months, days, hours, minutes, seconds, and milliseconds from given input.

    Args:
        seconds: Number of seconds to convert (supports float values).
        n_elem: Number of elements required from the converted list.

    Returns:
        str:
        Returns a humanized string notion of the number of seconds.
    """
    if not seconds:
        return "0s"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"

    seconds_in_year = 365 * 24 * 3600
    seconds_in_month = 30 * 24 * 3600

    years = seconds // seconds_in_year
    seconds %= seconds_in_year

    months = seconds // seconds_in_month
    seconds %= seconds_in_month

    days = seconds // (24 * 3600)
    seconds %= 24 * 3600

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60
    seconds %= 60

    milliseconds = round((seconds % 1) * 1000)
    seconds = int(seconds)  # Convert remaining seconds to int for display

    time_parts = []

    if years > 0:
        time_parts.append(f"{int(years)} year{'s' if years > 1 else ''}")
    if months > 0:
        time_parts.append(f"{int(months)} month{'s' if months > 1 else ''}")
    if days > 0:
        time_parts.append(f"{int(days)} day{'s' if days > 1 else ''}")
    if hours > 0:
        time_parts.append(f"{int(hours)} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        time_parts.append(f"{int(minutes)} minute{'s' if minutes > 1 else ''}")
    if seconds > 0 or milliseconds > 0:
        if seconds > 0 and milliseconds > 0:
            time_parts.append(f"{seconds + milliseconds / 1000:.1f}s")
        elif seconds > 0:
            time_parts.append(f"{seconds}s")
        else:
            time_parts.append(f"{milliseconds}ms")

    if len(time_parts) == 1:
        return time_parts[0]

    list_ = time_parts[:n_elem]
    return ", and ".join(
        [", ".join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_
    )


class Runtime:
    """A context manager that captures runtime for a given execution.

    Using context manager:
        >>> with Runtime() as runtime:
        >>>     bin(2018)
        >>> print(runtime.get())

    Manually:
        >>> runtime = Runtime()
        >>> runtime.start()
        >>> time.sleep(10)
        >>> runtime.stop()
        >>> print(runtime.get())
    """

    def __init__(self, breakout: int = 2):
        """Instantiates the Runtime object."""
        self.breakout = breakout
        self.start_time = None
        self.end_time = None

    def __enter__(self) -> "Runtime":
        """Entrypoint for context manager.

        Returns:
            Runtime:
            Returns a reference to the self object.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit function for context manager."""
        self.stop()

    def start(self) -> None:
        """Manually start the timer."""
        self.start_time = time.time()

    def stop(self) -> None | NoReturn:
        """Manually stop the timer."""
        if self.start_time is None:
            raise ValueError("Timer was never started.")
        self.end_time = time.time()

    def get(self) -> None | NoReturn:
        """Retrieve the elapsed time."""
        if not all((self.start_time, self.end_time)):
            raise ValueError(
                "Runtime not captured. Ensure you call `stop()` before `get()`."
            )
        return convert_seconds(self.end_time - self.start_time, n_elem=self.breakout)


def pretext() -> str:
    """Pre-text to gain reader's attention in the terminal."""
    return "".join(["*" for _ in range(os.get_terminal_size().columns)])


def center(text: str) -> str:
    """Aligns text to center of the terminal and returns it."""
    return text.center(os.get_terminal_size().columns)


def get_arch() -> str | NoReturn:
    """Classify system architecture into known categories.

    Returns:
        Returns exit code 1 if no architecture was detected.
    """
    machine: str = platform.machine().lower()
    if "aarch64" in machine or "arm64" in machine:
        architecture: str = "arm64"
    elif "64" in machine:
        architecture: str = "amd64"
    elif "86" in machine:
        architecture: str = "386"
    elif "armv5" in machine:
        architecture: str = "armv5"
    elif "armv6" in machine:
        architecture: str = "armv6"
    elif "armv7" in machine:
        architecture: str = "armv7"
    elif machine:
        architecture: str = machine
    else:
        logger.info(pretext())
        logger.info(center("Unable to detect system architecture!!"))
        logger.info(pretext())
        exit(1)
    return architecture


def confirmation_prompt() -> None | NoReturn:
    """Prompts a confirmation from the user to continue or exit."""
    try:
        prompt = input("Are you sure you want to continue? <Y/N> ")
    except KeyboardInterrupt:
        prompt = "N"
        print()
    if not re.match(r"^[yY](es)?$", prompt):
        logger.info(pretext())
        logger.info("Bye. Hope to see you soon.")
        logger.info(pretext())
        exit(0)


class Env:
    """Custom configuration variables, passed on to shell scripts as env vars.

    >>> Env

    """

    def __init__(self):
        """Instantiates the required members."""
        self.osname: str = platform.system().lower()
        self.architecture: str = get_arch()
        self.pyversion: str = f"{sys.version_info.major}{sys.version_info.minor}"
        self.current_dir: os.PathLike | str = os.path.dirname(__file__)
        self.exec: os.PathLike | str = sys.executable

    def install_uv(self) -> None | NoReturn:
        """Installs ``uv`` package manager."""
        run_subprocess(f"{env.exec} -m pip install uv")
        self.exec = shutil.which("uv")
        try:
            installer = sys.argv[0].split(os.path.sep)[-1]
        except Exception as err:
            logger.warning(err)
            installer = "jarvis"
        assert (
            self.exec
        ), f"\n\tFailed to install package manager. Try to rerun '{installer} {sys.argv[1]}'"


env = Env()
env_vars = {key: value for key, value in env.__dict__.items()}


def run_subprocess(command: str) -> None:
    """Run shell commands/scripts as subprocess including system environment variables.

    See Also:
        - 0 → success.
        - non-zero → failure.

    **Exit Codes**:
        - 1 → indicates a general failure.
        - 2 → indicates incorrect use of shell builtins.
        - 3-124 → indicate some error in job (check software exit codes)
        - 125 → indicates out of memory.
        - 126 → indicates command cannot execute.
        - 127 → indicates command not found
        - 128 → indicates invalid argument to exit
        - 129-192 → indicate jobs terminated by Linux signals
            - For these, subtract 128 from the number and match to signal code
            - Enter kill -l to list signal codes
            - Enter man signal for more information
    """
    process = subprocess.Popen(
        command,
        text=True,
        shell=True,
        env={k: v for k, v in {**os.environ, **env_vars}.items() if k and v},
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        for line in process.stdout:
            logger.info(line.strip())
        process.wait()
        for line in process.stderr:
            logger.error(line.strip())
        assert (
            process.returncode == 0
        ), f"{command!r} returned exit code {process.returncode}"
    except KeyboardInterrupt:
        if process.poll() is None:
            for line in process.stdout:
                logger.info(line.strip())
            process.terminate()


def windows_handler() -> None | NoReturn:
    """Function to handle installations on Windows operating systems."""
    logger.info(
        """
Make sure Git, Anaconda (or Miniconda) and VS C++ BuildTools are installed.
Refer the below links for:
    * Anaconda installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/
    * Miniconda installation: https://docs.conda.io/en/latest/miniconda.html#windows-installers
    * VisualStudio C++ BuildTools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    * Git: https://git-scm.com/download/win/
"""
    )
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    confirmation_prompt()


def untested_os() -> None | NoReturn:
    """Function to handle unsupported operating systems."""
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    logger.warning(f"Current Operating System: {env.osname}")
    logger.warning("Jarvis has currently been tested only on Linux, macOS and Windows")
    logger.warning(
        center("Please note that you might need to install additional dependencies.")
    )
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    confirmation_prompt()


def untested_arch() -> None | NoReturn:
    """Function to handle unsupported architecture."""
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    logger.warning(center(f"Current Architecture: {env.architecture}"))
    logger.warning(
        center("Jarvis has currently been tested only on AMD and ARM64 machines.")
    )
    logger.warning(
        center("Please note that you might need to install additional dependencies.")
    )
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    confirmation_prompt()


def no_venv() -> None | NoReturn:
    """Function to handle installations that are NOT on virtual environments."""
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    logger.info(
        center(
            """
Using a virtual environment is highly recommended to avoid version conflicts in dependencies
    * Creating Virtual Environments: https://docs.python.org/3/library/venv.html#creating-virtual-environments
    * How Virtual Environments work: https://docs.python.org/3/library/venv.html#how-venvs-work
    * Set UV_INSTALL=0, since uv package manager cannot be used for a system interpreter.
"""
        )
    )
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    confirmation_prompt()
    uv_install["option"] = False


class Requirements:
    """Install locations for pinned, locked and upgrade-able packages.

    >>> Requirements

    """

    def __init__(self):
        """Instantiates the file paths for pinned, locked and upgrade-able requirements."""
        self.pinned: str = os.path.join(
            env.current_dir, "version_pinned_requirements.txt"
        )
        self.locked: str = os.path.join(
            env.current_dir, "version_locked_requirements.txt"
        )
        self.upgrade: str = os.path.join(
            env.current_dir, "version_upgrade_requirements.txt"
        )


requirements = Requirements()


def os_specific_pip() -> List[str]:
    """Returns a list of pip installed packages."""
    src = [
        "dlib",
        "playsound",
        "pvporcupine",
        "opencv-python",
        "face-recognition",
    ]
    if env.osname == "windows":
        return src + ["pydub", "pywin32"]
    if env.osname == "linux":
        return src + ["gobject", "PyGObject"]
    if env.osname == "darwin":
        return src + ["ftransc", "pyobjc-framework-CoreWLAN"]


def thread_worker(commands: List[str]) -> bool:
    """Thread worker that runs subprocess commands in parallel.

    Args:
        commands: List of commands to be executed simultaneously.

    Returns:
        bool:
        Returns a boolean flag to indicate if there was a failure.
    """
    futures = {}
    with ThreadPoolExecutor(max_workers=len(commands)) as executor:
        for iterator in commands:
            future = executor.submit(run_subprocess, iterator)
            futures[future] = iterator
    failed = False
    for future in as_completed(futures):
        if future.exception():
            failed = True
            logger.error(
                f"Thread processing for {futures[future]!r} received an exception: {future.exception()!r}"
            )
    return failed


def dev_uninstall() -> None:
    """Uninstalls all the dev packages installed from pypi repository."""
    init()
    logger.info(pretext())
    logger.info(center("Uninstalling dev dependencies"))
    logger.info(pretext())
    with Runtime() as runtime:
        run_subprocess(
            f"{env.exec} pip uninstall{verbose} --no-cache-dir sphinx==5.1.1 pre-commit recommonmark gitverse"
        )
    logger.info(pretext())
    logger.info(center(f"Cleanup completed in {runtime.get()}!"))
    logger.info(pretext())


def main_uninstall() -> None:
    """Uninstalls all the main packages installed from pypi repository."""
    init()
    logger.info(pretext())
    logger.info(center("Uninstalling ALL dependencies"))
    logger.info(pretext())
    with Runtime() as runtime:
        exception = thread_worker(
            [
                f"{env.exec} pip uninstall{verbose} --no-cache-dir -r {requirements.pinned}",
                f"{env.exec} pip uninstall{verbose} --no-cache-dir -r {requirements.locked}",
                f"{env.exec} pip uninstall{verbose} --no-cache-dir -r {requirements.upgrade}",
                f"{env.exec} pip uninstall{verbose} --no-cache-dir {' '.join(os_specific_pip())}",
            ]
        )
    logger.info(pretext())
    if exception:
        logger.error(center("One or more cleanup threads have failed!!"))
    else:
        logger.info(center(f"Cleanup completed in {runtime.get()}!"))
    logger.info(pretext())


def os_agnostic() -> None:
    """Function to handle os-agnostic installations."""
    logger.info(pretext())
    logger.info(center("Installing OS agnostic dependencies"))
    logger.info(pretext())
    with Runtime() as runtime:
        exception = thread_worker(
            [
                f"{env.exec} pip install{verbose} --no-cache -r {requirements.pinned}",
                f"{env.exec} pip install{verbose} --no-cache -r {requirements.locked}",
                f"{env.exec} pip install{verbose} --no-cache --upgrade -r {requirements.upgrade}",
            ]
        )
    logger.info(pretext())
    if exception:
        logger.error(center("One or more installation threads have failed!!"))
        logger.error(
            center("Please set JARVIS_VERBOSITY=1 and retry to identify root cause.")
        )
    else:
        logger.info(center(f"Installation completed in {runtime.get()}"))
    logger.info(pretext())


def init() -> None:
    """Runs pre-flight validations and upgrades ``setuptools`` and ``wheel`` packages."""
    if env.osname not in ("darwin", "windows", "linux"):
        untested_os()

    if env.architecture not in ("amd64", "arm64"):
        untested_arch()

    if sys.prefix == sys.base_prefix:
        no_venv()

    pyversion: str = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info.major == 3 and sys.version_info.minor in (10, 11):
        logger.info(pretext())
        logger.info(
            center(f"{env.osname}-{env.architecture} running python {pyversion}")
        )
        logger.info(pretext())
    else:
        logger.warning(
            f"Python version {pyversion} is unsupported for Jarvis. "
            "Please use any python version between 3.10.* and 3.11.*"
        )
        exit(1)
    if uv_install["option"]:
        env.install_uv()
    else:
        env.exec += " -m"
    # fixme: Pinned version of setuptools to avoid deprecation warning due to import pkg_resources in dlib
    #   Future plan is to replace face recognition script with docker container (enable remote evaluation)
    run_subprocess(f"{env.exec} pip install{verbose} setuptools==76.0.0")
    run_subprocess(f"{env.exec} pip install{verbose} --upgrade pip wheel")


def dev_install() -> None:
    """Install dev dependencies."""
    init()
    logger.info(pretext())
    logger.info(center("Installing dev dependencies"))
    logger.info(pretext())
    with Runtime() as runtime:
        run_subprocess(
            f"{env.exec} pip install{verbose} sphinx==5.1.1 pre-commit recommonmark gitverse"
        )
    logger.info(pretext())
    logger.info(center(f"Installation completed in {runtime.get()}"))
    logger.info(pretext())


def main_install() -> None:
    """Install main dependencies."""
    init()
    install_script = os.path.join(env.current_dir, f"install_{env.osname}.sh")
    logger.info(pretext())
    logger.info(
        center(f"Installing dependencies specific to {string.capwords(env.osname)}")
    )
    logger.info(pretext())
    if env.osname == "windows":
        windows_handler()
    os.environ["PY_EXECUTABLE"] = env.exec
    run_subprocess(install_script)
    os_agnostic()
