# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Models

"""

import getpass
import os
import pathlib
import platform
import socket
import sys
from datetime import datetime
from enum import Enum
from typing import List, Union

import psutil
import pvporcupine
from packaging.version import parse as parser
from pydantic import (BaseModel, BaseSettings, DirectoryPath, EmailStr, Field,
                      FilePath, HttpUrl, PositiveFloat, PositiveInt, constr,
                      validator)

from api.rh_helper import cron_schedule
from modules.crontab.expression import CronExpression
from modules.database import database
from modules.exceptions import InvalidEnvVars, UnsupportedOS

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')


class Settings(BaseSettings):
    """Loads most common system values that do not change.

    >>> Settings

    """

    pid: PositiveInt = os.getpid()
    ram: Union[PositiveInt, PositiveFloat] = psutil.virtual_memory().total
    physical_cores: PositiveInt = psutil.cpu_count(logical=False)
    logical_cores: PositiveInt = psutil.cpu_count(logical=True)
    limited: bool = True if physical_cores < 4 else False

    if platform.system() == "Windows":
        macos: bool = False
    elif platform.system() == "Darwin":
        macos: bool = True
    else:
        raise UnsupportedOS(
            f"\n{''.join('*' for _ in range(80))}\n\n"
            "Unsupported Operating System. Currently Jarvis can run only on Mac and Windows OS.\n\n"
            "To raise an issue: https://github.com/thevickypedia/Jarvis/issues/new\n"
            "To reach out: https://vigneshrao.com/contact\n"
            f"\n{''.join('*' for _ in range(80))}\n"
        )
    legacy: bool = True if macos and parser(platform.mac_ver()[0]) < parser('10.14') else False


settings = Settings()


class EventApp(str, Enum):
    """Types of event applications supported by Jarvis.

    >>> EventApp

    """

    CALENDAR = 'calendar'
    OUTLOOK = 'outlook'


class CustomDict(BaseModel):
    """Custom links model."""

    seconds: int
    task: constr(strip_whitespace=True)

    @validator('task', allow_reuse=True)
    def check_empty_string(cls, v, values, **kwargs):  # noqa
        """Validate task field in tasks."""
        if v:
            return v
        raise ValueError('Bad value')


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
    phone_number: str = Field(default=None, regex="\\d{10}$", env='PHONE_NUMBER')
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
    event_app: EventApp = Field(default=EventApp.CALENDAR, env='EVENT_APP')
    ics_url: HttpUrl = Field(default=None, env='ICS_URL')
    website: HttpUrl = Field(default='https://vigneshrao.com', env='WEBSITE')
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
    timeout: Union[PositiveFloat, PositiveInt] = Field(default=3, env='TIMEOUT')
    phrase_limit: Union[PositiveFloat, PositiveInt] = Field(default=3, env='PHRASE_LIMIT')
    bot_token: str = Field(default=None, env='BOT_TOKEN')
    bot_chat_ids: List[int] = Field(default=[], env='BOT_CHAT_IDS')
    bot_users: List[str] = Field(default=[], env='BOT_USERS')
    bot_voice_timeout: Union[float, PositiveInt] = Field(default=3, le=5, ge=1, env='BOT_VOICE_TIMEOUT')
    wake_words: List[str] = Field(default=[pathlib.PurePath(sys.argv[0]).stem], env='WAKE_WORDS')
    speech_synthesis_timeout: int = Field(default=3, env='SPEECH_SYNTHESIS_TIMEOUT')
    speech_synthesis_host: str = Field(default=socket.gethostbyname('localhost'), env='SPEECH_SYNTHESIS_HOST')
    speech_synthesis_port: int = Field(default=5002, env='SPEECH_SYNTHESIS_PORT')
    title: str = Field(default='sir', env='TITLE')
    name: str = Field(default='Vignesh', env='NAME')
    tasks: List[CustomDict] = Field(default=[], env="TASKS")
    crontab: List[str] = Field(default=[], env='CRONTAB')
    limited: bool = Field(default=False, env='LIMITED')

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"

    # noinspection PyMethodParameters
    @validator("birthday", pre=True, allow_reuse=True)
    def parse_birthday(cls, value: str) -> Union[str, None]:
        """Validates date value to be in DD-MM format."""
        if not value:
            return
        try:
            if datetime.strptime(value, "%d-%B"):
                return value
        except ValueError:
            raise InvalidEnvVars('Format should be DD-MM')


env = EnvConfig()
env.website = env.website.lstrip(f"{env.website.scheme}://")

if not settings.legacy and env.wake_words != [pathlib.PurePath(sys.argv[0]).stem]:
    for keyword in env.wake_words:
        if not pvporcupine.KEYWORD_PATHS.get(keyword) or not os.path.isfile(pvporcupine.KEYWORD_PATHS[keyword]):
            raise InvalidEnvVars(
                f"Detecting '{keyword}' is unsupported!\n"
                f"Available keywords are: {', '.join(list(pvporcupine.KEYWORD_PATHS.keys()))}"
            )

# Note: Pydantic validation for ICS_URL can be implemented using regex=".*ics$"
# However it will NOT work in this use case, since the type hint is HttpUrl
if env.ics_url and not env.ics_url.endswith('.ics'):
    raise InvalidEnvVars(
        "'ICS_URL' should end with .ics"
    )

if env.tv_mac and isinstance(env.tv_mac, str):
    env.tv_mac = [env.tv_mac]

if env.speech_synthesis_port == env.offline_port:
    raise InvalidEnvVars(
        "Speech synthesizer and offline communicator cannot run simultaneously on the same port number."
    )

if all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
    env.crontab.append(cron_schedule(extended=True))

# Forces limited version if env var is set, otherwise it is enforced based on the number of physical cores
if env.limited:
    settings.limited = True

# Validates crontab expression if provided
for expression in env.crontab:
    CronExpression(expression)


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


fileio = FileIO()


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


indicators = Indicators()


# Create all necessary DB tables during startup
db = database.Database(database=FileIO().base_db)
db.create_table(table_name=env.event_app, columns=["info", "date"])
db.create_table(table_name="ics", columns=["info", "date"])
db.create_table(table_name="stopper", columns=["flag", "caller"])
db.create_table(table_name="restart", columns=["flag", "caller"])
db.create_table(table_name="children", columns=["meetings", "events", "crontab"])
db.create_table(table_name="vpn", columns=["state"])
