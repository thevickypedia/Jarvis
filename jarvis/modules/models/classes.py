# noinspection PyUnresolvedReferences
"""This is a space for environment variables shared across multiple modules validated using pydantic.

>>> Classes

"""

import getpass
import json
import os
import pathlib
import platform
import re
import socket
import sys
from collections import ChainMap
from datetime import datetime
from ipaddress import IPv4Address
from multiprocessing import current_process
from typing import Dict, List, Optional
from uuid import UUID

import jlrpy
import psutil
import pyttsx3
import yaml
from packaging.version import Version
from pydantic import (
    AliasChoices,
    BaseModel,
    DirectoryPath,
    EmailStr,
    Field,
    FilePath,
    HttpUrl,
    PositiveFloat,
    PositiveInt,
    constr,
    field_validator,
)
from pydantic_settings import BaseSettings
from pyhtcc import Zone

from jarvis import indicators, scripts
from jarvis.modules.exceptions import InvalidEnvVars, UnsupportedOS
from jarvis.modules.peripherals import channel_type, get_audio_devices

AUDIO_DRIVER = pyttsx3.init()

if sys.version_info.minor > 10:
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Override for python 3.10 due to lack of StrEnum."""


class SupportedPlatforms(StrEnum):
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
        interactive: bool = True
    else:
        interactive: bool = False
    pid: PositiveInt = os.getpid()
    pname: str = current_process().name
    ram: PositiveInt | PositiveFloat = psutil.virtual_memory().total
    physical_cores: PositiveInt = psutil.cpu_count(logical=False)
    logical_cores: PositiveInt = psutil.cpu_count(logical=True)
    limited: bool = True if physical_cores < 4 else False
    invoker: str = pathlib.PurePath(sys.argv[0]).stem

    os: str = platform.system()
    if os not in (
        supported_platforms.macOS,
        supported_platforms.linux,
        supported_platforms.windows,
    ):
        raise UnsupportedOS(
            f"\n{''.join('*' for _ in range(80))}\n\n"
            "Currently Jarvis can run only on Linux, Mac and Windows OS.\n\n"
            f"\n{''.join('*' for _ in range(80))}\n"
        )
    legacy: bool = False
    if os == supported_platforms.macOS and Version(platform.mac_ver()[0]) < Version(
        "10.14"
    ):
        legacy: bool = True


settings = Settings()
# Intermittently changes to Windows_NT because of pydantic
if settings.os.startswith("Windows"):
    settings.os = "Windows"


class WiFiConnection(BaseModel):
    """Wrapper to store Wi-Fi controls.

    >>> WiFiConnection

    """

    unknown_errors: int = 0
    os_errors: int = 0


class Thermostat(BaseModel):
    """Wrapper to store thermostat controls.

    >>> Thermostat

    """

    device: Optional[Zone | str] = None
    expiration: Optional[float] = None

    class Config:
        """Config to allow arbitrary types."""

        arbitrary_types_allowed = True


class VehicleConnection(BaseModel):
    """Wrapper to create and store vehicle connection.

    >>> VehicleConnection

    """

    vin: Optional[str] = None
    device_id: Optional[str] = None
    expiration: Optional[float] = None
    control: Optional[jlrpy.Vehicle] = None
    refresh_token: Optional[str | UUID] = None

    class Config:
        """Config to allow arbitrary types."""

        arbitrary_types_allowed = True


class RecognizerSettings(BaseModel):
    """Settings for speech recognition.

    >>> RecognizerSettings

    See Also:
        - energy_threshold: Minimum energy to consider for recording. Greater the value, louder the voice should be.
        - dynamic_energy_threshold: Change considerable audio energy threshold dynamically.
        - pause_threshold: Seconds of non-speaking audio before a phrase is considered complete.
        - phrase_threshold: Minimum seconds of speaking audio before it can be considered a phrase.
        - non_speaking_duration: Seconds of non-speaking audio to keep on both sides of the recording.
    """

    energy_threshold: PositiveInt = 700
    pause_threshold: PositiveInt | float = 2
    phrase_threshold: PositiveInt | float = 0.1
    dynamic_energy_threshold: bool = False
    non_speaking_duration: PositiveInt | float = 2


class TemperatureUnits(StrEnum):
    """Types of temperature units supported by Jarvis.

    >>> TemperatureUnits

    """

    METRIC: str = "metric"
    IMPERIAL: str = "imperial"


class DistanceUnits(StrEnum):
    """Types of distance units supported by Jarvis.

    >>> DistanceUnits

    """

    MILES: str = "miles"
    KILOMETERS: str = "kilometers"


class EventApp(StrEnum):
    """Types of event applications supported by Jarvis.

    >>> EventApp

    """

    CALENDAR = "calendar"
    OUTLOOK = "outlook"


class SSQuality(StrEnum):
    """Quality modes available for speech synthesis.

    >>> SSQuality

    """

    High_Quality = "high"
    Medium_Quality = "medium"
    Low_Quality = "low"


def handle_multiform(form_list: List[str]) -> List[int]:
    """Handles ignore_hours in the format 7-10.

    Args:
        form_list: Takes the split string as an argument.

    Returns:
        List[int]:
        List of hours as integers.

    Raises:
        ValueError:
        In case of validation errors.
    """
    form_list[0] = form_list[0].strip()
    form_list[1] = form_list[1].strip()
    try:
        assert form_list[0].isdigit()
        assert form_list[1].isdigit()
    except AssertionError:
        raise ValueError(
            "string format can either be start-end (7-10) or just the hour by itself (7)"
        )
    start_hour = int(form_list[0])
    end_hour = int(form_list[1])
    if start_hour <= end_hour:
        # Handle the case where the range is not wrapped around midnight
        v = list(range(start_hour, end_hour + 1))
    else:
        # Handle the case where the range wraps around midnight
        v = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
    return v


class BackgroundTask(BaseModel):
    """Custom links model."""

    seconds: int
    task: constr(strip_whitespace=True)
    ignore_hours: List[int] | List[str] | str | int | List[int | str] | None = []

    @field_validator("task", mode="before", check_fields=True)
    def check_empty_string(cls, v, values, **kwargs):  # noqa
        """Validate task field in tasks."""
        if v:
            return v
        raise ValueError("bad value")

    @field_validator("ignore_hours", check_fields=True)
    def check_hours_format(cls, v, values, **kwargs):  # noqa
        """Validate each entry in ignore hours list."""
        if not v:
            return []
        if isinstance(v, int):
            if v < 0 or v > 24:
                raise ValueError("24h format cannot be less than 0 or greater than 24")
            v = [v]
        elif isinstance(v, str):
            form_list = v.split("-")
            if len(form_list) == 1:
                try:
                    assert form_list[0].isdigit()
                except AssertionError:
                    raise ValueError(
                        "string format can either be start-end (7-10) or just the hour by itself (7)"
                    )
                else:
                    v = [int(form_list[0])]
            elif len(form_list) == 2:
                v = handle_multiform(form_list)
            else:
                raise ValueError(
                    "string format can either be start-end (7-10) or just the hour by itself (7)"
                )
        refined = []
        for multiple in v:
            if isinstance(multiple, str):
                refined.extend(
                    handle_multiform(multiple.split("-"))
                )  # comes back as a list of string
            else:
                refined.append(multiple)
        if refined:
            v = refined
        for hour in v:
            try:
                datetime.strptime(str(hour), "%H")
            except ValueError:
                raise ValueError("ignore hours should be 24H format")
        return v


class ReminderOptions(StrEnum):
    """Supported reminder options."""

    phone: str = "phone"
    email: str = "email"
    telegram: str = "telegram"
    ntfy: str = "ntfy"
    all: str = "all"


class StartupOptions(StrEnum):
    """Background threads to startup."""

    all: str = "all"
    car: str = "car"
    gpt: str = "gpt"
    thermostat: str = "thermostat"


def channel_validator(
    value: int | PositiveInt, ch_type: str
) -> int | PositiveInt | None:
    """Channel validator for camera and microphone index.

    Args:
        value: Index of the device.
        ch_type: Input/output.

    Returns:
        int | PositiveInt | None:
        Returns the validated device index.
    """
    if ch_type == "input":
        channels = channel_type.input_channels
    else:
        channels = channel_type.output_channels
    if not value:
        return
    if int(value) in list(
        map(
            lambda tag: tag["index"],
            get_audio_devices(channels),
        )
    ):
        return value
    else:
        complicated = dict(
            ChainMap(
                *list(
                    map(
                        lambda tag: {tag["index"]: tag["name"]},
                        get_audio_devices(channels),
                    )
                )
            )
        )
        raise InvalidEnvVars(f"value should be one of {complicated}")


# noinspection PyMethodParameters
class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    # Custom units
    distance_unit: DistanceUnits | None = None
    temperature_unit: TemperatureUnits | None = None

    # System config
    home: DirectoryPath = os.path.expanduser("~")
    volume: PositiveInt = 50
    limited: bool = False
    root_user: str = getpass.getuser()
    root_password: str | None = Field(
        None, validation_alias=AliasChoices("root_password", "password")
    )

    # Mute during meetings
    mute_for_meetings: bool = False

    # Built-in speaker config
    voice_name: str | None = None
    speech_rate: PositiveInt | PositiveFloat = AUDIO_DRIVER.getProperty("rate")

    # Peripheral config
    camera_index: int | PositiveInt | None = None
    speaker_index: int | PositiveInt | None = None
    microphone_index: int | PositiveInt | None = None

    # Log config
    debug: bool = False
    log_retention: int | PositiveInt = Field(10, lt=90, gt=0)

    # User add-ons
    birthday: str | None = None
    title: str = "sir"
    name: str = "Vignesh"
    website: HttpUrl | List[HttpUrl] = []
    plot_mic: bool = True
    ntfy_url: HttpUrl | None = None
    ntfy_username: str | None = None
    ntfy_password: str | None = None
    ntfy_topic: str | None = None
    notify_reminders: ReminderOptions | List[ReminderOptions] = ReminderOptions.all

    # Author specific
    author_mode: bool = False
    startup_options: StartupOptions | List[StartupOptions] = StartupOptions.all

    # Third party api config
    weather_api: str | None = None
    maps_api: str | None = None
    news_api: str | None = None

    # Machine learning model config
    ollama: bool = True
    ollama_model: str = "llama3"
    ollama_timeout: int = Field(5, le=30, ge=1)
    ollama_reuse_threshold: float | None = Field(None, le=0.9, ge=0.5)

    # Communication config
    gmail_user: EmailStr | None = None
    gmail_pass: str | None = None
    open_gmail_user: EmailStr | None = None
    open_gmail_pass: str | None = None
    recipient: EmailStr | None = None
    phone_number: str | None = Field(None, pattern="\\d{10}$")
    telegram_id: int | None = None

    # Offline communicator config
    offline_host: str = socket.gethostbyname("localhost")
    offline_port: PositiveInt = 4483
    offline_pass: str = "OfflineComm"
    workers: PositiveInt = 1

    # Calendar events and meetings config
    event_app: EventApp | None = None
    ics_url: HttpUrl | None = None
    # Set background sync limits to range: 15 minutes to 12 hours
    sync_meetings: int | None = Field(None, ge=900, le=43_200)
    sync_events: int | None = Field(None, ge=900, le=43_200)

    # Stock monitor apikey
    stock_monitor_api: Dict[EmailStr, str] = {}

    # Surveillance config
    surveillance_endpoint_auth: str | None = None
    surveillance_session_timeout: PositiveInt = 300

    # Apple devices' config
    icloud_user: EmailStr | None = None
    icloud_pass: str | None = None
    icloud_recovery: str | None = Field(None, pattern="\\d{10}$")

    # Robinhood config
    robinhood_user: EmailStr | None = None
    robinhood_pass: str | None = None
    robinhood_qr: str | None = None
    robinhood_endpoint_auth: str | None = None

    # GitHub config
    git_user: str | None = None
    git_pass: str | None = None

    # VPN Server config
    vpn_username: str | None = None
    vpn_password: str | None = None
    vpn_subdomain: str = "vpn"
    vpn_key_pair: str = "OpenVPN"
    vpn_security_group: str = "OpenVPN Access Server"
    vpn_info_file: str = Field("vpn_info.json", pattern=r".+\.json$")
    vpn_hosted_zone: str | None = None

    # Vehicle config
    car_username: EmailStr | None = None
    car_password: str | None = None
    car_pin: str | None = Field(None, pattern="\\d{4}$")

    # Thermostat config
    tcc_username: EmailStr | None = None
    tcc_password: str | None = None
    tcc_device_name: str | None = None

    # Listener config
    sensitivity: float | PositiveInt | List[float] | List[PositiveInt] = Field(
        0.5, le=1, ge=0
    )
    listener_timeout: PositiveFloat | PositiveInt = 3
    listener_phrase_limit: PositiveFloat | PositiveInt = 5
    recognizer_confidence: float | PositiveInt = Field(0, le=1, ge=0)

    # Telegram config
    bot_token: str | None = None
    bot_chat_ids: List[int] = []
    bot_users: List[str] = []
    # Telegram Webhook specific
    bot_webhook: HttpUrl | None = None
    bot_webhook_ip: IPv4Address | None = None
    bot_endpoint: str = Field("/telegram-webhook", pattern=r"^\/")
    bot_secret: str | None = Field(None, pattern="^[A-Za-z0-9_-]{1,256}$")
    bot_certificate: FilePath | None = None

    # Speech synthesis config (disabled for speaker by default)
    speech_synthesis_timeout: int = 0
    speech_synthesis_voice: str = "en-us_northern_english_male-glow_tts"
    speech_synthesis_quality: SSQuality = SSQuality.Medium_Quality
    speech_synthesis_host: str = socket.gethostbyname("localhost")
    speech_synthesis_port: PositiveInt = 5002

    # Background tasks
    weather_alert: str | datetime | None = None
    weather_alert_min: int | PositiveInt = 36
    weather_alert_max: int | PositiveInt = 104

    # WiFi config
    wifi_ssid: str | None = None
    wifi_password: str | None = None
    connection_retry: PositiveInt | PositiveFloat = 10

    # Legacy macOS config
    if settings.legacy:
        wake_words: List[str] = ["alexa"]
    else:
        wake_words: List[str] = ["jarvis"]

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        extra = "allow"

    @classmethod
    def from_env_file(cls, filename: pathlib.Path) -> "EnvConfig":
        """Create an instance of EnvConfig from environment file.

        Args:
            filename: Name of the env file.

        Returns:
            EnvConfig:
            Loads the ``EnvConfig`` model.
        """
        return cls(_env_file=filename)

    @field_validator("website", mode="after", check_fields=True)
    def parse_websites(cls, value: HttpUrl | List[HttpUrl]) -> List[HttpUrl]:
        """Validate websites."""
        if isinstance(value, list):
            return value
        return [value]

    @field_validator("notify_reminders", mode="after", check_fields=True)
    def parse_notify_reminders(
        cls, value: ReminderOptions | List[ReminderOptions]
    ) -> List[ReminderOptions]:
        """Validate reminder options."""
        if isinstance(value, list):
            if ReminderOptions.all in value:
                return [ReminderOptions.all]
            return value
        return [value]

    @field_validator("startup_options", mode="after", check_fields=True)
    def parse_startup_options(
        cls, value: StartupOptions | List[StartupOptions]
    ) -> List[StartupOptions]:
        """Validate startup options."""
        if isinstance(value, list):
            if StartupOptions.all in value:
                return [StartupOptions.all]
            return value
        return [value]

    @field_validator("microphone_index", mode="before", check_fields=True)
    def parse_microphone_index(
        cls, value: int | PositiveInt
    ) -> int | PositiveInt | None:
        """Validates microphone index."""
        return channel_validator(value, "input")

    @field_validator("speaker_index", mode="before", check_fields=True)
    def parse_speaker_index(cls, value: int | PositiveInt) -> int | PositiveInt | None:
        """Validates speaker index."""
        # TODO: Create an OS agnostic model for usage (currently the index value is unused)
        return channel_validator(value, "output")

    @field_validator("birthday", mode="before", check_fields=True)
    def parse_birthday(cls, value: str) -> str | None:
        """Validates date value to be in DD-MM format."""
        if not value:
            return
        try:
            if datetime.strptime(value, "%d-%B"):
                return value
        except ValueError:
            raise InvalidEnvVars("format should be 'DD-MM'")

    @field_validator("vpn_password", mode="before", check_fields=True)
    def validate_vpn_password(cls, v: str) -> str:
        """Validates vpn_password as per the required regex."""
        if v:
            if re.match(
                pattern=r"^(?=.*\d)(?=.*[A-Z])(?=.*[!@#$%&'()*+,-/[\]^_`{|}~<>]).+$",
                string=v,
            ):
                return v
            raise ValueError(
                r"Password must contain a digit, an Uppercase letter, and a symbol from !@#$%&'()*+,-/[\]^_`{|}~<>"
            )

    @field_validator("weather_alert", mode="before", check_fields=True)
    def parse_weather_alert(cls, value: str) -> str | None:
        """Validates date value to be in DD-MM format."""
        if not value:
            return
        try:
            # Convert datetime to string as the '07' for '%I' will pass validation but fail comparison
            if val := datetime.strptime(value, "%I:%M %p"):
                return val.strftime("%I:%M %p")
        except ValueError:
            raise InvalidEnvVars("format should be '%I:%M %p'")


def env_loader(key, default) -> EnvConfig:
    """Loads environment variables based on filetypes.

    Args:
        key: Key for the filename from where env vars have to be loaded.
        default: Default file to load env vars from.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    for _key, _value in os.environ.items():
        if _key.lower() == key.lower():
            env_file = pathlib.Path(_value)
            break
    else:
        env_file = pathlib.Path(default)
    if env_file.suffix.lower() == ".json":
        with open(env_file) as stream:
            env_data = json.load(stream)
        return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    elif env_file.suffix.lower() in (".yaml", ".yml"):
        with open(env_file) as stream:
            env_data = yaml.load(stream, yaml.FullLoader)
        return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    elif not env_file.suffix or env_file.suffix.lower() in (
        ".text",
        ".txt",
        default,
    ):
        return EnvConfig.from_env_file(env_file)
    else:
        raise ValueError(
            f"\n\tUnsupported format for 'env_file', can be one of (.json, .yaml, .yml, .txt, .text, {default})"
        )


env = env_loader(key="env_file", default=".env")


class FileIO(BaseModel):
    """Loads all the files' path required/created by Jarvis.

    >>> FileIO

    """

    # Directories
    root: DirectoryPath = os.path.realpath("fileio")

    # Speech Recognition config
    recognizer: FilePath = os.path.join(root, "recognizer.yaml")

    # Home automation
    crontab: FilePath = os.path.join(root, "crontab.yaml")
    tmp_crontab: FilePath = os.path.join(root, "tmp_crontab.yaml")
    automation: FilePath = os.path.join(root, "automation.yaml")
    tmp_automation: FilePath = os.path.join(root, "tmp_automation.yaml")
    background_tasks: FilePath = os.path.join(root, "background_tasks.yaml")
    tmp_background_tasks: FilePath = os.path.join(root, "tmp_background_tasks.yaml")
    smart_devices: FilePath = os.path.join(root, "smart_devices.yaml")
    contacts: FilePath = os.path.join(root, "contacts.yaml")

    # Alarms and Reminders
    alarms: FilePath = os.path.join(root, "alarms.yaml")
    reminders: FilePath = os.path.join(root, "reminders.yaml")

    # Simulation
    simulation: FilePath = os.path.join(root, "simulation.yaml")

    # Custom keyword-function map
    keywords: FilePath = os.path.join(root, "keywords.yaml")
    conditions: FilePath = os.path.join(root, "conditions.yaml")
    restrictions: FilePath = os.path.join(root, "restrictions.yaml")

    # Databases
    base_db: FilePath = os.path.join(root, "database.db")
    task_db: FilePath = os.path.join(root, "tasks.db")
    stock_db: FilePath = os.path.join(root, "stock.db")

    # API used
    robinhood: FilePath = os.path.join(root, "robinhood.html")
    stock_list_backup: FilePath = os.path.join(root, "stock_list_backup.yaml")

    # Future useful
    frequent: FilePath = os.path.join(root, "frequent.yaml")
    training_data: FilePath = os.path.join(root, "training_data.yaml")
    gpt_data: FilePath = os.path.join(root, "gpt_history.yaml")

    # Jarvis internal
    startup_dir: DirectoryPath = os.path.join(root, "startup")
    location: FilePath = os.path.join(root, "location.yaml")
    notes: FilePath = os.path.join(root, "notes.txt")
    processes: FilePath = os.path.join(root, "processes.yaml")

    # macOS specifics
    app_launcher: FilePath = os.path.join(scripts.__path__[0], "applauncher.scpt")
    event_script: FilePath = os.path.join(scripts.__path__[0], f"{env.event_app}.scpt")

    # Speech Synthesis
    speech_synthesis_wav: FilePath = os.path.join(root, "speech_synthesis.wav")
    # Store log file name in a variable as it is used in multiple modules with file IO
    speech_synthesis_cid: FilePath = os.path.join(root, "speech_synthesis.cid")
    speech_synthesis_log: FilePath = datetime.now().strftime(
        os.path.join("logs", "speech_synthesis_%d-%m-%Y.log")
    )

    # Secure Send
    secure_send: FilePath = os.path.join(root, "secure_send.yaml")

    # On demand storage
    uploads: DirectoryPath = os.path.join(root, "uploads")

    # Ollama
    ollama_model_file: FilePath = os.path.join(root, "Modelfile")


fileio = FileIO()


class Indicators(BaseModel):
    """Loads all the mp3 files' path required by Jarvis.

    >>> Indicators

    """

    acknowledgement: FilePath = os.path.join(
        indicators.__path__[0], "acknowledgement.mp3"
    )
    alarm: FilePath = os.path.join(indicators.__path__[0], "alarm.mp3")
    coin: FilePath = os.path.join(indicators.__path__[0], "coin.mp3")
    end: FilePath = os.path.join(indicators.__path__[0], "end.mp3")
    start: FilePath = os.path.join(indicators.__path__[0], "start.mp3")
