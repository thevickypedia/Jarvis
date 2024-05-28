import os
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Iterable, List

import requests
import yaml
from bs4 import BeautifulSoup
from webull import webull

from jarvis.api.logger import logger
from jarvis.api.models import settings
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.models import models


def ticker_gatherer(character: str) -> None:
    """Gathers the stock ticker in NASDAQ. Runs on ``multi-threading`` which drops run time by ~7 times.

    Args:
        character: ASCII character (alphabet) with which the stock ticker name starts.
    """
    try:
        response = requests.get(
            url=f"https://www.eoddata.com/stocklist/NASDAQ/{character}.htm"
        )
    except EgressErrors as error:
        logger.error(error)
        return
    scrapped = BeautifulSoup(response.text, "html.parser")
    d1 = scrapped.find_all("tr", {"class": "ro"})
    d2 = scrapped.find_all("tr", {"class": "re"})
    for link in d1:
        td1 = link.findAll("td")
        settings.trader.stock_list[td1[0].text] = td1[1].text
    for link in d2:
        td2 = link.findAll("td")
        settings.trader.stock_list[td2[0].text] = td2[1].text


def thread_worker(
    function_to_call: Callable, iterable: List | Iterable, workers: int = None
) -> None:
    """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

    Args:
        function_to_call: Takes the function/method that has to be called as an argument.
        iterable: List or iterable to be used as args.
        workers: Maximum number of workers to spin up.
    """
    if not workers:
        workers = len(iterable)

    futures = {}
    executor = ThreadPoolExecutor(max_workers=workers)
    with executor:
        for iterator in iterable:
            future = executor.submit(function_to_call, iterator)
            futures[future] = iterator

    thread_except = 0
    for future in as_completed(futures):
        if future.exception():
            thread_except += 1
            logger.error(
                "Thread processing for %s received an exception: %s",
                futures[future],
                future.exception(),
            )
    # Use backup file if more than 10% of the requests fail
    if thread_except > (len(iterable) * 10 / 100):
        with open(models.fileio.stock_list_backup) as file:
            settings.trader.stock_list = yaml.load(stream=file, Loader=yaml.FullLoader)


def nasdaq() -> None:
    """Get all stock tickers available. Creates/Updates backup file to be used."""
    if os.path.isfile(models.fileio.stock_list_backup):
        modified = int(os.stat(models.fileio.stock_list_backup).st_mtime)
        # Gathers new stock list only if the file is older than a day
        if int(time.time()) - modified < 86_400:
            try:
                with open(models.fileio.stock_list_backup) as file:
                    settings.trader.stock_list = yaml.load(
                        stream=file, Loader=yaml.FullLoader
                    )
            except yaml.YAMLError as error:
                logger.error(error)
            if len(settings.trader.stock_list) > 2_000:  # Usually close to ~5K
                logger.info(
                    "%s generated with %d tickers on %s looks re-usable."
                    % (
                        models.fileio.stock_list_backup,
                        len(settings.trader.stock_list),
                        datetime.fromtimestamp(modified).strftime("%c"),
                    )
                )
                return
    logger.info("Gathering stock list from webull.")
    try:
        settings.trader.stock_list = [
            ticker.get("symbol") for ticker in webull().get_all_tickers()
        ]
    except Exception as error:
        logger.error(error)
    if settings.trader.stock_list:
        os.remove("did.bin") if os.path.isfile(
            "did.bin"
        ) else None  # Created by webull module
    else:
        logger.info("Gathering stock list from eoddata.")
        thread_worker(function_to_call=ticker_gatherer, iterable=string.ascii_uppercase)
    logger.info("Total tickers gathered: %d", len(settings.trader.stock_list))
    # Writes to a backup file
    with open(models.fileio.stock_list_backup, "w") as file:
        yaml.dump(stream=file, data=settings.trader.stock_list)
