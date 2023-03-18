import os
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Iterable, List, NoReturn, Optional, Tuple, Union

import requests
import yaml
from bs4 import BeautifulSoup
from pydantic import EmailStr
from webull import webull

from jarvis.api.modals.settings import stock_monitor
from jarvis.api.squire.logger import logger
from jarvis.modules.database import database
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.models import models

stock_db = database.Database(database=models.fileio.stock_db)


def ticker_gatherer(character: str) -> NoReturn:
    """Gathers the stock ticker in NASDAQ. Runs on ``multi-threading`` which drops run time by ~7 times.

    Args:
        character: ASCII character (alphabet) with which the stock ticker name starts.
    """
    try:
        response = requests.get(url=f'https://www.eoddata.com/stocklist/NASDAQ/{character}.htm')
    except EgressErrors as error:
        logger.error(error)
        return
    scrapped = BeautifulSoup(response.text, "html.parser")
    d1 = scrapped.find_all('tr', {'class': 'ro'})
    d2 = scrapped.find_all('tr', {'class': 're'})
    for link in d1:
        stock_monitor.stock_list.append(f"{(link.get('onclick').split('/')[-1]).split('.')[0]}")
    for link in d2:
        stock_monitor.stock_list.append(f"{(link.get('onclick').split('/')[-1]).split('.')[0]}")


def thread_worker(function_to_call: Callable, iterable: Union[List, Iterable], workers: int = None) -> NoReturn:
    """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

    Args:
        function_to_call: Takes the function/method that has to be called as an argument.
        iterable: List or iterable to be used as args.
        workers: Maximum number of workers to be spun up.
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
            logger.error("Thread processing for %s received an exception: %s", iterator, future.exception())
    if thread_except > (len(iterable) * 10 / 100):  # Use backup file if more than 10% of the requests fail
        with open(models.fileio.stock_list_backup) as file:
            stock_monitor.stock_list = yaml.load(stream=file, Loader=yaml.FullLoader)


def nasdaq() -> NoReturn:
    """Get all stock tickers available. Creates/Updates backup file to be used."""
    if os.path.isfile(models.fileio.stock_list_backup):
        modified = int(os.stat(models.fileio.stock_list_backup).st_mtime)
        if int(time.time()) - modified < 86_400:  # Gathers new stock list only if the file is older than a day
            try:
                with open(models.fileio.stock_list_backup) as file:
                    stock_monitor.stock_list = yaml.load(stream=file, Loader=yaml.FullLoader)
            except yaml.YAMLError as error:
                logger.error(error)
            if len(stock_monitor.stock_list) > 5_000:
                logger.info("%s generated on %s looks re-usable." %
                            (models.fileio.stock_list_backup, datetime.fromtimestamp(modified).strftime('%c')))
                return
    logger.info("Gathering stock list from webull.")
    try:
        stock_monitor.stock_list = [ticker.get('symbol') for ticker in webull().get_all_tickers()]
    except Exception as error:
        logger.error(error)
    if stock_monitor.stock_list:
        os.remove('did.bin') if os.path.isfile('did.bin') else None  # Created by webull module
    else:
        logger.info("Gathering stock list from eoddata.")
        thread_worker(function_to_call=ticker_gatherer, iterable=string.ascii_uppercase)
    logger.info("Total tickers gathered: %d", len(stock_monitor.stock_list))
    # Writes to a backup file
    with open(models.fileio.stock_list_backup, 'w') as file:
        yaml.dump(stream=file, data=stock_monitor.stock_list)


def cleanup_stock_userdata() -> NoReturn:
    """Delete duplicates tuples within the database."""
    data = get_stock_userdata()
    if dupes := [x for n, x in enumerate(data) if x in data[:n]]:
        logger.info("%d duplicate entries found.", len(dupes))
        cleaned = list(set(data))
        with stock_db.connection:
            cursor = stock_db.connection.cursor()
            cursor.execute("DELETE FROM stock")
            for record in cleaned:
                cursor.execute(f"INSERT or REPLACE INTO stock {stock_monitor.user_info} "
                               f"VALUES {stock_monitor.values};", record)
            stock_db.connection.commit()


def insert_stock_userdata(entry: Tuple[str, EmailStr, Union[int, float], Union[int, float], int]) -> NoReturn:
    """Inserts new entry into the stock database.

    Args:
        entry: Tuple of information that has to be inserted.
    """
    with stock_db.connection:
        cursor = stock_db.connection.cursor()
        cursor.execute(f"INSERT or REPLACE INTO stock {stock_monitor.user_info} VALUES {stock_monitor.values};",
                       entry)
        stock_db.connection.commit()


def get_stock_userdata(email: Optional[Union[EmailStr, str]] = None) -> \
        List[Tuple[str, EmailStr, Union[int, float], Union[int, float], int]]:
    """Reads the stock database to get all the user data.

    Returns:
        list:
        List of tuple of user information.
    """
    with stock_db.connection:
        cursor = stock_db.connection.cursor()
        if email:
            data = cursor.execute("SELECT * FROM stock WHERE email=(?)", (email,)).fetchall()
        else:
            data = cursor.execute("SELECT * FROM stock").fetchall()
    return data


def delete_stock_userdata(data: Tuple[str, EmailStr, Union[int, float], Union[int, float], int]) -> NoReturn:
    """Delete particular user data from stock database.

    Args:
        data: Tuple of user information to be deleted.
    """
    with stock_db.connection:
        cursor = stock_db.connection.cursor()
        cursor.execute("DELETE FROM stock WHERE ticker=(?) AND email=(?) AND max=(?) AND min=(?) AND correction=(?);",
                       data)
        stock_db.connection.commit()
