import os
import sqlite3

file_name = 'tasks.db'
table_name = file_name.replace('.db', '')


class Database:
    def create_db(self):
        if os.path.isfile(file_name):
            return f"A database named, {file_name}, already exists."
        else:
            connection = sqlite3.connect(file_name)
            connection.execute(f"CREATE TABLE {table_name} (category, item, id INTEGER PRIMARY KEY )")
            connection.commit()
            return "A database has been created."

    def uploader(self, category, item):
        connection = sqlite3.connect(file_name)
        connector = connection.cursor()
        connector.execute(f"SELECT category, item from {table_name}")
        response = connector.fetchall()
        for c, i in response:
            if i == item and c == category:
                return f"Looks like the table: {table_name}, already has the item: {item} in, {category} category"
        connection.execute(f"INSERT INTO {table_name} (category, item) VALUES ('{category}','{item}')")
        connection.commit()
        return f"I've added the item: {item} to the category: {category}."

    def downloader(self):
        connection = sqlite3.connect(file_name)
        connector = connection.cursor()
        connector.execute(f"SELECT category, item from {table_name}")
        response = connector.fetchall()
        connector.close()
        return response

    def deleter(self, item):
        connection = sqlite3.connect(file_name)
        connector = connection.cursor()
        connector.execute(f"SELECT category, item from {table_name}")
        response = connector.fetchall()
        check = 0
        for c, i in response:
            if i == item or c == item:
                check += 1
        if check == 0:
            return f"Looks like there is no item or category with the name: {item}"
        connection.execute(f"DELETE FROM {table_name} WHERE item='{item}' OR category='{item}'")
        connection.commit()
        return f"Item: {item} has been removed from {table_name}."


if __name__ == '__main__':
    data = Database().downloader()
    for row in data:
        result = {row[i]: row[i + 1] for i in range(0, len(row), 2)}
        print(result)
