# noinspection PyUnresolvedReferences
"""This is a space for dictionaries shared across multiple modules.

>>> Globals

"""

from datetime import datetime, timezone

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo

text_spoken = {'text': ''}
vpn_status = {'active': False}
called_by_offline = {'status': False}
processes = {}
hosted_device = {}
greet_check = {}
tv = None

called = {
    'report': False,
    'locate_places': False,
    'directions': False,
    'google_maps': False,
    'time_travel': False,
    'todo': False,
    'add_todo': False
}
