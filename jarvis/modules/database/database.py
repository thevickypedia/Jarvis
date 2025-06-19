"""Module for database controls.

>>> Database

"""

import logging
import os
import random
import sqlite3
from typing import List, Tuple

from pydantic import FilePath


class Database:
    """Creates a connection to the base DB.

    >>> Database

    Args:
        database: Name of the database file.
        timeout: Timeout for the connection to database.
    """

    def __init__(self, database: FilePath | str, timeout: int = 3):
        """Instantiates the class ``Database`` with the given datastore and timeout options.

        Args:
            database: Database filepath.
            timeout: Connection timeout for the database.
        """
        if not database.endswith(".db"):
            database = database + ".db"
        self.datastore = database
        self.timeout = timeout

    @property
    def connection(self) -> sqlite3.Connection:
        """Creates a database connection.

        Returns:
            sqlite3.Connection:
            Returns a ``sqlite3.Connection`` object.
        """
        return sqlite3.connect(
            database=self.datastore, check_same_thread=False, timeout=self.timeout
        )

    def create_table(
        self, table_name: str, columns: List[str] | Tuple[str], primary_key: str = None
    ) -> None:
        """Creates the table with the required columns.

        Args:
            table_name: Name of the table that has to be created.
            columns: List of columns that has to be created.
            primary_key: Primary key.
        """
        if primary_key:
            # Ensure the column exists by name
            assert (
                primary_key in columns
            ), f"{primary_key!r} should be one of the columns"
            # Rebuild the column definition with PRIMARY KEY
            columns = [
                f"{col} PRIMARY KEY" if col == primary_key else col for col in columns
            ]
        with self.connection as connection:
            cursor = connection.cursor()
            # Use f-string or %s as table names cannot be parametrized
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            )


class __TestDatabase:
    """Basic examples of a test database.

    >>> __TestDatabase

    """

    def __init__(self):
        """Initiates all the imported modules and creates a database file named ``sample``."""
        handler = logging.StreamHandler()
        fmt_ = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
            datefmt="%b-%d-%Y %I:%M:%S %p",
        )
        handler.setFormatter(fmt=fmt_)
        logging.root.addHandler(hdlr=handler)
        logging.root.setLevel(level=logging.DEBUG)
        self.db = Database(database="sample")

    def at_exit(self):
        """Deletes the database file ``sample``."""
        os.remove(self.db.datastore)

    def random_single(self) -> None:
        """Example using a single column."""
        self.db.create_table(
            table_name="TestDatabase", columns=["column"], primary_key="column"
        )
        with self.db.connection as connection:
            cursor_ = connection.cursor()
            cursor_.execute("INSERT INTO TestDatabase (column) VALUES (?);", (True,))
            connection.commit()
            if foo := cursor_.execute("SELECT column FROM TestDatabase").fetchone():
                logging.info(foo[0])
                cursor_.execute("DELETE FROM TestDatabase WHERE column=1")
                connection.commit()
            if bar := cursor_.execute("SELECT column FROM TestDatabase").fetchone():
                logging.warning(bar[0])
            cursor_.execute("DROP TABLE IF EXISTS TestDatabase")
            connection.commit()

    def random_double(self) -> None:
        """Example using two columns with only one holding a value at any given time."""
        self.db.create_table(table_name="TestDatabase", columns=["row", "column"])
        with self.db.connection as connection:
            cursor_ = connection.cursor()
            cursor_.execute(
                f"INSERT INTO TestDatabase ({random.choice(['row', 'column'])}) VALUES (?);",
                (True,),
            )
            connection.commit()
            if (
                row := cursor_.execute("SELECT row FROM TestDatabase").fetchone()
            ) and row[0]:
                logging.info(f"Row: {row[0]}")
                cursor_.execute("DELETE FROM TestDatabase WHERE row=1")
                connection.commit()
            if (
                col := cursor_.execute("SELECT column FROM TestDatabase").fetchone()
            ) and col[0]:
                logging.info(f"Column: {col[0]}")
                cursor_.execute("DELETE FROM TestDatabase WHERE column=1")
                connection.commit()
            cursor_.execute("DROP TABLE IF EXISTS TestDatabase")
            connection.commit()


if __name__ == "__main__":
    test_db = __TestDatabase()
    test_db.random_single()
    test_db.random_double()
    test_db.at_exit()
