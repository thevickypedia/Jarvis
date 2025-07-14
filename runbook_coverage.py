import os
import pathlib
import sys
from collections.abc import Generator

root = pathlib.Path(__file__).parent

rst_file = root / "docs_gen" / "index.rst"
rst_text = rst_file.read_text()


class Format:
    """Initiates Format object to define variables that print the message in a certain format.

    >>> Format

    """

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ITALIC = "\x1B[3m"
    END = "\033[0m"


class Colors:
    """Initiates Colors object to define variables that print the message in a certain color.

    >>> Colors

    """

    VIOLET = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    LIGHT_GREEN = "\033[32m"
    LIGHT_YELLOW = "\033[2;33m"
    LIGHT_RED = "\033[31m"


EXCLUSIONS = [
    "__pycache__",
    "__init__.py",
    "version.py",
]


def get_missing(entrypoint: str) -> Generator[str]:
    """Get modules that are not documented in the index.rst file."""
    for src, dir__, files__ in os.walk(root / entrypoint):
        if any(src.endswith(exclusion) for exclusion in EXCLUSIONS):
            continue
        for file in files__:
            if file.endswith(".py") and file not in EXCLUSIONS:
                filepath = os.path.join(src, file).split(entrypoint, 1)[1]
                module = entrypoint + filepath.replace(".py", "").replace(
                    os.path.sep, "."
                )
                if module not in rst_text:
                    yield module


def main(entrypoint: str) -> None:
    """Main function to run the script."""
    if missing := list(get_missing(entrypoint)):
        msg = "The following modules are missing from the rubook:"
        print(f"{Colors.RED}{Format.BOLD}ERROR:{'':<2}{msg}{Colors.END}\n")
        for module in missing:
            print(f"\t• {Format.BOLD}{Format.ITALIC}{module}{Format.END}")
        msg = f"Please add them to the {rst_file.__str__()!r}"
        print(f"\n{Colors.YELLOW}{Format.ITALIC}{msg}{Colors.END}\n")
        exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
