# noinspection PyUnresolvedReferences
"""This is a space for variables shared across multiple modules.

>>> Shared

"""

from datetime import datetime, timezone

LOCAL_TIMEZONE = datetime.now(tz=timezone.utc).astimezone().tzinfo

greeting = False
called_by_offline = False
called_by_automator = False

active_vpn = None
text_spoken = None
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
