import os
import platform
import re
import string
import subprocess
import sys
from typing import NoReturn


def pretext() -> str:
    """Pre-text to gain reader's attention in the terminal."""
    return "".join(["*" for _ in range(os.get_terminal_size().columns)])


class Env:
    """Custom configuration variables, passed on to shell scripts as env vars.

    >>> Env

    """

    def __init__(self):
        """Instantiates the required members."""
        self.osname: str = platform.system().lower()
        self.architecture: str = platform.machine().lower()
        self.pyversion: str = f"{sys.version_info.major}{sys.version_info.minor}"
        self.current_dir: str = os.path.dirname(__file__)


env = Env()
env_vars = {key: value for key, value in env.__dict__.items()}


def run_subprocess(command: str) -> None:
    """Run shell commands/scripts as subprocess.

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
            print(line.strip())
        process.wait()
        for line in process.stderr:
            print(line.strip())
        assert (
            process.returncode == 0
        ), f"{command!r} returned exit code {process.returncode}"
    except KeyboardInterrupt:
        if process.poll() is None:
            for line in process.stdout:
                print(line.strip())
            process.terminate()


def center(text: str) -> None:
    """Aligns text to center of the terminal."""
    print(text.center(os.get_terminal_size().columns))


def windows_caveat() -> None | NoReturn:
    """Function to handle installations on Windows operating systems."""
    print(
        """
Make sure Git, Anaconda (or Miniconda) and VS C++ BuildTools are installed.
Refer the below links for:
    * Anaconda installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/
    * Miniconda installation: https://docs.conda.io/en/latest/miniconda.html#windows-installers
    * VisualStudio C++ BuildTools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    * Git: https://git-scm.com/download/win/
"""
    )
    print(pretext())
    print(pretext())
    prompt = input("Are you sure you want to continue? <Y/N> ")
    if not re.match(r"^[yY](es)?$", prompt):
        print()
        print(pretext())
        print("Bye. Hope to see you soon.")
        print(pretext())
        exit(0)


def unsupported_os() -> NoReturn:
    """Function to handle unsupported operating systems."""
    print(f"\n{pretext()}\n{pretext()}\n")
    print(f"Current Operating System: {env.osname}")
    print("Jarvis is currently supported only on Linux, MacOS and Windows")
    print(f"\n{pretext()}\n{pretext()}\n")
    exit(1)


def os_agnostic() -> None:
    """Function to handle os-agnostic installations."""
    print(pretext())
    center("Installing OS agnostic dependencies")
    print(pretext())
    run_subprocess(
        f"python -m pip install --no-cache -r {env.current_dir}/version_pinned_requirements.txt"
    )
    run_subprocess(
        f"python -m pip install --no-cache -r {env.current_dir}/version_locked_requirements.txt"
    )
    run_subprocess(
        f"python -m pip install --no-cache --upgrade -r {env.current_dir}/version_upgrade_requirements.txt"
    )


def init() -> None:
    """Runs pre-flight validations and upgrades ``setuptools`` and ``wheel`` packages."""
    if env.osname not in ("darwin", "windows", "linux"):
        unsupported_os()

    pyversion: str = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info.major == 3 and sys.version_info.minor in (10, 11):
        print(pretext())
        center(f"{env.osname}-{env.architecture} running python {pyversion}")
        print(pretext())
    else:
        print(
            f"Python version {pyversion} is unsupported for Jarvis. "
            "Please use any python version between 3.10.* and 3.11.*"
        )
        exit(1)
    run_subprocess("python -m pip install --upgrade pip setuptools wheel")


def dev() -> None:
    """Install dev dependencies."""
    init()
    print(pretext())
    center("Installing dev dependencies")
    print(pretext())
    run_subprocess(
        "python -m pip install sphinx==5.1.1 pre-commit recommonmark gitverse"
    )


def main() -> None:
    """Install main dependencies."""
    # todo: include support for raspberry-pi
    # todo: possible arch (arm11, cortex-a7, cortex-a53, cortex-53-aarch64, cortex-a72, cortex-a72-aarch64)
    init()
    install_script = os.path.join(env.current_dir, f"install_{env.osname}.sh")

    print(pretext())
    center(f"Installing dependencies specific to {string.capwords(env.osname)}")
    print(pretext())

    if env.osname == "windows":
        windows_caveat()
    run_subprocess(install_script)
    os_agnostic()
