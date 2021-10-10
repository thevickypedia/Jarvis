from os.path import isfile
from sqlite3 import connect

file_name = 'tasks.db'


class Database:
    """Connector for ``Database`` to create and modify.

    >>> Database

    ``create_db`` - creates a database named 'tasks.db' with table as 'tasks'
    ``downloader`` - gets item and category stored in the table 'tasks'
    ``uploader`` - adds new item and category to the table 'tasks' and groups with existing category if found
    ``deleter`` - removes items from the table 'tasks' when the item or category name is matched.
    """

    def __init__(self):
        self.file_name = file_name
        self.table_name = self.file_name.replace('.db', '')

    def create_db(self) -> str:
        """Creates a database with the set ``filename: tasks.db`` and a ``table: tasks``.

        Returns:
            str:
            A success message on DB and table creation.
        """
        if isfile(self.file_name):
            return f"A database named, {self.file_name}, already exists."
        else:
            connection = connect(self.file_name)
            connection.execute(f"CREATE TABLE {self.table_name} (category, item, id INTEGER PRIMARY KEY )")
            connection.commit()
            return "A database has been created."

    def downloader(self) -> list:
        """Downloads the rows and columns in the table.

        Returns:
            list:
            The downloaded table information.
        """
        connection = connect(self.file_name)
        connector = connection.cursor()
        connector.execute(f"SELECT category, item from {self.table_name}")
        response = connector.fetchall()
        connector.close()
        return response

    def uploader(self, category: str, item: str) -> str:
        """Updates the table: tasks with new rows.

        Args:
            category: Category under which a task falls. (Eg: Groceries)
            item: Item which has to be added to the category. (Eg: Water can)

        Returns:
            str:
            A string indicating the item and category that it was added to.
        """
        connection = connect(self.file_name)
        response = self.downloader()
        for c, i in response:  # browses through all categories and items
            if i == item and c == category:  # checks if already present and updates items in case of repeated category
                return f"Looks like the table: {self.table_name}, already has the item: {item} in, {category} category"
        connection.execute(f"INSERT INTO {self.table_name} (category, item) VALUES ('{category}','{item}')")
        connection.commit()
        return f"I've added the item: {item} to the category: {category}."

    def deleter(self, keyword: str) -> str:
        """Deletes a particular record from the table.

        Args:
            keyword: Takes the item that has to be removed as an argument.

        Returns:
            str:
            On success, returns a string indicating the item has been deleted.
            On failure, returns a string indicating the item was not found.
        """
        connection = connect(self.file_name)
        response = self.downloader()
        delete = None
        c, i = None, None
        for c, i in response:  # browses through all categories and items
            if c.lower() == keyword:  # matches keyword with Category to choose the deletion value
                delete = c
            elif i.lower() == keyword:  # matches keyword with Item to choose the deletion value
                delete = i
        # if check remains 0 returns the message that the item or category wasn't found
        if not delete:
            return f"Looks like there is no item or category with the name: {keyword}"
        connection.execute(f"DELETE FROM {self.table_name} WHERE item='{delete}' OR category='{delete}'")
        connection.commit()
        if c and i:
            return f"Item: {i} from the Category: {c} has been removed from {self.table_name}."
        else:
            return f"Item: {keyword} has been removed from {self.table_name}."


if __name__ == '__main__':
    data = Database().downloader()
    for row in data:
        result = {row[i]: row[i + 1] for i in range(0, len(row), 2)}
        print(result)
