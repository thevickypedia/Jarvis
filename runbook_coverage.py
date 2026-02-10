import os
import pathlib
import re
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
    "exceptions.py",
    "version.py",
]


def inheritance(filepath: str, module: str) -> Generator[str]:
    """Check for inheritance."""
    with open(filepath) as file:
        lines = file.readlines()
    for line in lines:
        if line.startswith("class") and "(" in line and ")" in line:
            if match := re.search(r"class\s+(\w+)", line.strip()):
                class_name = match.group(1)
                autoclass = module + "." + class_name
                if autoclass not in rst_text:
                    yield autoclass


def get_missing(entrypoint: str) -> Generator[str]:
    """Get modules that are not documented in the index.rst file."""
    for src, dir__, files__ in os.walk(root / entrypoint):
        if any(src.endswith(exclusion) for exclusion in EXCLUSIONS):
            continue
        for file in files__:
            if file.endswith(".py") and file not in EXCLUSIONS:
                src_file = os.path.join(src, file)
                filepath = src_file.split(entrypoint, 1)[1]
                automodule = entrypoint + filepath.replace(".py", "").replace(os.path.sep, ".")
                yield from inheritance(src_file, automodule)
                if automodule not in rst_text:
                    yield automodule


def check_autodoc() -> Generator[str]:
    """Check if autoclass is documented in the index.rst file."""
    for line in rst_text.splitlines():
        if "autoclass" in line and "(" not in line:
            yield line
        if "automodule" in line and "(" in line:
            yield line


def main(entrypoint: str) -> None:
    """Main function to run the script."""
    if invalid := list(check_autodoc()):
        msg = "The following modules are misconfigured::"
        print(f"{Colors.RED}{Format.BOLD}ERROR:{'':<2}{msg}{Colors.END}\n")
        for module in invalid:
            print(f"\t• {Format.BOLD}{Format.ITALIC}{module}{Format.END}")
        msg = f"Please fix them in {rst_file.__str__()!r}"
        print(f"\n{Colors.YELLOW}{Format.ITALIC}{msg}{Colors.END}\n")
        exit(1)
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
