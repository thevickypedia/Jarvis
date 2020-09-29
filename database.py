import sqlite3

connection = sqlite3.connect('todo.db')
connection.execute("CREATE TABLE todo (category, item)")
connection.execute("INSERT INTO todo (category, item) VALUES ('Shopping','onions')")
connection.execute("INSERT INTO todo (category, item) VALUES ('Shopping','milk')")
connection.execute("INSERT INTO todo (category, item) VALUES ('Shopping','bread')")
connection.commit()

connector = connection.cursor()
connector.execute("SELECT category, item from todo")
result = connector.fetchall()
connector.close()
print(result)
