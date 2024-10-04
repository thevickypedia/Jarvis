from multiprocessing import Process
from typing import Any, Callable, Dict, Tuple

from jarvis.modules.database import database
from jarvis.modules.models import models

db = database.Database(database=models.fileio.base_db)


def semaphores(
    fn: Callable,
    args: Tuple = None,
    kwargs: Dict[str, Any] = None,
    daemon: bool = False,
) -> None:
    """Resource tracker to store undefined process IDs in the base database and cleanup at shutdown.

    Args:
        fn: Function to start multiprocessing for.
        args: Optional arguments to pass.
        kwargs: Keyword arguments to pass.
        daemon: Boolean flag to set daemon mode.
    """
    process = Process(target=fn, args=args or (), kwargs=kwargs or {}, daemon=daemon)
    process.start()
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("INSERT INTO children (undefined) VALUES (?);", (process.pid,))
        db.connection.commit()
