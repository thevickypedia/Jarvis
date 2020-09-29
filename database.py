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
