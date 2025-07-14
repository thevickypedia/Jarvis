import os
import sys
from multiprocessing import current_process
from typing import Callable

version = "7.1.1.post1"


def __preflight_check__() -> Callable:
    """Startup validator that imports Jarvis' main module to validate all dependencies' installation status.

    Returns:
        Callable:
        Returns the ``start`` function.
    """
    try:
        import pynotification  # noqa: F401

        from ._preexec import keywords_handler  # noqa: F401
        from .main import start  # noqa: F401
    except ImportError:
        try:
            # noinspection PyUnboundLocalVariable
            pynotification.pynotifier(
                title="First time user?",
                dialog=True,
                message="Please run\n\njarvis install",
            )
        except NameError:
            pass
        raise UserWarning("Missing dependencies!\n\nPlease run\n\tjarvis install")
    return start


def start() -> None:
    """Start function to invoke Jarvis programmatically."""
    init = __preflight_check__()
    init()


def commandline() -> None:
    """Starter function to invoke Jarvis using commandline."""
    # This is to validate that only 'jarvis' command triggers this function and not invoked by other functions
    assert sys.argv[0].endswith("jarvis"), "Invalid commandline trigger!!"
    options = {
        "install": "Installs the main dependencies.",
        "dev-install": "Installs the dev dependencies.",
        "start | run": "Initiates Jarvis.",
        "uninstall": "Uninstall the main dependencies",
        "dev-uninstall": "Uninstall the dev dependencies",
        "--version | -v": "Prints the version.",
        "--help | -h": "Prints the help section.",
    }
    # weird way to increase spacing to keep all values monotonic
    _longest_key = len(max(options.keys()))
    _pretext = "\n\t* "
    choices = _pretext + _pretext.join(
        f"{k} {'·' * (_longest_key - len(k) + 8)}→ {v}".expandtabs()
        for k, v in options.items()
    )
    try:
        arg = sys.argv[1].lower()
    except (IndexError, AttributeError):
        print(
            f"Cannot proceed without arbitrary commands. Please choose from {choices}"
        )
        exit(1)
    from jarvis.lib import installer

    match arg:
        case "install":
            installer.main_install()
        case "dev-install":
            installer.dev_install()
        case "uninstall":
            installer.main_uninstall()
        case "dev-uninstall":
            installer.dev_uninstall()
        case "start" | "run":
            os.environ["debug"] = str(os.environ.get("JARVIS_VERBOSITY", "-1") == "1")
            init = __preflight_check__()
            init()
        case "version" | "-v" | "--version":
            print(f"Jarvis {version}")
        case "help" | "-h" | "--help":
            print(
                f"Usage: jarvis [arbitrary-command]\nOptions (and corresponding behavior):{choices}"
            )
        case _:
            print(f"Unknown Option: {arg}\nArbitrary commands must be one of {choices}")


# MainProcess has specific conditions to land at 'start' or 'commandline'
# __preflight_check__ still needs to be loaded for all other child processes
if current_process().name == "MainProcess":
    current_process().name = os.environ.get("PROCESS_NAME", "JARVIS")
else:
    __preflight_check__()
