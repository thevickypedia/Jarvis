import os
import sys
from multiprocessing import current_process
from typing import Callable

version = "5.0.0"

if current_process().name == "MainProcess":
    current_process().name = os.environ.get("PROCESS_NAME", "JARVIS")


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
    if sys.argv[0].endswith("jarvis"):
        choices = "\n\t* " + "\n\t* ".join(
            ("install", "dev-install", "start | run", "version | -v | --version | -V")
        )
        try:
            arg = sys.argv[1].lower()
        except (IndexError, AttributeError):
            print(
                f"Cannot proceed without arbitrary commands. Please choose from {choices}"
            )
            exit(1)
        match arg:
            case "install":
                from jarvis.lib import install  # noqa: F401

                install.main()
            case "dev-install":
                from jarvis.lib import install  # noqa: F401

                install.dev()
            case "start" | "run":
                init = __preflight_check__()
                init()
            case "version" | "-v" | "-V" | "--version":
                print(f"Jarvis {version}")
            case _:
                print(
                    f"Unknown Option: {arg}\nArbitrary commands must be one of {choices}"
                )
    else:
        __preflight_check__()
