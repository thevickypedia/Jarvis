# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Classes

"""

import getpass
import importlib
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
from collections import ChainMap
from datetime import datetime
from enum import Enum
from multiprocessing import current_process
from threading import Thread
from typing import Callable, Dict, List, NoReturn, Optional, Union
from uuid import UUID

import psutil
import pyttsx3
from packaging.version import Version
from pydantic import (BaseModel, BaseSettings, DirectoryPath, EmailStr, Field,
                      FilePath, HttpUrl, PositiveFloat, PositiveInt, constr,
                      validator)

from jarvis import indicators, scripts
from jarvis.modules.crontab.expression import CronExpression
from jarvis.modules.exceptions import (InvalidEnvVars, SegmentationError,
                                       UnsupportedOS)
from jarvis.modules.peripherals import channel_type, get_audio_devices

module: Dict[str, pyttsx3.Engine] = {}
if not os.environ.get('AWS_DEFAULT_REGION'):
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-2'  # Required when vpn-server is imported


class SupportedPlatforms(str, Enum):
    """Supported operating systems."""

    windows: str = "Windows"
    macOS: str = "Darwin"
    linux: str = "Linux"


supported_platforms = SupportedPlatforms


class Settings(BaseModel):
    """Loads most common system values that do not change.

    >>> Settings

    Raises:
        UnsupportedOS:
        If the hosted device is other than Linux, macOS or Windows.
    """

    if sys.stdin.isatty():
        interactive = True
    else:
        interactive = False
    pid: PositiveInt = os.getpid()
    pname: str = current_process().name
    ram: Union[PositiveInt, PositiveFloat] = psutil.virtual_memory().total
    physical_cores: PositiveInt = psutil.cpu_count(logical=False)
    logical_cores: PositiveInt = psutil.cpu_count(logical=True)
    limited: bool = True if physical_cores < 4 else False
    invoker: str = pathlib.PurePath(sys.argv[0]).stem

    os: str = platform.system()
    if os not in (supported_platforms.macOS, supported_platforms.linux, supported_platforms.windows):
        raise UnsupportedOS(
            f"\n{''.join('*' for _ in range(80))}\n\n"
            "Currently Jarvis can run only on Linux, Mac and Windows OS.\n\n"
            f"\n{''.join('*' for _ in range(80))}\n"
        )
    legacy = True if os == supported_platforms.macOS and Version(platform.mac_ver()[0]) < Version('10.14') else False


settings = Settings()
# Intermittently changes to Windows_NT because of pydantic
if settings.os.startswith('Windows'):
    settings.os = "Windows"


class VehicleAuthorization(BaseModel):
    """Wrapper to store vehicle authorization."""

    device_id: Optional[str] = None
    expiration: Optional[float] = None
    refresh_token: Optional[Union[str, UUID]] = None


class VehicleConnection(BaseModel):
    """Module to create vehicle connection."""

    vin: Optional[str] = None
    connection: Optional[Callable] = None


def import_module() -> NoReturn:
    """Instantiates pyttsx3 after importing ``nsss`` drivers beforehand."""
    if settings.os == "Darwin":
        importlib.import_module("pyttsx3.drivers.nsss")
    module['pyttsx3'] = pyttsx3.init()


def dynamic_rate() -> int:
    """Speech rate based on the Operating System."""
    if settings.os == "Linux":
        return 1
    return 200


def test_and_load_audio_driver() -> pyttsx3.Engine:
    """Get audio driver by instantiating pyttsx3.

    Returns:
        pyttsx3.Engine:
        Audio driver.
    """
    try:
        subprocess.run([shutil.which(cmd="python"), "-c", "import pyttsx3; pyttsx3.init()"], check=True)
    except subprocess.CalledProcessError as error:
        if error.returncode == -11:  # Segmentation fault error code
            if settings.pname == "JARVIS":
                print(f"\033[91mERROR:{'':<6}Segmentation fault when loading audio driver "
                      "(interrupted by signal 11: SIGSEGV)\033[0m")
                print(f"\033[93mWARNING:{'':<4}Trying alternate solution...\033[0m")
            thread = Thread(target=import_module)
            thread.start()
            thread.join(timeout=10)
            if module.get('pyttsx3'):
                if settings.pname == "JARVIS":
                    print(f"\033[92mINFO:{'':<7}Instantiated audio driver successfully\033[0m")
                return module['pyttsx3']
            else:
                raise SegmentationError(
                    "Segmentation fault when loading audio driver (interrupted by signal 11: SIGSEGV)"
                )
        else:
            return pyttsx3.init()
    else:
        return pyttsx3.init()


try:
    audio_driver = test_and_load_audio_driver()
except (SegmentationError, Exception):  # resolve to speech-synthesis
    audio_driver = None


class Sensitivity(float or PositiveInt, Enum):
    """Allowed values for sensitivity.

    >>> Sensitivity

    """

    sensitivity: Union[float, PositiveInt]


class RecognizerSettings(BaseModel):
    """Settings for speech recognition.

    >>> RecognizerSettings

    """

    energy_threshold: PositiveInt = 700
    pause_threshold: Union[PositiveInt, float] = 2
    phrase_threshold: Union[PositiveInt, float] = 0.1
    dynamic_energy_threshold: bool = False
    non_speaking_duration: Union[PositiveInt, float] = 2


class TemperatureUnits(str, Enum):
    """Types of temperature units supported by Jarvis.

    >>> TemperatureUnits

    """

    METRIC: str = 'metric'
    IMPERIAL: str = 'imperial'


class DistanceUnits(str, Enum):
    """Types of distance units supported by Jarvis.

    >>> DistanceUnits

    """

    MILES: str = 'miles'
    KILOMETERS: str = 'kilometers'


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
    ignore_hours: Union[Optional[List[int]], Optional[str], Optional[int]] = []

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
        if isinstance(v, int):
            if v < 0 or v > 24:
                raise ValueError
            v = [v]
        elif isinstance(v, str):
            form_list = v.split('-')
            if len(form_list) == 1:
                if form_list[0].isdigit():
                    v = [int(form_list[0])]
                else:
                    raise ValueError('string format can either be start-end (7-10) or just the hour by itself (7)')
            elif len(form_list) == 2:
                assert form_list[0].isdigit()
                assert form_list[1].isdigit()
                start = int(form_list[0])
                end = int(form_list[1])
                if end < 24:
                    end += 1
                if start < end:
                    v = [i for i in range(start, end)]
                else:
                    v = [i for i in range(start, 24)] + [i for i in range(0, end)]
                if int(form_list[1]) == 24:
                    v.append(0)
            else:
                raise ValueError
        for hour in v:
            try:
                datetime.strptime(str(hour), '%H')
            except ValueError:
                raise ValueError('ignore hours should be 24H format')
        return v


class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    # Custom units
    distance_unit: DistanceUnits = Field(default=None, env='DISTANCE_UNIT')
    temperature_unit: TemperatureUnits = Field(default=None, env='TEMPERATURE_UNIT')

    # System config
    home: DirectoryPath = Field(default=os.path.expanduser('~'), env='HOME')
    volume: PositiveInt = Field(default=50, env='VOLUME')
    limited: bool = Field(default=None, env='LIMITED')
    root_user: str = Field(default=getpass.getuser(), env='USER')
    root_password: str = Field(default=None, env='ROOT_PASSWORD')

    # Mute during meetings
    mute_for_meetings: bool = Field(default=False, env='MUTE_FOR_MEETINGS')

    # Built-in speaker config
    voice_name: str = Field(default=None, env='VOICE_NAME')
    _rate = audio_driver.getProperty("rate") if audio_driver else dynamic_rate()
    speech_rate: Union[PositiveInt, PositiveFloat] = Field(default=_rate, env='SPEECH_RATE')

    # Peripheral config
    camera_index: Union[int, PositiveInt] = Field(default=None, ge=0, env='CAMERA_INDEX')
    speaker_index: Union[int, PositiveInt] = Field(default=None, ge=0, env='SPEAKER_INDEX')
    microphone_index: Union[int, PositiveInt] = Field(default=None, ge=0, env='MICROPHONE_INDEX')

    # Log config
    debug: bool = Field(default=False, env='DEBUG')
    log_retention: Union[int, PositiveInt] = Field(default=10, lt=90, gt=0, env='LOG_RETENTION')

    # User add-ons
    birthday: str = Field(default=None, env='BIRTHDAY')
    title: str = Field(default='sir', env='TITLE')
    name: str = Field(default='Vignesh', env='NAME')
    website: HttpUrl = Field(default='https://vigneshrao.com', env='WEBSITE')
    plot_mic: bool = Field(default=True, env='PLOT_MIC')

    # Author specific
    author_mode: bool = Field(default=False, env='AUTHOR_MODE')

    # Third party api config
    weather_api: str = Field(default=None, env='WEATHER_API')
    maps_api: str = Field(default=None, env='MAPS_API')
    news_api: str = Field(default=None, env='NEWS_API')
    openai_api: str = Field(default=None, env='OPENAI_API')
    openai_reuse_threshold: float = Field(default=None, ge=0.5, le=0.9, env='OPENAI_REUSE_THRESHOLD')

    # Communication config
    gmail_user: EmailStr = Field(default=None, env='GMAIL_USER')
    gmail_pass: str = Field(default=None, env='GMAIL_PASS')
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
    # Set background sync limits to range: 15 minutes to 12 hours
    sync_meetings: int = Field(default=None, ge=900, le=43_200, env='SYNC_MEETINGS')
    sync_events: int = Field(default=None, ge=900, le=43_200, env='SYNC_EVENTS')

    # Stock monitor apikey
    stock_monitor_api: Dict[EmailStr, str] = Field(default={}, env="STOCK_MONITOR_API")

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
    listener_timeout: Union[PositiveFloat, PositiveInt] = Field(default=3, env='LISTENER_TIMEOUT')
    listener_phrase_limit: Union[PositiveFloat, PositiveInt] = Field(default=None, env='LISTENER_PHRASE_LIMIT')
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
    crontab: List[CronExpression] = Field(default=[], env='CRONTAB')
    weather_alert: Union[str, datetime] = Field(default=None, env='WEATHER_ALERT')
    weather_alert_min: Union[int, PositiveInt] = Field(default=36, env='WEATHER_ALERT_MIN')
    weather_alert_max: Union[int, PositiveInt] = Field(default=104, env='WEATHER_ALERT_MAX')

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
            raise InvalidEnvVars("format should be 'DD-MM'")

    # noinspection PyMethodParameters
    @validator("weather_alert", pre=True, allow_reuse=True)
    def parse_weather_alert(cls, value: str) -> Union[str, None, datetime]:
        """Validates date value to be in DD-MM format."""
        if not value:
            return
        try:
            # Convert datetime to string as the '07' for '%I' will pass validation but fail comparison
            if val := datetime.strptime(value, '%I:%M %p'):
                return val.strftime('%I:%M %p')
        except ValueError:
            raise InvalidEnvVars("format should be '%I:%M %p'")


env = EnvConfig()


class FileIO(BaseModel):
    """Loads all the files' path required/created by Jarvis.

    >>> FileIO

    """

    # Directories
    root: DirectoryPath = os.path.realpath('fileio')

    # Home automation
    automation: FilePath = os.path.join(root, 'automation.yaml')
    tmp_automation: FilePath = os.path.join(root, 'tmp_automation.yaml')
    background_tasks: FilePath = os.path.join(root, 'background_tasks.yaml')
    tmp_background_tasks: FilePath = os.path.join(root, 'tmp_background_tasks.yaml')
    smart_devices: FilePath = os.path.join(root, 'smart_devices.yaml')
    contacts: FilePath = os.path.join(root, 'contacts.yaml')

    # Simulation
    simulation: FilePath = os.path.join(root, 'simulation.yaml')

    # Custom keyword-function map
    keywords: FilePath = os.path.join(root, 'keywords.yaml')
    conditions: FilePath = os.path.join(root, 'conditions.yaml')

    # Databases
    base_db: FilePath = os.path.join(root, 'database.db')
    task_db: FilePath = os.path.join(root, 'tasks.db')
    stock_db: FilePath = os.path.join(root, 'stock.db')

    # API used
    stock_list_backup: FilePath = os.path.join(root, 'stock_list_backup.yaml')
    robinhood: FilePath = os.path.join(root, 'robinhood.html')

    # Future useful
    frequent: FilePath = os.path.join(root, 'frequent.yaml')
    training_data: FilePath = os.path.join(root, 'training_data.yaml')
    gpt_data: FilePath = os.path.join(root, 'gpt_history.yaml')

    # Jarvis internal
    location: FilePath = os.path.join(root, 'location.yaml')
    notes: FilePath = os.path.join(root, 'notes.txt')
    processes: FilePath = os.path.join(root, 'processes.yaml')

    # macOS specifics
    app_launcher: FilePath = os.path.join(scripts.__path__[0], 'applauncher.scpt')
    event_script: FilePath = os.path.join(scripts.__path__[0], f'{env.event_app}.scpt')

    # Speech Synthesis
    speech_synthesis_wav: FilePath = os.path.join(root, 'speech_synthesis.wav')
    # Store log file name in a variable as it is used in multiple modules with file IO
    speech_synthesis_log: FilePath = datetime.now().strftime(os.path.join('logs', 'speech_synthesis_%d-%m-%Y.log'))
    speech_synthesis_id: FilePath = datetime.now().strftime(os.path.join(root, 'speech_synthesis_%d-%m-%Y.cid'))

    # Secure Send
    secure_send: FilePath = os.path.join(root, 'secure_send.yaml')


fileio = FileIO()


class Indicators(BaseModel):
    """Loads all the mp3 files' path required by Jarvis.

    >>> Indicators

    """

    acknowledgement: FilePath = os.path.join(indicators.__path__[0], 'acknowledgement.mp3')
    alarm: FilePath = os.path.join(indicators.__path__[0], 'alarm.mp3')
    coin: FilePath = os.path.join(indicators.__path__[0], 'coin.mp3')
    end: FilePath = os.path.join(indicators.__path__[0], 'end.mp3')
    start: FilePath = os.path.join(indicators.__path__[0], 'start.mp3')
