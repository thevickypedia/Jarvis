# noinspection PyUnresolvedReferences
"""This is a space for variables shared across multiple modules.

>>> Shared

"""

import sys
import time

if sys.platform != "win32":
    # noinspection PyProtectedMember
    from multiprocessing.connection import Connection
else:
    # noinspection PyProtectedMember
    from multiprocessing.connection import PipeConnection as Connection

start_time = time.time()
greeting = False
called_by_offline = False
called_by_bg_tasks = False
widget_connection: Connection | None = None

text_spoken = None
offline_caller = None
tv = {}

processes = {}

called = {
    "report": False,
    "locate_places": False,
    "directions": False,
}
