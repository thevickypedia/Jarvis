# noinspection PyUnresolvedReferences
"""This is a space for variables shared across multiple modules.

>>> Shared

"""

import time

start_time = time.time()
greeting = False
called_by_offline = False

text_spoken = None
offline_caller = None
tv = {}

processes = {}
hosted_device = {}

called = {
    'report': False,
    'locate_places': False,
    'directions': False,
    'google_maps': False,
    'time_travel': False,
    'todo': False,
    'add_todo': False
}
