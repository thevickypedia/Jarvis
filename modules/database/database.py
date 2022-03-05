import sqlite3
from typing import Any, AnyStr, List

from executors.logger import logger


class Database:
    """Creates a connection to the base DB.

    >>> Database

    """

    def __init__(self, table_name: str, columns: list):
        """Instantiates the class ``Database`` to create a connection and a cursor.

        Args:
            table_name: Name of the table that has to be created.
            columns: List of columns that has to be created.
        """
        logger.info('Connecting to the Database...')
        self.table_name = table_name
        self.connection = sqlite3.connect(database='database.db')
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} ({', '.join(columns)})")
        self.cursor = self.connection.cursor()

    # def del(self):
    #     self.cursor.close()
    #     self.connection.close()
    #     logger.info('Database connection has closed.')

    def get(self, key: Any) -> AnyStr:
        """Placeholder method for reference."""
        if value := self.cursor.execute(f"SELECT value from {self.table_name} WHERE key=?", (key,)).fetchone():
            logger.info(f'Getting value for {key}')
            return value[0]

    def download(self) -> List:
        """Placeholder method for reference."""
        logger.info('Downloading the database.')
        return self.cursor.execute(f"SELECT * from {self.table_name}").fetchall()

    def upload(self, key: Any, value: Any) -> None:
        """Placeholder method for reference."""
        logger.info(f"Uploading {key}: {''.join(['*' for _ in str(value)])}")
        self.cursor.execute(f"INSERT OR REPLACE INTO {self.table_name} (key, value) VALUES ('{key}','{value}')")
        self.connection.commit()

    def delete(self, key: Any = None, value: Any = None) -> None:
        """Placeholder method for reference."""
        if not any([key, value]):
            logger.error('Requires either key or value which has to be deleted from the database.')
            return
        logger.info(f"Deleting {key or ''.join(['*' for _ in str(value)])}")
        self.cursor.execute(f"DELETE FROM {self.table_name} WHERE key=:key OR value=:value ",
                            {'key': key, 'value': value})
        self.connection.commit()
