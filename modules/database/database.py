# noinspection PyUnresolvedReferences
"""Connector for ``Database`` to create and modify.

>>> Database

- ``create_db``: creates a database named 'tasks.db' with table as 'tasks'
- ``downloader``: gets item and category stored in the table 'tasks'
- ``uploader``: adds new item and category to the table 'tasks' and groups with existing category if found
- ``deleter``: removes items from the table 'tasks' when the item or category name is matched.
"""

from os.path import isfile
from sqlite3 import connect

TASKS_DB = 'tasks.db'
table_name = TASKS_DB.replace('.db', '')


def create_db() -> str:
    """Creates a database with the set ``filename: tasks.db`` and a ``table: tasks``.

    Returns:
        str:
        A success message on DB and table creation.
    """
    if isfile(TASKS_DB):
        return f"A database named, {TASKS_DB}, already exists."
    else:
        connection = connect(TASKS_DB)
        connection.execute(f"CREATE TABLE {table_name} (category, item, id INTEGER PRIMARY KEY )")
        connection.commit()
        return "A database has been created."


def downloader() -> list:
    """Downloads the rows and columns in the table.

    Returns:
        list:
        The downloaded table information.
    """
    connection = connect(TASKS_DB)
    connector = connection.cursor()
    connector.execute(f"SELECT category, item from {table_name}")
    response = connector.fetchall()
    connector.close()
    return response


def uploader(category: str, item: str) -> str:
    """Updates the table: tasks with new rows.

    Args:
        category: Category under which a task falls. (Eg: Groceries)
        item: Item which has to be added to the category. (Eg: Water can)

    Returns:
        str:
        A string indicating the item and category that it was added to.
    """
    connection = connect(TASKS_DB)
    response = downloader()
    for c, i in response:  # browses through all categories and items
        if i == item and c == category:  # checks if already present and updates items in case of repeated category
            return f"Looks like the table: {table_name}, already has the item: {item} in, {category} category"
    connection.execute(f"INSERT INTO {table_name} (category, item) VALUES ('{category}','{item}')")
    connection.commit()
    return f"I've added the item: {item} to the category: {category}."


def deleter(keyword: str) -> str:
    """Deletes a particular record from the table.

    Args:
        keyword: Takes the item that has to be removed as an argument.

    Returns:
        str:
        On success, returns a string indicating the item has been deleted.
        On failure, returns a string indicating the item was not found.
    """
    connection = connect(TASKS_DB)
    response = downloader()
    delete = None
    cat, it = None, None
    for c, i in response:  # browses through all categories and items
        if c.lower() == keyword:  # matches keyword with Category to choose the deletion value
            delete = cat = c
            it = i
        elif i.lower() == keyword:  # matches keyword with Item to choose the deletion value
            delete = it = i
            cat = c
    # if check remains 0 returns the message that the item or category wasn't found
    if not delete:
        return f"Looks like there is no item or category with the name: {keyword}"
    connection.execute(f"DELETE FROM {table_name} WHERE item='{delete}' OR category='{delete}'")
    connection.commit()
    if cat and it:
        return f"Item: {it} from the Category: {cat} has been removed from {table_name}."
    else:
        return f"Item: {keyword} has been removed from {table_name}."


if __name__ == '__main__':
    for row in downloader():
        result = {row[i]: row[i + 1] for i in range(0, len(row), 2)}
        print(result)
