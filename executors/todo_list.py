import json
import os
import random
import sys

from modules.audio import listener, speaker
from modules.conditions import conversation, keywords
from modules.tasks import tasks
from modules.utils import globals, support


def create_db() -> None:
    """Creates a database for to-do list by calling the ``create_db`` function in ``database`` module."""
    speaker.speak(text=tasks.create_db())
    if globals.called['todo']:
        globals.called['todo'] = False
        todo()
    elif globals.called['add_todo']:
        globals.called['add_todo'] = False
        add_todo()


def todo(no_repeat: bool = False) -> None:
    """Says the item and category stored in the to-do list.

    Args:
        no_repeat: A placeholder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
    """
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(tasks.TASKS_DB) and (globals.called['time_travel'] or globals.called['report']):
        pass
    elif not os.path.isfile(tasks.TASKS_DB):
        if globals.called_by_offline['status']:
            speaker.speak(text="Your don't have any items in your to-do list sir!")
            return
        if no_repeat:
            speaker.speak(text="Would you like to create a database for your to-do list?")
        else:
            speaker.speak(
                text="You don't have a database created for your to-do list sir. Would you like to spin up one now?")
        speaker.speak(run=True)
        key = listener.listen(timeout=3, phrase_limit=3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok):
                globals.called['todo'] = True
                support.flush_screen()
                create_db()
            else:
                return
        else:
            if no_repeat:
                return
            speaker.speak(text="I didn't quite get that. Try again.")
            todo(no_repeat=True)
    else:
        sys.stdout.write("\rQuerying DB for to-do list..")
        result = {}
        for category, item in tasks.downloader():
            # condition below makes sure one category can have multiple items without repeating category for each item
            if category not in result:
                result.update({category: item})  # creates dict for category and item if category is not found in result
            else:
                result[category] = result[category] + ', ' + item  # updates category if already found in result
        support.flush_screen()
        if result:
            if globals.called_by_offline['status']:
                speaker.speak(text=json.dumps(result))
                return
            speaker.speak(text='Your to-do items are')
            for category, item in result.items():  # browses dictionary and stores result in response and says it
                response = f"{item}, in {category} category."
                speaker.speak(text=response)
        elif globals.called['report'] and not globals.called['time_travel']:
            speaker.speak(text="You don't have any tasks in your to-do list sir.")
        elif globals.called['time_travel']:
            pass
        else:
            speaker.speak(text="You don't have any tasks in your to-do list sir.")

    if globals.called['report'] or globals.called['time_travel']:
        speaker.speak(run=True)


def add_todo() -> None:
    """Adds new items to the to-do list."""
    sys.stdout.write("\rLooking for to-do database..")
    # if database file is not found calls create_db()
    if not os.path.isfile(tasks.TASKS_DB):
        support.flush_screen()
        speaker.speak(text="You don't have a database created for your to-do list sir.")
        speaker.speak(text="Would you like to spin up one now?", run=True)
        key = listener.listen(timeout=3, phrase_limit=3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok):
                globals.called['add_todo'] = True
                support.flush_screen()
                create_db()
            else:
                return
    speaker.speak(text="What's your plan sir?", run=True)
    item = listener.listen(timeout=3, phrase_limit=5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            speaker.speak(text='Your to-do list has been left intact sir.')
        else:
            speaker.speak(text=f"I heard {item}. Which category you want me to add it to?", run=True)
            category = listener.listen(timeout=3, phrase_limit=3)
            if category == 'SR_ERROR':
                category = 'Unknown'
            if 'exit' in category or 'quit' in category or 'Xzibit' in category:
                speaker.speak(text='Your to-do list has been left intact sir.')
            else:
                # passes the category and item to uploader() in modules/database.py which updates the database
                response = tasks.uploader(category, item)
                speaker.speak(text=response)
                speaker.speak(text="Do you want to add anything else to your to-do list?", run=True)
                category_continue = listener.listen(timeout=3, phrase_limit=3)
                if any(word in category_continue.lower() for word in keywords.ok):
                    add_todo()
                else:
                    speaker.speak(text='Alright')


def delete_todo() -> None:
    """Deletes items from an existing to-do list."""
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(tasks.TASKS_DB):
        speaker.speak(text="You don't have a database created for your to-do list sir.")
        return
    speaker.speak(text="Which one should I remove sir?", run=True)
    item = listener.listen(timeout=3, phrase_limit=5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            return
        response = tasks.deleter(keyword=item.lower())
        # if the return message from database starts with 'Looks' it means that the item wasn't matched for deletion
        speaker.speak(text=response, run=True)


def delete_db() -> None:
    """Deletes the ``tasks.db`` database file after getting confirmation."""
    if not os.path.isfile(tasks.TASKS_DB):
        speaker.speak(text='I did not find any database sir.')
        return
    else:
        speaker.speak(text=f'{random.choice(conversation.confirmation)} delete your database?', run=True)
        response = listener.listen(timeout=3, phrase_limit=3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.ok):
                os.remove(tasks.TASKS_DB)
                speaker.speak(text="I've removed your database sir.")
            else:
                speaker.speak(text="Your database has been left intact sir.")
            return
