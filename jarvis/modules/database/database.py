"""Module for database controls.

>>> Database

"""

import importlib
import logging
import os
import random
import sqlite3
from typing import List, NoReturn, Tuple, Union

from pydantic import FilePath


class Database:
    """Creates a connection to the base DB.

    >>> Database

    """

    def __init__(self, database: Union[FilePath, str], timeout: int = 10):
        """Instantiates the class ``Database`` to create a connection and a cursor.

        Args:
            database: Name of the database file.
            timeout: Timeout for the connection to database.
        """
        if not database.endswith('.db'):
            database = database + '.db'
        self.connection = sqlite3.connect(database=database, check_same_thread=False, timeout=timeout)

    def create_table(self, table_name: str, columns: Union[List[str], Tuple[str]]) -> NoReturn:
        """Creates the table with the required columns.

        Args:
            table_name: Name of the table that has to be created.
            columns: List of columns that has to be created.
        """
        with self.connection:
            cursor = self.connection.cursor()
            # Use f-string or %s as table names cannot be parametrized
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})")


class __TestDatabase:
    """Basic examples of a test database.

    >>> __TestDatabase

    """

    def __init__(self):
        """Initiates all the imported modules and creates a database file named ``sample``."""
        importlib.reload(module=logging)

        handler = logging.StreamHandler()
        fmt_ = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s',
            datefmt='%b-%d-%Y %I:%M:%S %p'
        )
        handler.setFormatter(fmt=fmt_)
        logging.root.addHandler(hdlr=handler)
        logging.root.setLevel(level=logging.DEBUG)
        self.db = Database(database="sample")

    def __del__(self):
        """Deletes the database file ``sample``."""
        os.remove("sample.db")

    def random_single(self) -> NoReturn:
        """Example using a single column."""
        self.db.create_table(table_name="TestDatabase", columns=["column"])
        with self.db.connection:
            cursor_ = self.db.connection.cursor()
            cursor_.execute("INSERT INTO TestDatabase (column) VALUES (?);", (True,))
            self.db.connection.commit()
            if foo := cursor_.execute("SELECT column FROM TestDatabase").fetchone():
                logging.info(foo[0])
                cursor_.execute("DELETE FROM TestDatabase WHERE column=1")
                self.db.connection.commit()
            if bar := cursor_.execute("SELECT column FROM TestDatabase").fetchone():
                logging.warning(bar[0])
            cursor_.execute("DROP TABLE IF EXISTS TestDatabase")
            self.db.connection.commit()

    def random_double(self) -> NoReturn:
        """Example using two columns with only one holding a value at any given time."""
        self.db.create_table(table_name="TestDatabase", columns=["row", "column"])
        with self.db.connection:
            cursor_ = self.db.connection.cursor()
            cursor_.execute(f"INSERT INTO TestDatabase ({random.choice(['row', 'column'])}) VALUES (?);", (True,))
            self.db.connection.commit()
            if (row := cursor_.execute("SELECT row FROM TestDatabase").fetchone()) and row[0]:
                logging.info(f"Row: {row[0]}")
                cursor_.execute("DELETE FROM TestDatabase WHERE row=1")
                self.db.connection.commit()
            if (col := cursor_.execute("SELECT column FROM TestDatabase").fetchone()) and col[0]:
                logging.info(f"Column: {col[0]}")
                cursor_.execute("DELETE FROM TestDatabase WHERE column=1")
                self.db.connection.commit()
            cursor_.execute("DROP TABLE IF EXISTS TestDatabase")
            self.db.connection.commit()


if __name__ == '__main__':
    test_db = __TestDatabase()
    test_db.random_single()
    test_db.random_double()
