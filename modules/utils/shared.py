# noinspection PyUnresolvedReferences
"""This is a space for variables shared across multiple modules.

>>> Shared

"""

greeting = False
called_by_offline = False
called_by_automator = False

active_vpn = None
text_spoken = None
offline_caller = None
tv = None

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
