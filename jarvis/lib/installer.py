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
import string
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, NoReturn

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def pretext() -> str:
    """Pre-text to gain reader's attention in the terminal."""
    return "".join(["*" for _ in range(os.get_terminal_size().columns)])


def center(text: str) -> str:
    """Aligns text to center of the terminal and returns it."""
    return text.center(os.get_terminal_size().columns)


def get_arch() -> str | NoReturn:
    """Classify system architecture into known categories.

    Returns:
        Returns exit code 1 if architecture is unknown.
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
    else:
        logger.info(pretext())
        logger.info(center(f"Unknown Architecture: {machine}"))
        logger.info(pretext())
        exit(1)
    return architecture


class Env:
    """Custom configuration variables, passed on to shell scripts as env vars.

    >>> Env

    """

    def __init__(self):
        """Instantiates the required members."""
        self.osname: str = platform.system().lower()
        self.architecture: str = get_arch()
        self.pyversion: str = f"{sys.version_info.major}{sys.version_info.minor}"
        self.current_dir: str = os.path.dirname(__file__)


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
        env={**os.environ, **env_vars},
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


def windows_caveat() -> None | NoReturn:
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
    logger.info(pretext())
    logger.info(pretext())
    prompt = input("Are you sure you want to continue? <Y/N> ")
    if not re.match(r"^[yY](es)?$", prompt):
        logger.info(pretext())
        logger.info("Bye. Hope to see you soon.")
        logger.info(pretext())
        exit(0)


def unsupported_os() -> NoReturn:
    """Function to handle unsupported operating systems.

    Returns:
        Returns exit code 1 if operating system is not either Linux, macOS or Windows.
    """
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    logger.warning(f"Current Operating System: {env.osname}")
    logger.warning("Jarvis is currently supported only on Linux, macOS and Windows")
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    exit(1)


def unsupported_arch() -> NoReturn:
    """Function to handle unsupported architecture.

    Returns:
        Returns exit code 1 if architecture is not AMD.
    """
    # todo: include support for raspberry-pi
    # todo: possible arch (arm11, cortex-a7, cortex-a53, cortex-53-aarch64, cortex-a72, cortex-a72-aarch64)
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    logger.warning(f"Current Architecture: {env.architecture}")
    logger.warning("Jarvis is currently supported only on AMD machines.")
    logger.warning(f"\n{pretext()}\n{pretext()}\n")
    exit(1)


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
    run_subprocess(
        "python -m pip uninstall --no-cache-dir sphinx==5.1.1 pre-commit recommonmark gitverse -y"
    )


def main_uninstall() -> None:
    """Uninstalls all the main packages installed from pypi repository."""
    init()
    logger.info(pretext())
    logger.info(center("Uninstalling ALL dependencies"))
    logger.info(pretext())
    exc = thread_worker(
        [
            f"python -m pip uninstall --no-cache-dir -r {requirements.pinned} -y",
            f"python -m pip uninstall --no-cache-dir -r {requirements.locked} -y",
            f"python -m pip uninstall --no-cache-dir -r {requirements.upgrade} -y",
            f"python -m pip uninstall --no-cache-dir {' '.join(os_specific_pip())} -y",
        ]
    )
    logger.info(pretext())
    logger.info(center("Cleanup has completed!")) if exc else logger.info(
        center("One or many cleanup threads have failed!!")
    )
    logger.info(pretext())


def os_agnostic() -> None:
    """Function to handle os-agnostic installations."""
    logger.info(pretext())
    logger.info(center("Installing OS agnostic dependencies"))
    logger.info(pretext())
    thread_worker(
        [
            f"python -m pip install --no-cache -r {requirements.pinned}",
            f"python -m pip install --no-cache -r {requirements.locked}",
            f"python -m pip install --no-cache --upgrade -r {requirements.upgrade}",
        ]
    )


def init() -> None:
    """Runs pre-flight validations and upgrades ``setuptools`` and ``wheel`` packages."""
    if env.osname not in ("darwin", "windows", "linux"):
        unsupported_os()

    if env.architecture != "amd64":
        unsupported_arch()

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
    run_subprocess("python -m pip install --upgrade pip setuptools wheel")


def dev_install() -> None:
    """Install dev dependencies."""
    init()
    logger.info(pretext())
    logger.info(center("Installing dev dependencies"))
    logger.info(pretext())
    run_subprocess(
        "python -m pip install sphinx==5.1.1 pre-commit recommonmark gitverse"
    )


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
        windows_caveat()
    run_subprocess(install_script)
    os_agnostic()
