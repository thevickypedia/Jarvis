import logging
import os
import pathlib
import re
import shutil
import subprocess
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Process, current_process
from typing import List, Tuple, Union

import requests
from pydantic import HttpUrl

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')  # noqa: RegExpRedundantEscape
FOOTNOTE_LINK_TEXT_RE = re.compile(r'\[([^\]]+)\]\[(\d+)\]')  # noqa: RegExpRedundantEscape
FOOTNOTE_LINK_URL_RE = re.compile(r'\[(\d+)\]:\s+(\S+)')  # noqa: RegExpRedundantEscape
ANCHORED_LINK_RE = re.compile(r'\[([^\]]+)\]:\s+(\S+)')  # noqa: RegExpRedundantEscape
SESSION = requests.Session()


def find_md_links(markdown: str) -> Generator[Tuple[str, HttpUrl]]:
    """Return list of dict with links in markdown.

    Args:
        markdown: Data from markdown file.

    Yields:
        Tuple of the string and the associated URL.
    """
    yield from list(INLINE_LINK_RE.findall(markdown))
    yield from list(ANCHORED_LINK_RE.findall(markdown))
    footnote_links = dict(FOOTNOTE_LINK_TEXT_RE.findall(markdown))
    footnote_urls = dict(FOOTNOTE_LINK_URL_RE.findall(markdown))
    for key in footnote_links.keys():
        yield footnote_links[key], footnote_urls[footnote_links[key]]


def verify_url(hyperlink: Tuple[str, HttpUrl], timeout: Tuple[int, int] = (3, 3)):
    """Make a GET request the hyperlink for validation.

    Args:
        hyperlink: Takes a tuple of the name and URL.
        timeout: A tuple of connect timeout and read timeout.

    See Also:
        Retries once with a longer connect and read timeout in case of a timeout error.

    Raises:
        ValueError: When a particular hyperlink breaks.
    """
    text, url = hyperlink
    try:
        if SESSION.get(url, timeout=timeout).ok:
            return
    except requests.Timeout as error:
        logger.warning(error)
        # Retry with a longer timeout if URL times out with 3 second timeout
        return verify_url(hyperlink, (10, 10))
    except requests.RequestException:
        pass
    if "amazon" in url:
        logger.warning(f"[{current_process().name}] - {text!r} - {url!r} is broken")
    else:
        raise ValueError(f"[{current_process().name}] - {text!r} - {url!r} is broken")


def verify_hyperlinks_in_md(filename: str):
    """Get all hyperlinks in a markdown file and validate them in a pool of threads.

    Args:
        filename: Name of the markdown file to be validated.

    Raises:
        ValueError: When a particular thread fails.
    """
    current_process().name = pathlib.Path(filename).name
    with open(filename) as file:
        md_file = file.read()
    futures = {}
    with ThreadPoolExecutor() as executor:
        for iterator in find_md_links(md_file):
            # noinspection PyTypeChecker
            future = executor.submit(verify_url, iterator)
            futures[future] = iterator
    try:
        file = current_process().name.split('.-')[1]
    except IndexError:
        file = current_process().name
    logger.info("Hyperlinks validated in '%s': %d", file, len(futures))
    for future in as_completed(futures):
        if future.exception():
            raise ValueError(future.exception())


def run_git_cmd(cmd: str) -> Union[str, List[str]]:
    """Run the git command.

    Returns:
        list:
        Returns the output of the git command split by lines.
    """
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode(encoding='UTF-8').strip()
    except (subprocess.CalledProcessError, subprocess.SubprocessError, Exception) as error:
        if isinstance(error, subprocess.CalledProcessError):
            result = error.output.decode(encoding='UTF-8').strip()
            logger.error(f"[{error.returncode}]: {result}")
        else:
            logger.error(error)


def check_all_md_files():
    """Downloads all the markdown files from wiki and initiates individual validation process for each markdown file."""
    wiki_path = "Jarvis.wiki"
    run_git_cmd(f"git clone https://github.com/thevickypedia/{wiki_path}.git")
    wiki_path = os.path.join(os.getcwd(), wiki_path)
    processes = [Process(target=verify_hyperlinks_in_md, args=("README.md",))]
    processes[0].start()
    if os.path.isdir(wiki_path):
        for file in os.listdir(wiki_path):
            if file.endswith(".md"):
                process = Process(target=verify_hyperlinks_in_md, args=(os.path.join(wiki_path, file),))
                process.start()
                processes.append(process)
    for process in processes:
        process.join()
    shutil.rmtree(wiki_path)


if __name__ == '__main__':
    check_all_md_files()
