# noinspection PyUnresolvedReferences
"""This is a space for variables shared across multiple modules.

>>> Shared

"""

import time

start_time = time.time()
greeting = False
called_by_offline = False
called_by_bg_tasks = False

text_spoken = None
offline_caller = None
tv = {}

processes = {}

called = {
    "report": False,
    "locate_places": False,
    "directions": False,
}
