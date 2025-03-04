import json
import logging
import os.path
import pathlib
import re
import sys
import time
import urllib.request
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from typing import Any, Callable, Dict, Iterable, List
from urllib.error import HTTPError

from display import echo
from version import Version

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    fmt=logging.Formatter(
        datefmt="%b-%d-%Y %I:%M:%S %p",
        fmt="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
    )
)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


@dataclass
class PackageInfo(dict):
    """Dataclass for package information."""

    filepath: str
    package_name: str
    current_version: str
    latest_version: str = None


def get_latest_version(package_name, retries=5) -> str:
    """Get latest version of a package from pypi repository.

    Args:
        package_name: Name of the package.
        retries: Number of retries to attempt.

    Returns:
        str:
        Returns a string indicating the version.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    attempt = 0
    while attempt < retries:
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode()
                package_info = json.loads(data)
                latest_version = package_info["info"]["version"]
                return latest_version
        except HTTPError as error:
            if error.code == 429:
                attempt += 1
                # Exponential backoff (1, 2, 4, 8, 16 seconds)
                delay = 2**attempt
                logger.warning(
                    f"Throttled: Retrying '{package_name}'... Attempt {attempt}/{retries}. Waiting {delay} seconds."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"HTTPError {error.code}: Could not retrieve {package_name!r}"
                )
                return f"Error: {error.code}"
        except Exception as error:
            logger.error(error)
            return f"Error: {type(error).__name__}"
    logger.error(f"Max retries exceeded for {package_name!r}")
    return "Error: Max retries exceeded"


def get_package_and_version(
    input_string: str,
) -> Dict[str, str | None] | None:
    """Parses a package specified in the requirements file to retrieve package name and version.

    Args:
        input_string: Input line from the requirements file.

    Returns:
        Dict[str, str | None]:
        Returns key-value pairs with package name and version.
    """
    if not input_string or input_string.startswith("#"):
        return None
    # Define the pattern for splitting at special characters and capturing the version
    pattern = r"([=<>#@])"
    split_result = re.split(pattern, input_string, maxsplit=1)
    # Now extract the version from the remaining part of the string
    # noinspection RegExpUnnecessaryNonCapturingGroup,RegExpRedundantEscape,RegExpSimplifiable
    version_match = re.search(r"[\d]+\.[\d]+(?:\.[\d]+)?(?:[\.\*]*)", input_string)
    version = version_match.group(0) if version_match else None
    return dict(package_name=split_result[0].strip(), current_version=version)


def read_requirements(
    filepath: str,
) -> Generator[Dict[str, str | None]]:
    """Reads the requirements file and yields the package information.

    Args:
        filepath: Takes the filepath as an argument.

    Yields:
        Dict[str, str | None]:
        Returns key-value pairs with package name and version.
    """
    with open(filepath) as file:
        for requirement in file.readlines():
            if package := get_package_and_version(requirement.strip()):
                package["filepath"] = filepath
                yield package


def thread_worker(
    function_to_call: Callable,
    iterable: List | Iterable | Generator,
    workers: int = os.cpu_count(),
) -> Generator[Any]:
    """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

    Args:
        function_to_call: Takes the function/method that has to be called as an argument.
        iterable: List or iterable to be used as args.
        workers: Maximum number of workers to spin up.

    Yields:
        Any:
        Yields the response from the function as it is the executed.
    """
    logger.info("Running '%s' with %d workers", function_to_call.__name__, workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(function_to_call, item): item for item in iterable}
        for future in as_completed(futures):
            try:
                result = future.result()
                if isinstance(result, Generator):
                    yield from result
                else:
                    yield result
            except Exception as error:
                logger.error(
                    "Thread processing for %s received an exception: %s",
                    futures[future],
                    error,
                )


def get_version(package: Dict[str, str]) -> PackageInfo:
    """Get version information of a package.

    Args:
        package: Package information as key-value pairs.

    Returns:
        PackageInfo:
        Returns the final PackageInfo object.
    """
    return PackageInfo(
        **package, latest_version=get_latest_version(package["package_name"])
    )


def write_gh_summary(filepath: str, text: str) -> None:
    """Writes output to GitHub step summary.

    Args:
        filepath: GitHub summary filepath.
        text: Text to write to summary.
    """
    with open(filepath, "a") as file:
        file.write("```")
        file.write(text)
        file.write("```")
        file.write("\n")
        file.flush()


def entrypoint():
    """Entrypoint function to read all the requirements file and callout packages that are outdated."""
    root_dir = pathlib.Path(__file__).parent.parent
    base_dir = os.path.join(root_dir, "jarvis", "lib")
    gha = os.getenv("GITHUB_ACTIONS") == "true"
    gha_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    requirement_files = [
        os.path.join(base_dir, file)
        for file in os.listdir(base_dir)
        if file.endswith(".txt")
    ]
    requirements: Generator[Dict[str, str]] = thread_worker(
        read_requirements, requirement_files
    )
    versioned_requirements: Generator[PackageInfo] = thread_worker(
        get_version, requirements
    )

    for versioned in versioned_requirements:
        if gha and not versioned.current_version:
            # Since the requirements will not be installed in GHA
            continue
        elif not versioned.current_version:
            # Check locally installed version in case it's missing in requirements.txt
            try:
                version = distribution(versioned.package_name)
            except PackageNotFoundError:
                continue
            versioned.current_version = version.version
        if versioned.current_version.endswith("*"):
            current_version = versioned.current_version.rstrip(".*")
            latest_version = ".".join(versioned.latest_version.split(".")[:-1])
        else:
            current_version = versioned.current_version
            latest_version = versioned.latest_version
        if Version(latest_version) > Version(current_version):
            version_dict = versioned.__dict__
            version_dict.pop("filepath", 1)
            if gha:
                write_gh_summary(gha_summary, json.dumps(version_dict, indent=4))
                print(f"::warning title=Outdated Version::{version_dict}", file=sys.stderr)
            else:
                echo.warning(json.dumps(version_dict, indent=4))


if __name__ == "__main__":
    entrypoint()
