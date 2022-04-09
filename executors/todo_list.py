import json
import sys

from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.database import database
from modules.models import models
from modules.utils import shared

env = models.env
fileio = models.fileio

tdb = database.Database(database=fileio.task_db)
tdb.create_table(table_name="tasks", columns=["category", "item"])


def todo() -> None:
    """Says the item and category stored in the to-do list."""
    sys.stdout.write("\rQuerying DB for to-do list..")
    with tdb.connection:
        cursor = tdb.connection.cursor()
        downloaded = cursor.execute("SELECT category, item FROM tasks").fetchall()
    result = {}
    for category, item in downloaded:
        # condition below makes sure one category can have multiple items without repeating category for each item
        if category not in result:
            result.update({category: item})  # creates dict for category and item if category is not found in result
        else:
            result[category] = result[category] + ', ' + item  # updates category if already found in result
    if result:
        if shared.called_by_offline:
            speaker.speak(text=json.dumps(result))
            return
        speaker.speak(text='Your to-do items are')
        for category, item in result.items():  # browses dictionary and stores result in response and says it
            response = f"{item}, in {category} category."
            speaker.speak(text=response)
    elif shared.called['report'] and not shared.called['time_travel']:
        speaker.speak(text=f"You don't have any tasks in your to-do list {env.title}.")
    elif shared.called['time_travel']:
        pass
    else:
        speaker.speak(text=f"You don't have any tasks in your to-do list {env.title}.")

    if shared.called['report'] or shared.called['time_travel']:
        speaker.speak(run=True)


def add_todo() -> None:
    """Adds new items to the to-do list."""
    speaker.speak(text=f"What's your plan {env.title}?", run=True)
    item = listener.listen(timeout=3, phrase_limit=5)
    if item == 'SR_ERROR' or 'exit' in item or 'quit' in item or 'Xzibit' in item:
        speaker.speak(text=f'Your to-do list has been left intact {env.title}.')
        return
    speaker.speak(text=f"I heard {item}. Which category you want me to add it to?", run=True)
    category = listener.listen(timeout=3, phrase_limit=3)
    if category == 'SR_ERROR':
        category = 'Unknown'
    if 'exit' in category or 'quit' in category or 'Xzibit' in category:
        speaker.speak(text=f'Your to-do list has been left intact {env.title}.')
        return
    with tdb.connection:
        cursor = tdb.connection.cursor()
        downloaded = cursor.execute("SELECT category, item FROM tasks").fetchall()
    if downloaded:
        for c, i in downloaded:  # browses through all categories and items
            if i == item and c == category:  # checks if already present and updates items in case of repeated category
                speaker.speak(text=f"Looks like you already have the item: {item} added in, {category} category")
                return
    with tdb.connection:
        cursor = tdb.connection.cursor()
        cursor.execute(f"INSERT OR REPLACE INTO tasks (category, item) VALUES {(category, item)}")
    speaker.speak(text=f"I've added the item: {item} to the category: {category}. "
                       "Do you want to add anything else to your to-do list?", run=True)
    category_continue = listener.listen(timeout=3, phrase_limit=3)
    if any(word in category_continue.lower() for word in keywords.ok):
        add_todo()
    else:
        speaker.speak(text='Alright')


def delete_todo_items() -> None:
    """Deletes items from an existing to-do list."""
    speaker.speak(text=f"Which one should I remove {env.title}?", run=True)
    item = listener.listen(timeout=3, phrase_limit=5)
    if item == 'SR_ERROR' or 'exit' in item or 'quit' in item or 'Xzibit' in item:
        speaker.speak(text=f'Your to-do list has been left intact {env.title}.')
        return
    with tdb.connection:
        cursor = tdb.connection.cursor()
        cursor.execute(f"DELETE FROM tasks WHERE item='{item}' OR category='{item}'")
        cursor.connection.commit()
    speaker.speak(text=f'Done {env.title}!', run=True)


def delete_todo() -> None:
    """Drops the table ``tasks`` from the database."""
    with tdb.connection:
        cursor = tdb.connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS tasks')
        cursor.connection.commit()
    speaker.speak(text=f"I've dropped the table: tasks from the database {env.title}.")
