from typing import List, NoReturn, Optional, Tuple, Union

from pydantic import EmailStr

from jarvis.api.modals.settings import stock_monitor
from jarvis.api.squire.logger import logger
from jarvis.modules.database import database
from jarvis.modules.models import models

stock_db = database.Database(database=models.fileio.stock_db)


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
