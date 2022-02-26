# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Models

"""

import getpass
import os.path
import socket

from pydantic import (BaseSettings, DirectoryPath, EmailStr, Field,
                      PositiveFloat, PositiveInt)


class EnvConfigValidated(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfigValidated

    """

    home: DirectoryPath = Field(default=os.path.expanduser('~'), env='home')
    weather_api: str = Field(default=None, env='weather_api')
    gmail_user: EmailStr = Field(default=None, env='gmail_user')
    gmail_pass: str = Field(default=None, env='gmail_pass')
    alt_gmail_user: EmailStr = Field(default=None, env='alt_gmail_user')
    alt_gmail_pass: str = Field(default=None, env='alt_gmail_pass')
    recipient: EmailStr = Field(default=None, env='recipient')
    phone_number: str = Field(default=None, env='phone_number')
    offline_host: str = Field(default=socket.gethostbyname('localhost'), env='offline_host')
    offline_port: PositiveInt = Field(default=4483, env='offline_port')
    offline_pass: str = Field(default='OfflineComm', env='offline_pass')
    icloud_user: EmailStr = Field(default=None, env='icloud_user')
    icloud_pass: str = Field(default=None, env='icloud_pass')
    robinhood_user: EmailStr = Field(default=None, env='robinhood_user')
    robinhood_pass: str = Field(default=None, env='robinhood_pass')
    robinhood_qr: str = Field(default=None, env='robinhood_qr')
    robinhood_endpoint_auth: str = Field(default=None, env='robinhood_endpoint_auth')
    meeting_app: str = Field(default='calendar', env='meeting_app')
    website: str = Field(default='thevickypedia.com', env='website')
    wolfram_api_key: str = Field(default=None, env='wolfram_api_key')
    maps_api: str = Field(default=None, env='maps_api')
    news_api: str = Field(default=None, env='news_api')
    icloud_recovery: str = Field(default=None, env='icloud_recovery')
    git_user: str = Field(default=None, env='git_user')
    git_pass: str = Field(default=None, env='git_pass')
    tv_client_key: str = Field(default=None, env='tv_client_key')
    root_user: str = Field(default=getpass.getuser(), env='USER')
    root_password: str = Field(default=None, env='root_password')
    router_pass: str = Field(default=None, env='router_pass')
    vpn_username: str = Field(default=None, env='vpn_username')
    vpn_password: str = Field(default=None, env='vpn_password')
    birthday: str = Field(default=None, env='birthday')
    car_email: EmailStr = Field(default=None, env='car_email')
    car_pass: str = Field(default=None, env='car_pass')
    car_pin: PositiveInt = Field(default=None, env='car_pin')
    sensitivity: PositiveFloat = Field(default=0.5, env='sensitivity')
    timeout: PositiveInt = Field(default=3, env='timeout')
    phrase_limit: PositiveInt = Field(default=3, env='phrase_limit')

    class Config:
        """Environment variables configuration."""

        env_prefix = None
        env_file = '.env'


class EnvConfigUnvalidated:
    """Class to load all env vars to share across modules.

    >>> EnvConfigUnvalidated

    """

    home = os.path.expanduser('~')
    weather_api = os.environ.get('weather_api')
    gmail_user = os.environ.get('gmail_user')
    gmail_pass = os.environ.get('gmail_pass')
    alt_gmail_user = os.environ.get('alt_gmail_user', gmail_user)
    alt_gmail_pass = os.environ.get('alt_gmail_pass', gmail_pass)
    recipient = os.environ.get('recipient', gmail_user)
    phone_number = os.environ.get('phone_number')
    offline_host = socket.gethostbyname('localhost')
    offline_port = int(os.environ.get('offline_port', 4483))
    offline_pass = os.environ.get('offline_pass')
    icloud_user = os.environ.get('icloud_user')
    icloud_pass = os.environ.get('icloud_pass')
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
    root_user = os.environ.get('USER', getpass.getuser())
    root_password = os.environ.get('root_password')
    router_pass = os.environ.get('router_pass')
    vpn_username = os.environ.get('vpn_username', root_user or 'openvpn')
    vpn_password = os.environ.get('vpn_password', root_password or 'aws_vpn_2021')
    birthday = os.environ.get('birthday')
    car_email = os.environ.get('car_email')
    car_pass = os.environ.get('car_pass')
    car_pin = os.environ.get('car_pin')
    sensitivity = float(os.environ.get('sensitivity', 0.5))
    timeout = int(os.environ.get('timeout', 3))
    phrase_limit = int(os.environ.get('phrase_limit', 3))


if os.path.isfile('.env'):
    env = EnvConfigValidated()
else:
    env = EnvConfigUnvalidated
