import os
import sqlite3

file_name = 'todo.db'
table_name = file_name.replace('.db', '')


class Database:
    def create_db(self):
        if os.path.isfile(file_name):
            return f"Database {file_name} already exists."
        else:
            connection = sqlite3.connect(file_name)
            connection.execute(f"CREATE TABLE {table_name} (category, item)")
            connection.commit()
            return f"Database {file_name} has been created."

    def uploader(self, category, item):
        connection = sqlite3.connect(file_name)
        connection.execute(f"INSERT INTO {table_name} (category, item) VALUES ('{category}','{item}')")
        connection.commit()
        return f"Table {table_name} has been updated with Category: {category} and Item: {item}."

    def downloader(self):
        connection = sqlite3.connect(file_name)
        connector = connection.cursor()
        connector.execute(f"SELECT category, item from {table_name}")
        response = connector.fetchall()
        connector.close()
        return response


if __name__ == '__main__':
    data = Database().downloader()
    for row in data:
        result = {row[i]: row[i + 1] for i in range(0, len(row), 2)}
        print(result)
