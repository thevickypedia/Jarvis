import sqlite3
from typing import NoReturn

from jarvis.modules.audio import speaker
from jarvis.modules.database import database
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.retry import retry

db = database.Database(database=models.fileio.base_db)


def listener_control(phrase: str) -> NoReturn:
    """Controls the listener table in base db.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    state = get_listener_state()
    if "deactivate" in phrase or "disable" in phrase:
        if state:
            put_listener_state(state=False)
            speaker.speak(text=f"Listener has been deactivated {models.env.title}!")
        else:
            speaker.speak(text=f"Listener was never activated {models.env.title}!")
    elif "activate" in phrase or "enable" in phrase:
        if state:
            speaker.speak(text=f"Listener is already active {models.env.title}!")
        else:
            put_listener_state(state=True)
            speaker.speak(text=f"Listener has been activated {models.env.title}!")
    else:
        if state:
            speaker.speak(text=f"Listener is currently active {models.env.title}!")
        else:
            speaker.speak(text=f"Listener is currently inactive {models.env.title}!")


def get_listener_state() -> bool:
    """Gets the current state of listener.

    Returns:
        bool: A boolean flag to indicate if the listener is active.
    """
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT state FROM listener").fetchone()
    if state and state[0]:
        logger.debug("Listener is currently enabled")
        return True
    else:
        logger.debug("Listener is currently disabled")


@retry.retry(attempts=3, interval=2, exclude_exc=sqlite3.OperationalError)
def put_listener_state(state: bool) -> NoReturn:
    """Updates the state of the listener.

    Args:
        state: Takes the boolean value to be inserted.
    """
    logger.info("Current listener status: '%s'", get_listener_state())
    logger.info("Updating listener status to %s", state)
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM listener")
        if state:
            cursor.execute("INSERT or REPLACE INTO listener (state) VALUES (?);", (state,))
            cursor.execute("UPDATE listener SET state=(?)", (state,))
        else:
            cursor.execute("UPDATE listener SET state=null")
        db.connection.commit()
