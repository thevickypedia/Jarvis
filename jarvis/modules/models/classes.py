# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Classes

"""

import getpass
import os
import platform
import socket
from collections import ChainMap
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

import psutil
import pyttsx3
from packaging.version import parse as parser
from pydantic import (BaseModel, BaseSettings, DirectoryPath, EmailStr, Field,
                      FilePath, HttpUrl, PositiveFloat, PositiveInt, constr,
                      validator)

from jarvis import indicators, scripts
from jarvis.modules.exceptions import InvalidEnvVars, UnsupportedOS
from jarvis.modules.peripherals import channel_type, get_audio_devices

audio_driver = pyttsx3.init()
if not os.environ.get('AWS_DEFAULT_REGION'):
    os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'  # Required when import vpn-server module


class Settings(BaseSettings):
    """Loads most common system values that do not change.

    >>> Settings

    Raises:
        UnsupportedOS:
        If the hosted device is neither macOS nor Windows.
    """

    pid: PositiveInt = os.getpid()
    runenv: str = psutil.Process(pid).parent().name()
    ram: Union[PositiveInt, PositiveFloat] = psutil.virtual_memory().total
    physical_cores: PositiveInt = psutil.cpu_count(logical=False)
    logical_cores: PositiveInt = psutil.cpu_count(logical=True)
    limited: bool = True if physical_cores < 4 else False
    wake_words: Optional[List[str]]
    bot: str = "jarvis"

    if runenv.endswith('sh'):
        ide = False
    else:
        ide = True
    os: str = platform.system()
    if os not in ["Windows", "Darwin", "Linux"]:
        raise UnsupportedOS(
            f"\n{''.join('*' for _ in range(80))}\n\n"
            "Unsupported Operating System. Currently Jarvis can run only on Mac and Windows OS.\n\n"
            "To raise an issue: https://github.com/thevickypedia/Jarvis/issues/new\n"
            "To reach out: https://vigneshrao.com/contact\n"
            f"\n{''.join('*' for _ in range(80))}\n"
        )
    legacy: bool = True if os == "Darwin" and parser(platform.mac_ver()[0]) < parser('10.14') else False


settings = Settings()


class Sensitivity(float or PositiveInt, Enum):
    """Allowed values for sensitivity.

    >>> Sensitivity

    """

    sensitivity: Union[float, PositiveInt]


class RecognizerSettings(BaseSettings):
    """Settings for speech recognition.

    >>> RecognizerSettings

    """

    energy_threshold: PositiveInt = 700
    pause_threshold: Union[PositiveInt, float] = 2
    phrase_threshold: Union[PositiveInt, float] = 0.1
    dynamic_energy_threshold: bool = False
    non_speaking_duration: Union[PositiveInt, float] = 2


class EventApp(str, Enum):
    """Types of event applications supported by Jarvis.

    >>> EventApp

    """

    CALENDAR = 'calendar'
    OUTLOOK = 'outlook'


class SSQuality(str, Enum):
    """Quality modes available for speech synthesis.

    >>> SSQuality

    """

    High_Quality = 'high'
    Medium_Quality = 'medium'
    Low_Quality = 'low'


class BackgroundTask(BaseModel):
    """Custom links model."""

    seconds: int
    task: constr(strip_whitespace=True)
    ignore_hours: Optional[List[int]] = []

    @validator('task', allow_reuse=True)
    def check_empty_string(cls, v, values, **kwargs):  # noqa
        """Validate task field in tasks."""
        if v:
            return v
        raise ValueError('bad value')

    @validator('ignore_hours', allow_reuse=True)
    def check_hours_format(cls, v, values, **kwargs):  # noqa
        """Validate each entry in ignore hours list."""
        if not v:
            return []
        for hour in v:
            try:
                datetime.strptime(str(hour), '%H')
            except ValueError:
                raise ValueError('ignore hours should be a list of integers in 24H format')
        return v


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    # System config
    home: DirectoryPath = Field(default=os.path.expanduser('~'), env='HOME')
    volume: PositiveInt = Field(default=50, env='VOLUME')
    limited: bool = Field(default=None, env='LIMITED')
    root_user: str = Field(default=getpass.getuser(), env='USER')
    root_password: str = Field(default=None, env='ROOT_PASSWORD')

    # Built-in speaker config
    voice_name: str = Field(default=None, env='VOICE_NAME')
    voice_rate: Union[PositiveInt, PositiveFloat] = Field(default=audio_driver.getProperty("rate"), env='VOICE_RATE')

    # Peripheral config
    camera_index: Union[int, PositiveInt] = Field(default=None, ge=0, env='CAMERA_INDEX')
    speaker_index: Union[int, PositiveInt] = Field(default=None, ge=0, env='SPEAKER_INDEX')
    microphone_index: Union[int, PositiveInt] = Field(default=None, ge=0, env='MICROPHONE_INDEX')

    # Log config
    debug: bool = Field(default=False, env='DEBUG')
    log_retention: Union[int, PositiveInt] = Field(default=10, gt=0, env='LOG_RETENTION')

    # User add-ons
    birthday: str = Field(default=None, env='BIRTHDAY')
    title: str = Field(default='sir', env='TITLE')
    name: str = Field(default='Vignesh', env='NAME')
    website: HttpUrl = Field(default='https://vigneshrao.com', env='WEBSITE')
    plot_mic: bool = Field(default=True, env='PLOT_MIC')
    tunnel: bool = Field(default=False, env='TUNNEL')

    # Third party api config
    weather_api: str = Field(default=None, env='WEATHER_API')
    wolfram_api_key: str = Field(default=None, env='WOLFRAM_API_KEY')
    maps_api: str = Field(default=None, env='MAPS_API')
    news_api: str = Field(default=None, env='NEWS_API')

    # Communication config
    gmail_user: EmailStr = Field(default=None, env='GMAIL_USER')
    gmail_pass: str = Field(default=None, env='GMAIL_PASS')
    alt_gmail_user: EmailStr = Field(default=None, env='ALT_GMAIL_USER')
    alt_gmail_pass: str = Field(default=None, env='ALT_GMAIL_PASS')
    open_gmail_user: EmailStr = Field(default=None, env='OPEN_GMAIL_USER')
    open_gmail_pass: str = Field(default=None, env='OPEN_GMAIL_PASS')
    recipient: EmailStr = Field(default=None, env='RECIPIENT')
    phone_number: str = Field(default=None, regex="\\d{10}$", env='PHONE_NUMBER')

    # Offline communicator config
    offline_host: str = Field(default=socket.gethostbyname('localhost'), env='OFFLINE_HOST')
    offline_port: PositiveInt = Field(default=4483, env='OFFLINE_PORT')
    offline_pass: str = Field(default='OfflineComm', env='OFFLINE_PASS')
    workers: PositiveInt = Field(default=1, env='WORKERS')

    # Calendar events and meetings config
    event_app: EventApp = Field(default=EventApp.CALENDAR, env='EVENT_APP')
    ics_url: HttpUrl = Field(default=None, env='ICS_URL')
    sync_meetings: PositiveInt = Field(default=3_600, env='SYNC_MEETINGS')
    sync_events: PositiveInt = Field(default=3_600, env='SYNC_EVENTS')

    # Surveillance config
    surveillance_endpoint_auth: str = Field(default=None, env='SURVEILLANCE_ENDPOINT_AUTH')
    surveillance_session_timeout: PositiveInt = Field(default=300, env='SURVEILLANCE_SESSION_TIMEOUT')

    # Apple devices' config
    icloud_user: EmailStr = Field(default=None, env='ICLOUD_USER')
    icloud_pass: str = Field(default=None, env='ICLOUD_PASS')
    icloud_recovery: str = Field(default=None, regex="\\d{10}$", env='ICLOUD_RECOVERY')

    # Robinhood config
    robinhood_user: EmailStr = Field(default=None, env='ROBINHOOD_USER')
    robinhood_pass: str = Field(default=None, env='ROBINHOOD_PASS')
    robinhood_qr: str = Field(default=None, env='ROBINHOOD_QR')
    robinhood_endpoint_auth: str = Field(default=None, env='ROBINHOOD_ENDPOINT_AUTH')

    # GitHub config
    git_user: str = Field(default=None, env='GIT_USER')
    git_pass: str = Field(default=None, env='GIT_PASS')

    # VPN Server config
    vpn_username: str = Field(default=None, env='VPN_USERNAME')
    vpn_password: str = Field(default=None, env='VPN_PASSWORD')
    vpn_domain: str = Field(default=None, env='VPN_DOMAIN')
    vpn_record_name: str = Field(default=None, env='VPN_RECORD_NAME')

    # Vehicle config
    car_email: EmailStr = Field(default=None, env='CAR_EMAIL')
    car_pass: str = Field(default=None, env='CAR_PASS')
    car_pin: str = Field(default=None, regex="\\d{4}$", env='CAR_PIN')

    # Garage door config
    myq_username: EmailStr = Field(default=None, env='MYQ_USERNAME')
    myq_password: str = Field(default=None, env='MYQ_PASSWORD')

    # Listener config
    sensitivity: Union[Sensitivity, List[Sensitivity]] = Field(default=0.5, le=1, ge=0, env='SENSITIVITY')
    timeout: Union[PositiveFloat, PositiveInt] = Field(default=3, env='TIMEOUT')
    phrase_limit: Union[PositiveFloat, PositiveInt] = Field(default=None, env='PHRASE_LIMIT')
    recognizer_settings: RecognizerSettings = Field(default=None, env='RECOGNIZER_SETTINGS')

    # Telegram config
    bot_token: str = Field(default=None, env='BOT_TOKEN')
    bot_chat_ids: List[int] = Field(default=[], env='BOT_CHAT_IDS')
    bot_users: List[str] = Field(default=[], env='BOT_USERS')

    # Speech synthesis config
    speech_synthesis_timeout: int = Field(default=3, env='SPEECH_SYNTHESIS_TIMEOUT')
    speech_synthesis_voice: str = Field(default='en-us_northern_english_male-glow_tts', env='SPEECH_SYNTHESIS_VOICE')
    speech_synthesis_quality: SSQuality = Field(default=SSQuality.Medium_Quality, env='SPEECH_SYNTHESIS_QUALITY')
    speech_synthesis_host: str = Field(default=socket.gethostbyname('localhost'), env='SPEECH_SYNTHESIS_HOST')
    speech_synthesis_port: PositiveInt = Field(default=5002, env='SPEECH_SYNTHESIS_PORT')

    # Background tasks
    crontab: List[str] = Field(default=[], env='CRONTAB')  # User input is gathered from fileio/crontab.yaml

    # WiFi config
    wifi_ssid: str = Field(default=None, env='WIFI_SSID')
    wifi_password: str = Field(default=None, env='WIFI_PASSWORD')
    connection_retry: Union[PositiveInt, PositiveFloat] = Field(default=10, env='CONNECTION_RETRY')

    # Legacy macOS config
    if settings.legacy:
        wake_words: List[str] = Field(default=['alexa'], env='WAKE_WORDS')
    else:
        wake_words: List[str] = Field(default=['jarvis'], env='WAKE_WORDS')

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        env_file = ".env"

    # noinspection PyMethodParameters
    @validator("microphone_index", pre=True, allow_reuse=True)
    def parse_microphone_index(cls, value: Union[int, PositiveInt]) -> Union[int, PositiveInt, None]:
        """Validates microphone index."""
        if not value:
            return
        if int(value) in list(map(lambda tag: tag['index'], get_audio_devices(channels=channel_type.input_channels))):
            return value
        else:
            complicated = dict(ChainMap(*list(map(lambda tag: {tag['index']: tag['name']},
                                                  get_audio_devices(channels=channel_type.input_channels)))))
            raise InvalidEnvVars(f"value should be one of {complicated}")

    # noinspection PyMethodParameters
    @validator("speaker_index", pre=True, allow_reuse=True)
    def parse_speaker_index(cls, value: Union[int, PositiveInt]) -> Union[int, PositiveInt, None]:
        """Validates speaker index."""
        # TODO: Create an OS agnostic model for usage
        if not value:
            return
        if int(value) in list(map(lambda tag: tag['index'], get_audio_devices(channels=channel_type.output_channels))):
            return value
        else:
            complicated = dict(ChainMap(*list(map(lambda tag: {tag['index']: tag['name']},
                                                  get_audio_devices(channels=channel_type.output_channels)))))
            raise InvalidEnvVars(f"value should be one of {complicated}")

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
            raise InvalidEnvVars('format should be DD-MM')


env = EnvConfig()


class FileIO(BaseModel):
    """Loads all the files' path required/created by Jarvis.

    >>> FileIO

    """

    # Directories
    root: DirectoryPath = os.path.realpath('fileio')

    # Home automation
    automation: FilePath = os.path.join('fileio', 'automation.yaml')
    tmp_automation: FilePath = os.path.join('fileio', 'tmp_automation.yaml')
    background_tasks: FilePath = os.path.join('fileio', 'background_tasks.yaml')
    tmp_background_tasks: FilePath = os.path.join('fileio', 'tmp_background_tasks.yaml')
    smart_devices: FilePath = os.path.join('fileio', 'smart_devices.yaml')
    contacts: FilePath = os.path.join('fileio', 'contacts.yaml')

    # Simulation
    simulation: FilePath = os.path.join('fileio', 'simulation.yaml')

    # Databases
    base_db: FilePath = os.path.join('fileio', 'database.db')
    task_db: FilePath = os.path.join('fileio', 'tasks.db')
    stock_db: FilePath = os.path.join('fileio', 'stock.db')

    # API used
    stock_list_backup: FilePath = os.path.join('fileio', 'stock_list_backup.yaml')
    robinhood: FilePath = os.path.join('fileio', 'robinhood.html')

    # Future useful
    frequent: FilePath = os.path.join('fileio', 'frequent.yaml')
    training_data: FilePath = os.path.join('fileio', 'training_data.yaml')

    # Jarvis internal
    location: FilePath = os.path.join('fileio', 'location.yaml')
    notes: FilePath = os.path.join('fileio', 'notes.txt')
    processes: FilePath = os.path.join('fileio', 'processes.yaml')

    # macOS specifics
    app_launcher: FilePath = os.path.join(scripts.__path__[0], 'applauncher.scpt')
    event_script: FilePath = os.path.join(scripts.__path__[0], f'{env.event_app}.scpt')

    # Speech Synthesis
    speech_synthesis_wav: FilePath = os.path.join('fileio', 'speech_synthesis.wav')
    # Store log file name in a variable as it is used in multiple modules with file IO
    speech_synthesis_log: FilePath = datetime.now().strftime(os.path.join('logs', 'speech_synthesis_%d-%m-%Y.log'))
    speech_synthesis_id: FilePath = datetime.now().strftime(os.path.join('fileio', 'speech_synthesis_%d-%m-%Y.cid'))


fileio = FileIO()


class Indicators(BaseModel):
    """Loads all the mp3 files' path required by Jarvis.

    >>> Indicators

    """

    acknowledgement: FilePath = os.path.join(indicators.__path__[0], 'acknowledgement.mp3')
    alarm: FilePath = os.path.join(indicators.__path__[0], 'alarm.mp3')
    coin: FilePath = os.path.join(indicators.__path__[0], 'coin.mp3')
    end: FilePath = os.path.join(indicators.__path__[0], 'end.mp3')
    exhaust: FilePath = os.path.join(indicators.__path__[0], 'exhaust.mp3')
    start: FilePath = os.path.join(indicators.__path__[0], 'start.mp3')
    tv_connect: FilePath = os.path.join(indicators.__path__[0], 'tv_connect.mp3')
    tv_scan: FilePath = os.path.join(indicators.__path__[0], 'tv_scan.mp3')
