from multiprocessing import Process
from typing import Any, Callable, Dict, Tuple

from jarvis.modules.models import models


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
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO children (undefined) VALUES (?);", (process.pid,))
        connection.commit()
