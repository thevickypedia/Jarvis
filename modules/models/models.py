# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Models

"""

import getpass
import os
import platform
import socket
from datetime import datetime
from typing import Union

from pydantic import (BaseModel, BaseSettings, DirectoryPath, EmailStr, Field,
                      FilePath, HttpUrl, PositiveInt)

from modules.exceptions import InvalidEnvVars, UnsupportedOS

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    home: DirectoryPath = Field(default=os.path.expanduser('~'), env='HOME')
    volume: PositiveInt = Field(default=50, env='VOLUME')
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
    sync_meetings: PositiveInt = Field(default=3_600, env='SYNC_MEETINGS')
    sync_events: PositiveInt = Field(default=3_600, env='SYNC_EVENTS')
    icloud_user: EmailStr = Field(default=None, env='ICLOUD_USER')
    icloud_pass: str = Field(default=None, env='ICLOUD_PASS')
    icloud_recovery: str = Field(default=None, env='ICLOUD_RECOVERY')
    robinhood_user: EmailStr = Field(default=None, env='ROBINHOOD_USER')
    robinhood_pass: str = Field(default=None, env='ROBINHOOD_PASS')
    robinhood_qr: str = Field(default=None, env='ROBINHOOD_QR')
    robinhood_endpoint_auth: str = Field(default=None, env='ROBINHOOD_ENDPOINT_AUTH')
    event_app: str = Field(default='calendar', env='EVENT_APP')
    ics_url: HttpUrl = Field(default=None, env='ICS_URL')
    website: str = Field(default='vigneshrao.com', env='WEBSITE')
    wolfram_api_key: str = Field(default=None, env='WOLFRAM_API_KEY')
    maps_api: str = Field(default=None, env='MAPS_API')
    news_api: str = Field(default=None, env='NEWS_API')
    git_user: str = Field(default=None, env='GIT_USER')
    git_pass: str = Field(default=None, env='GIT_PASS')
    tv_client_key: str = Field(default=None, env='TV_CLIENT_KEY')
    tv_mac: Union[str, list] = Field(default=None, env='TV_MAC')
    root_user: str = Field(default=getpass.getuser(), env='USER')
    root_password: str = Field(default=None, env='ROOT_PASSWORD')
    vpn_username: str = Field(default=None, env='VPN_USERNAME')
    vpn_password: str = Field(default=None, env='VPN_PASSWORD')
    birthday: str = Field(default=None, env='BIRTHDAY')
    car_email: EmailStr = Field(default=None, env='CAR_EMAIL')
    car_pass: str = Field(default=None, env='CAR_PASS')
    car_pin: str = Field(default=None, regex="\\d{4}$", env='CAR_PIN')
    sensitivity: Union[float, PositiveInt] = Field(default=0.5, le=1, ge=0, env='SENSITIVITY')
    timeout: Union[float, PositiveInt] = Field(default=3, env='TIMEOUT')
    phrase_limit: Union[float, PositiveInt] = Field(default=3, env='PHRASE_LIMIT')
    bot_token: str = Field(default=None, env='BOT_TOKEN')
    bot_chat_ids: list = Field(default=[], env='BOT_CHAT_IDS')
    bot_users: list = Field(default=[], env='BOT_USERS')
    bot_voice_timeout: Union[float, PositiveInt] = Field(default=3, le=5, ge=1, env='BOT_VOICE_TIMEOUT')
    legacy_keywords: list = Field(default=['jarvis'], env='LEGACY_KEYWORDS')
    speech_synthesis_timeout: int = Field(default=3, env='SPEECH_SYNTHESIS_TIMEOUT')
    speech_synthesis_port: int = Field(default=5002, env='SPEECH_SYNTHESIS_PORT')
    save_audio_timeout: int = Field(default=0, env='SAVE_AUDIO_TIMEOUT')
    title: str = Field(default='sir', env='TITLE')
    name: str = Field(default='Vignesh', env='NAME')

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"

    if platform.system() == "Windows":
        macos = 0
    elif platform.system() == "Darwin":
        macos = 1
    else:
        raise UnsupportedOS(
            f"\n{''.join('*' for _ in range(80))}\n\n"
            "Unsupported Operating System. Currently Jarvis can run only on Mac and Windows OS.\n\n"
            "To raise an issue: https://github.com/thevickypedia/Jarvis/issues/new\n"
            "To reach out: https://vigneshrao.com/contact\n"
            f"\n{''.join('*' for _ in range(80))}\n"
        )


env = EnvConfig()

if env.event_app not in ('calendar', 'outlook'):
    raise InvalidEnvVars(
        "'EVENT_APP' can only be either 'outlook' OR 'calendar'"
    )

# Note: Pydantic validation for ICS_URL can be implemented using regex=".*ics$"
# However it will NOT work in this use case, since the type hint is HttpUrl
if env.ics_url and not env.ics_url.endswith('.ics'):
    raise InvalidEnvVars(
        "'ICS_URL' should end with .ics"
    )

if env.tv_mac and isinstance(env.tv_mac, str):
    env.tv_mac = [env.tv_mac]


class FileIO(BaseModel):
    """Loads all the files' path required/created by Jarvis.

    >>> FileIO

    """

    automation: FilePath = os.path.join('fileio', 'automation.yaml')
    tmp_automation: FilePath = os.path.join('fileio', 'tmp_automation.yaml')
    base_db: FilePath = os.path.join('fileio', 'database.db')
    task_db: FilePath = os.path.join('fileio', 'tasks.db')
    frequent: FilePath = os.path.join('fileio', 'frequent.yaml')
    location: FilePath = os.path.join('fileio', 'location.yaml')
    notes: FilePath = os.path.join('fileio', 'notes.txt')
    robinhood: FilePath = os.path.join('fileio', 'robinhood.html')
    smart_devices: FilePath = os.path.join('fileio', 'smart_devices.yaml')
    training: FilePath = os.path.join('fileio', 'training_data.yaml')
    event_script: FilePath = os.path.join('fileio', f'{env.event_app}.scpt')
    speech_synthesis_wav: FilePath = os.path.join('fileio', 'speech_synthesis.wav')
    speech_synthesis_log: FilePath = datetime.now().strftime(os.path.join('logs', 'speech_synthesis_%d-%m-%Y.log'))


class Indicators(BaseModel):
    """Loads all the mp3 files' path required by Jarvis.

    >>> Indicators

    """

    acknowledgement: FilePath = os.path.join('indicators', 'acknowledgement.mp3')
    alarm: FilePath = os.path.join('indicators', 'alarm.mp3')
    coin: FilePath = os.path.join('indicators', 'coin.mp3')
    end: FilePath = os.path.join('indicators', 'end.mp3')
    exhaust: FilePath = os.path.join('indicators', 'exhaust.mp3')
    initialize: FilePath = os.path.join('indicators', 'initialize.mp3')
    start: FilePath = os.path.join('indicators', 'start.mp3')
    tv_connect: FilePath = os.path.join('indicators', 'tv_connect.mp3')
    tv_scan: FilePath = os.path.join('indicators', 'tv_scan.mp3')
