r"""Snippet to get the lines of code and total number of files for Jarvis.

Following shell command is a simple one-liner replicating this snippet.

Notes:
    ``find .`` (dot) can be replaced with the base directory to start the scan from.

.. code-block:: shell

    find . \( -path './venv' -o -path './docs' -o -path './docs_gen' \) \
        -prune -o \( -name '*.py' -o -name '*.sh' -o -name '*.html' \) \
        -print | xargs wc -l | grep total
"""

import os
import sys
import urllib.parse
from collections.abc import Generator
from typing import List

from fastapi.responses import RedirectResponse
from pydantic import FilePath, PositiveInt

import jarvis
from jarvis.api.logger import logger
from jarvis.modules.cache import cache

if sys.version_info.minor > 10:
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Override for python 3.10 due to lack of StrEnum."""


FILE_EXTENSIONS: List[str] = [".html", ".py", ".scpt", ".sh", ".xml"]


class ValidColors(StrEnum):
    """Valid colors for badges in img.shields.io.

    >>> ValidColors

    **Source:**
        https://github.com/badges/buckler/blob/master/README.md#valid-colours
    """

    brightgreen = "brightgreen"
    green = "green"
    yellowgreen = "yellowgreen"
    yellow = "yellow"
    orange = "orange"
    red = "red"
    grey = "grey"
    gray = "grey"
    lightgrey = "lightgrey"
    lightgray = "lightgray"
    blue = "blue"


def should_include(filepath: FilePath) -> bool:
    """Check if the file has one of the desired extensions and if the directory is excluded.

    Args:
        filepath: File path for which the exclusion status is needed.

    Returns:
        bool:
        Boolean flag to indicate whether the file has to be included.
    """
    return any(filepath.endswith(ext) for ext in FILE_EXTENSIONS)


def count_lines(filepath: FilePath) -> PositiveInt:
    """Opens a file and counts the number of lines in it.

    Args:
        filepath: File path to get the line count from.

    Returns:
        PositiveInt:
        Returns the number of lines in the file.
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        return sum(1 for _ in file)


def get_files() -> Generator[str]:
    """Walk through the directory and collect all relevant files.

    Yields:
        Yields the file path.
    """
    for root, dirs, files in os.walk(jarvis.__path__[0]):
        for file in files:
            file_path = os.path.join(root, file)
            if should_include(file_path):
                yield file_path


@cache.timed_cache(max_age=900)
def total_lines_of_code() -> PositiveInt:
    """Cached function to calculate the total lines of code.

    Returns:
        PositiveInt:
        Total lines of code in all files within the base directory.
    """
    logger.info("Calculating total lines of code.")
    return sum(count_lines(file) for file in get_files())


@cache.timed_cache(max_age=900)
def total_files() -> PositiveInt:
    """Cached function to calculate the total number of files.

    Returns:
        PositiveInt:
        Total files within the base directory.
    """
    logger.info("Calculating total number of files.")
    return len(list(get_files()))


async def line_count(
    badge: bool = False,
    color: ValidColors = ValidColors.blue,
    text: str = "lines of code",
):
    """Get total lines of code for Jarvis.

    Args:
        badge: Boolean flag to return a badge from ``img.shields.io`` as HTML.
        color: Color for the badge.
        text: Text to be displayed in the badge.

    Returns:

        RedirectResponse:
        Returns a badge from ``img.shields.io`` or an integer with total count based on the ``badge`` argument.
    """
    total_lines = total_lines_of_code()
    logger.info("Total lines of code: %d", total_lines)
    if badge:
        return RedirectResponse(
            f"https://img.shields.io/badge/{urllib.parse.quote(text)}-{total_lines:,}-{color}"
        )
    return total_lines


async def file_count(
    badge: bool = False,
    color: ValidColors = ValidColors.blue,
    text: str = "total files",
):
    """Get total number of files for Jarvis.

    Args:
        badge: Boolean flag to return a badge from ``img.shields.io`` as HTML.
        color: Color for the badge.
        text: Text to be displayed in the badge.


    Returns:

        RedirectResponse:
        Returns a badge from ``img.shields.io`` or an integer with total count based on the ``badge`` argument.
    """
    files = total_files()
    logger.info("Total number of files: %d", files)
    if badge:
        return RedirectResponse(
            f"https://img.shields.io/badge/{urllib.parse.quote(text)}-{files:,}-{color}"
        )
    return files
