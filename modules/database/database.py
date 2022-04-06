import sqlite3
from typing import NoReturn


class Database:
    """Creates a connection to the base DB.

    >>> Database

    """

    def __init__(self, database: str):
        """Instantiates the class ``Database`` to create a connection and a cursor.

        Args:
            database: Name of the database file.
        """
        if not database.endswith('.db'):
            database = database + '.db'
        self.connection = sqlite3.connect(database=database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name: str, columns: list[str]) -> NoReturn:
        """Creates the table with the required columns.

        Args:
            table_name: Name of the table that has to be created.
            columns: List of columns that has to be created.
        """
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})")


if __name__ == '__main__':
    db = Database(database="sample")
    db.create_table(table_name="TestDatabase", columns=["column"])
    db.cursor.execute("INSERT INTO TestDatabase (column) VALUES (?);", (True,))
    db.connection.commit()
    if foo := db.cursor.execute("SELECT column FROM TestDatabase").fetchone():
        print(foo[0])
        db.cursor.execute("DELETE FROM TestDatabase WHERE column=1")
        db.connection.commit()
    if bar := db.cursor.execute("SELECT column FROM TestDatabase").fetchone():
        print(bar[0])
    db.cursor.execute("DROP TABLE IF EXISTS TestDatabase")
    db.connection.commit()
