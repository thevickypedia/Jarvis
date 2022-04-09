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

    def create_table(self, table_name: str, columns: list[str]) -> NoReturn:
        """Creates the table with the required columns.

        Args:
            table_name: Name of the table that has to be created.
            columns: List of columns that has to be created.
        """
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})")


if __name__ == '__main__':
    db = Database(database="sample")
    db.create_table(table_name="TestDatabase", columns=["column"])
    with db.connection:
        cursor_ = db.connection.cursor()
        cursor_.execute("INSERT INTO TestDatabase (column) VALUES (?);", (True,))
        db.connection.commit()
        if foo := cursor_.execute("SELECT column FROM TestDatabase").fetchone():
            print(foo[0])
            cursor_.execute("DELETE FROM TestDatabase WHERE column=1")
            db.connection.commit()
        if bar := cursor_.execute("SELECT column FROM TestDatabase").fetchone():
            print(bar[0])
        cursor_.execute("DROP TABLE IF EXISTS TestDatabase")
        db.connection.commit()
