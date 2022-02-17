# noinspection PyUnresolvedReferences
"""This is a space for dictionaries shared across multiple modules.

>>> Globals

"""

import os
from socket import gethostbyname

import dotenv

if os.path.isfile('.env'):
    dotenv.load_dotenv(dotenv_path='.env', verbose=True, override=True)  # loads the .env file

STOPPER = {'status': False}
current_location_ = {}
text_spoken = {'text': ''}
vpn_status = {'active': False}
called_by_offline = {'status': False}
smart_devices = {}
hosted_device = {}


class ENV:
    """Class to load all env vars to share across modules.

    >>> ENV

    """

    weather_api = os.environ.get('weather_api')
    gmail_user = os.environ.get('gmail_user')
    gmail_pass = os.environ.get('gmail_pass')
    recipient = os.environ.get('recipient')
    offline_host = gethostbyname('localhost')
    offline_port = int(os.environ.get('offline_port', 4483))
    icloud_user = os.environ.get('icloud_user')
    icloud_pass = os.environ.get('icloud_pass')
    phone_number = os.environ.get('phone_number')
    offline_pass = os.environ.get('offline_pass')
    robinhood_user = os.environ.get('robinhood_user')
    robinhood_pass = os.environ.get('robinhood_pass')
    robinhood_qr = os.environ.get('robinhood_qr')
    robinhood_endpoint_auth = os.environ.get('robinhood_endpoint_auth')
    meeting_app = os.environ.get('meeting_app', 'calendar')
    website = os.environ.get('website', 'thevickypedia.com')
    wolfram_api_key = os.environ.get('wolfram_api_key')
    maps_api = os.environ.get('maps_api')
    news_api = os.environ.get('news_api')
    icloud_recovery = os.environ.get('icloud_recovery')
    git_user = os.environ.get('git_user')
    git_pass = os.environ.get('git_pass')
    tv_client_key = os.environ.get('tv_client_key')
    root_password = os.environ.get('root_password')
    car_email = os.environ.get('car_email')
    car_pass = os.environ.get('car_pass')
    car_pin = os.environ.get('car_pin')
    sensitivity = float(os.environ.get('sensitivity', 0.5))
    timeout = int(os.environ.get('timeout', 3))
    phrase_limit = int(os.environ.get('phrase_limit', 3))
    restart_interval = int(os.environ.get('restart_interval', 28_800))  # 8 hours
