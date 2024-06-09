r"""Snippet to get the lines of code for Jarvis.

Following shell command is a simple one-liner replicating this snippet.

Notes:
    ``find .`` (dot) can be replaced with the base directory to start the scan from.

.. code-block:: shell

    find . \( -path './venv' -o -path './docs' -o -path './docs_gen' \) \
        -prune -o \( -name '*.py' -o -name '*.sh' -o -name '*.html' \) \
        -print | xargs wc -l | grep total
"""

import os
from collections.abc import Generator
from typing import List

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, DirectoryPath, FilePath, PositiveInt

from jarvis.api.logger import logger
from jarvis.modules.cache import cache

router = APIRouter()


class Customizations(BaseModel):
    """Custom exlusitions and inclusions for the scan.

    >>> Customizations

    """

    excluded_dirs: List[str] = ["./venv", "./docs", "./docs_gen", "./logs"]
    file_extensions: List[str] = [".py", ".sh", ".html"]


custom = Customizations()


def should_include(filepath: FilePath) -> bool:
    """Check if the file has one of the desired extensions and if the directory is excluded.

    Args:
        filepath: File path for which the exclusion status is needed.

    Returns:
        bool:
        Boolean flag to indicate whether the file has to be included.
    """
    if not any(filepath.endswith(ext) for ext in custom.file_extensions):
        return False
    # Check if the file is in one of the excluded directories
    for excluded_dir in custom.excluded_dirs:
        if os.path.commonpath([filepath, excluded_dir]) == excluded_dir:
            return False
    return True


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


def get_files(base_path: DirectoryPath) -> Generator[FilePath]:
    """Walk through the directory and collect all relevant files.

    Args:
        base_path: Base path to start scan from.

    Yields:
        Yields the file path.
    """
    for root, dirs, files in os.walk(base_path):
        # Modify dirs in place to skip the excluded directories
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in custom.excluded_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            if should_include(file_path):
                yield file_path


@cache.timed_cache(max_age=900)  # Cache for 15 minutes
def total_lines_of_code(base_dir: DirectoryPath) -> PositiveInt:
    """Cached function to calculate the total lines of code.

    Args:
        base_dir: Base directory to start the scan from.

    Returns:
        PositiveInt:
        Total lines of code in all files within the base directory.
    """
    logger.info("Calculating total lines of code.")
    return sum(count_lines(file) for file in get_files(base_dir))


@cache.timed_cache(max_age=900)  # Cache for 15 minutes
def total_files(base_dir: DirectoryPath) -> PositiveInt:
    """Cached function to calculate the total number of files.

    Args:
        base_dir: Base directory to start the scan from.

    Returns:
        PositiveInt:
        Total files within the base directory.
    """
    logger.info("Calculating total lines of code.")
    return len(list(get_files(base_dir)))


@router.get(path="/line-count", include_in_schema=True)
async def line_count(redirect: bool = True, base_dir: DirectoryPath = "jarvis"):
    """Get total lines of code for Jarvis.

    Args:

        redirect: Boolean flag to return a redirect response on-demand.
        base_dir: Base directory to start the scan from.

    Returns:

        RedirectResponse:
        Returns the response from img.shields.io or an integer with total count based on the ``redirect`` argument.
    """
    total_lines = total_lines_of_code(base_dir)
    # todo: Get GitHub repo and owner name, make this an open-source (use Redis or other caching mechanism)
    logger.info("Total lines of code: %d", total_lines)
    if redirect:
        return RedirectResponse(
            f"https://img.shields.io/badge/lines%20of%20code-{total_lines:,}-blue"
        )
    return total_lines


@router.get(path="/file-count", include_in_schema=True)
async def file_count(redirect: bool = True, base_dir: DirectoryPath = "jarvis"):
    """Get total number of files for Jarvis.

    Args:

        redirect: Boolean flag to return a redirect response on-demand.
        base_dir: Base directory to start the scan from.

    Returns:

        RedirectResponse:
        Returns the response from img.shields.io or an integer with total count based on the ``redirect`` argument.
    """
    files = total_files(base_dir)
    # todo: Get GitHub repo and owner name, make this an open-source (use Redis or other caching mechanism)
    logger.info("Total number of files: %d", files)
    if redirect:
        return RedirectResponse(
            f"https://img.shields.io/badge/total%20files-{files:,}-blue"
        )
    return files
