from collections.abc import Generator
from typing import Dict, List, Optional, Tuple

from pydantic import EmailStr

from jarvis.api.logger import logger
from jarvis.api.models import settings
from jarvis.modules.database import database
from jarvis.modules.models import models

stock_db = database.Database(database=models.fileio.stock_db)
stock_db.create_table(table_name="stock", columns=settings.stock_monitor.user_info)
stock_db.create_table(table_name="stock_daily", columns=settings.stock_monitor.alerts)


def cleanup_stock_userdata() -> None:
    """Delete duplicates tuples within the database."""
    data = get_stock_userdata()
    if dupes := [x for n, x in enumerate(data) if x in data[:n]]:
        logger.info("%d duplicate entries found.", len(dupes))
        cleaned = list(set(data))
        with stock_db.connection as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM stock")
            for params in cleaned:
                query = (
                    f"INSERT or REPLACE INTO stock {settings.stock_monitor.user_info} "
                    f"VALUES {settings.stock_monitor.values};"
                )
                cursor.execute(query, params)
            connection.commit()


def insert_stock_userdata(
    params: Tuple[str, EmailStr, int | float, int | float, int, str]
) -> None:
    """Inserts new entry into the stock database.

    Args:
        params: Tuple of information that has to be inserted.
    """
    with stock_db.connection as connection:
        cursor = connection.cursor()
        query = (
            f"INSERT or REPLACE INTO stock {settings.stock_monitor.user_info} "
            f"VALUES {settings.stock_monitor.values};"
        )
        cursor.execute(query, params)
        connection.commit()


def get_stock_userdata(
    email: Optional[EmailStr | str] = None,
) -> List[Tuple[str, EmailStr, int | float, int | float, int, str]]:
    """Reads the stock database to get all the user data.

    Returns:
        list:
        List of tuple of user information.
    """
    with stock_db.connection as connection:
        cursor = connection.cursor()
        if email:
            data = cursor.execute(
                "SELECT * FROM stock WHERE email=(?)", (email,)
            ).fetchall()
        else:
            data = cursor.execute("SELECT * FROM stock").fetchall()
    return data


def get_daily_alerts() -> Generator[
    Dict[int, Tuple[int, str, EmailStr, int | float, int | float, int, str]]
]:
    """Get all the information stored in ``stock_daily`` database table.

    Yields:
        A dictionary of epoch time and tuple of user information stored as key value pairs.
    """
    with stock_db.connection as connection:
        cursor = connection.cursor()
        data = cursor.execute("SELECT * FROM stock_daily").fetchall()
        yield {record[0]: record[1:] for record in data}


def put_daily_alerts(
    params: List[
        Dict[int, Tuple[int, str, EmailStr, int | float, int | float, int, str]]
    ]
):
    """Updates the daily alerts into the ``stock_daily`` database table.

    Args:
        params: Takes the tuple of all entries that has to be inserted.
    """
    with stock_db.connection as connection:
        cursor = connection.cursor()
        params = [(key, *values) for param in params for key, values in param.items()]
        # clear all existing data
        cursor.execute("DELETE FROM stock_daily")
        query = (
            f"INSERT OR REPLACE INTO stock_daily {settings.stock_monitor.alerts} VALUES "
            f"{settings.stock_monitor.alert_values};"
        )
        for param in params:
            # write new data in db
            cursor.execute(query, param)
        connection.commit()


def delete_stock_userdata(
    data: Tuple[str, EmailStr, int | float, int | float, int, str]
) -> None:
    """Delete particular user data from stock database.

    Args:
        data: Tuple of user information to be deleted.
    """
    with stock_db.connection as connection:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM stock WHERE ticker=(?) AND email=(?) AND "
            "max=(?) AND min=(?) AND correction=(?) AND repeat=(?);",
            data,
        )
        connection.commit()
