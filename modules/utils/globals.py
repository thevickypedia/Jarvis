# noinspection PyUnresolvedReferences
"""This is a space for dictionaries shared across multiple modules.

>>> Globals

"""

import os

RESTART_INTERVAL = int(os.environ.get('restart_interval', 28_800))  # 8 hours
STOPPER = {'status': False}

current_location_ = {}
text_spoken = {'text': ''}
vpn_status = {'active': False}
called_by_offline = {'status': False}
smart_devices = {}
hosted_device = {}
