import os
from sqlite3 import connect

file_name = 'tasks.db'


class Database:
    """create_db - creates a database named 'tasks.db' with table as 'tasks'
       downloader - gets item and category stored in the table 'tasks'
       uploader - adds new item and category to the table 'tasks' and groups with existing category if found
       deleter - removes items from the table 'tasks' when the item or category name is matched."""

    def __init__(self):
        self.file_name = file_name
        self.table_name = self.file_name.replace('.db', '')

    def create_db(self):
        if os.path.isfile(self.file_name):
            return f"A database named, {self.file_name}, already exists."
        else:
            connection = connect(self.file_name)
            connection.execute(f"CREATE TABLE {self.table_name} (category, item, id INTEGER PRIMARY KEY )")
            connection.commit()
            return "A database has been created."

    def downloader(self):
        connection = connect(self.file_name)
        connector = connection.cursor()
        connector.execute(f"SELECT category, item from {self.table_name}")
        response = connector.fetchall()
        connector.close()
        return response

    def uploader(self, category, item):
        connection = connect(self.file_name)
        response = Database().downloader()
        for c, i in response:  # browses through all categories and items
            if i == item and c == category:  # checks if already present and updates items in case of repeated category
                return f"Looks like the table: {self.table_name}, already has the item: {item} in, {category} category"
        connection.execute(f"INSERT INTO {self.table_name} (category, item) VALUES ('{category}','{item}')")
        connection.commit()
        return f"I've added the item: {item} to the category: {category}."

    def deleter(self, item):
        connection = connect(self.file_name)
        response = Database().downloader()
        check = 0
        for c, i in response:  # browses through all categories and items
            if i == item or c == item:  # matches the item that needs to be deleted
                check += 1
        # if check remains 0 returns the message that the item or category wasn't found
        if check == 0:
            return f"Looks like there is no item or category with the name: {item}"
        connection.execute(f"DELETE FROM {self.table_name} WHERE item='{item}' OR category='{item}'")
        connection.commit()
        return f"Item: {item} has been removed from {self.table_name}."


if __name__ == '__main__':
    data = Database().downloader()
    for row in data:
        result = {row[i]: row[i + 1] for i in range(0, len(row), 2)}
        print(result)
