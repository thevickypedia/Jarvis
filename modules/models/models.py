# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Models

"""

import getpass
import os.path
import platform
import socket

from pydantic import (BaseModel, BaseSettings, DirectoryPath, EmailStr, Field,
                      FilePath, PositiveInt)

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')


class FileIO(BaseModel):
    """Loads all the files' path required/created by Jarvis.

    >>> FileIO

    """

    automation: FilePath = f'fileio{os.path.sep}automation.yaml'
    tmp_automation: FilePath = f'fileio{os.path.sep}tmp_automation.yaml'
    base_db: FilePath = f'fileio{os.path.sep}database.db'
    frequent: FilePath = f'fileio{os.path.sep}frequent.yaml'
    location: FilePath = f'fileio{os.path.sep}location.yaml'
    meetings: FilePath = f'fileio{os.path.sep}meetings'
    notes: FilePath = f'fileio{os.path.sep}notes.txt'
    smart_devices: FilePath = f'fileio{os.path.sep}smart_devices.yaml'
    hostnames: FilePath = f'fileio{os.path.sep}hostnames.yaml'
    task_db: FilePath = f'fileio{os.path.sep}tasks.db'
    training: FilePath = f'fileio{os.path.sep}training_data.yaml'


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    home: DirectoryPath = Field(default=os.path.expanduser('~'), env='HOME')
    weather_api: str = Field(default=None, env='WEATHER_API')
    gmail_user: EmailStr = Field(default=None, env='GMAIL_USER')
    gmail_pass: str = Field(default=None, env='GMAIL_PASS')
    alt_gmail_user: EmailStr = Field(default=None, env='ALT_GMAIL_USER')
    alt_gmail_pass: str = Field(default=None, env='ALT_GMAIL_PASS')
    recipient: EmailStr = Field(default=None, env='RECIPIENT')
    phone_number: str = Field(default=None, env='PHONE_NUMBER')
    offline_host: str = Field(default=socket.gethostbyname('localhost'), env='OFFLINE_HOST')
    offline_port: PositiveInt = Field(default=4483, env='OFFLINE_PORT')
    offline_pass: str = Field(default='OfflineComm', env='OFFLINE_PASS')
    icloud_user: EmailStr = Field(default=None, env='ICLOUD_USER')
    icloud_pass: str = Field(default=None, env='ICLOUD_PASS')
    icloud_recovery: str = Field(default=None, env='ICLOUD_RECOVERY')
    robinhood_user: EmailStr = Field(default=None, env='ROBINHOOD_USER')
    robinhood_pass: str = Field(default=None, env='ROBINHOOD_PASS')
    robinhood_qr: str = Field(default=None, env='ROBINHOOD_QR')
    robinhood_endpoint_auth: str = Field(default=None, env='ROBINHOOD_ENDPOINT_AUTH')
    meeting_app: str = Field(default='calendar', env='MEETING_APP')
    website: str = Field(default='vigneshrao.com', env='WEBSITE')
    wolfram_api_key: str = Field(default=None, env='WOLFRAM_API_KEY')
    maps_api: str = Field(default=None, env='MAPS_API')
    news_api: str = Field(default=None, env='NEWS_API')
    git_user: str = Field(default=None, env='GIT_USER')
    git_pass: str = Field(default=None, env='GIT_PASS')
    tv_client_key: str = Field(default=None, env='TV_CLIENT_KEY')
    root_user: str = Field(default=getpass.getuser(), env='USER')
    root_password: str = Field(default=None, env='ROOT_PASSWORD')
    router_pass: str = Field(default=None, env='ROUTER_PASS')
    vpn_username: str = Field(default=None, env='VPN_USERNAME')
    vpn_password: str = Field(default=None, env='VPN_PASSWORD')
    birthday: str = Field(default=None, env='BIRTHDAY')
    car_email: EmailStr = Field(default=None, env='CAR_EMAIL')
    car_pass: str = Field(default=None, env='CAR_PASS')
    car_pin: str = Field(default=None, regex="\\d{4}$", env='CAR_PIN')
    sensitivity: float = Field(default=0.5, le=1, ge=0, env='SENSITIVITY')
    timeout: PositiveInt = Field(default=3, env='TIMEOUT')
    phrase_limit: PositiveInt = Field(default=3, env='PHRASE_LIMIT')
    bot_token: str = Field(default=None, env='BOT_TOKEN')
    bot_chat_ids: list = Field(default=[], env='BOT_CHAT_IDS')
    bot_users: list = Field(default=[], env='BOT_USERS')
    legacy_keywords: list = Field(default=['jarvis'], env='LEGACY_KEYWORDS')
    title: str = Field(default='sir', env='TITLE')
    name: str = Field(default='Vignesh', env='NAME')

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"

    if platform.system() == "Windows":
        mac = 0
    elif platform.system() == "Darwin":
        mac = 1
    else:
        raise SystemError(
            f"\n{''.join('*' for _ in range(80))}\n\n"
            "Unsupported Operating System. Currently Jarvis can run only on Mac and Windows OS.\n\n"
            "To raise an issue: https://github.com/thevickypedia/Jarvis/issues/new\n"
            "To reach out: https://vigneshrao.com/contact\n"
            f"\n{''.join('*' for _ in range(80))}\n"
        )


env = EnvConfig()
fileio = FileIO()
