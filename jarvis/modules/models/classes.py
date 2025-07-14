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
from datetime import datetime
from ipaddress import IPv4Address
from multiprocessing import current_process
from typing import Dict, List, NoReturn, Optional
from uuid import UUID

import dotenv
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
from jarvis.modules.models import enums, env_file, squire

AUDIO_DRIVER = pyttsx3.init()
platform_info: List[str] = platform.platform(terse=True).split("-")


class Settings(BaseModel):
    """Loads most common system values that do not change.

    >>> Settings

    Raises:
        UnsupportedOS:
        If the hosted device is other than Linux, macOS or Windows.
    """

    interactive: bool = sys.stdin.isatty()
    pid: PositiveInt = os.getpid()
    pname: str = current_process().name
    ram: PositiveInt | PositiveFloat = psutil.virtual_memory().total
    disk: PositiveInt | PositiveFloat = psutil.disk_usage("/").total
    physical_cores: PositiveInt = psutil.cpu_count(logical=False)
    logical_cores: PositiveInt = psutil.cpu_count(logical=True)
    limited: bool = True if physical_cores < 4 else False
    invoker: str = pathlib.PurePath(sys.argv[0]).stem

    device: str = re.sub(r"\..*", "", platform.node() or socket.gethostname())
    os_name: str = platform_info[0]
    os_version: str = platform_info[1]
    distro: str = Field(default=squire.get_distributor_info_linux())
    weather_onecall: bool = False

    os: str = platform.system()
    if os == enums.SupportedPlatforms.macOS and Version(
        platform.mac_ver()[0]
    ) < Version("10.14"):
        raise DeprecationWarning(
            f"\nmacOS {platform.mac_ver()[0]} has been deprecated\n"
            f"Please upgrade to 10.14 or above to continue using Jarvis",
        )


settings = Settings()
# Intermittently changes to Windows_NT because of pydantic
if settings.os.startswith(enums.SupportedPlatforms.windows.value):
    settings.os = enums.SupportedPlatforms.windows.value

if settings.os not in (
    enums.SupportedPlatforms.macOS,
    enums.SupportedPlatforms.linux,
    enums.SupportedPlatforms.windows,
):
    raise UnsupportedOS(
        f"\n{''.join('*' for _ in range(80))}\n\n"
        "Currently Jarvis can run only on Linux, Mac and Windows OS.\n\n"
        f"\n{''.join('*' for _ in range(80))}\n"
    )


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


# noinspection PyMethodParameters
class BackgroundTask(BaseModel):
    """Custom links model."""

    seconds: int
    task: constr(strip_whitespace=True)
    ignore_hours: List[int] | List[str] | str | int | List[int | str] | None = Field(
        default_factory=list
    )

    @field_validator("task", mode="before", check_fields=True)
    def check_empty_string(cls, value):
        """Validate task field in tasks."""
        if value:
            return value
        raise ValueError("bad value")

    @field_validator("ignore_hours", check_fields=True)
    def check_hours_format(cls, value) -> List[int]:
        """Validate each entry in ignore hours list."""
        if not value:
            return []
        return squire.parse_ignore_hours(value)


# noinspection PyMethodParameters
class EnvConfig(BaseSettings):
    """Configure all env vars and validate using ``pydantic`` to share across modules.

    >>> EnvConfig

    """

    # Custom units
    distance_unit: enums.DistanceUnits | None = None
    temperature_unit: enums.TemperatureUnits | None = None

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
    speech_rate: PositiveInt | PositiveFloat = Field(
        default=AUDIO_DRIVER.getProperty("rate")
    )

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
    website: HttpUrl | List[HttpUrl] = Field(default_factory=list)
    plot_mic: bool = True
    ntfy_url: HttpUrl | None = None
    ntfy_username: str | None = None
    ntfy_password: str | None = None
    ntfy_topic: str | None = None
    notify_reminders: enums.ReminderOptions | List[
        enums.ReminderOptions
    ] = enums.ReminderOptions.all

    # Author specific
    author_mode: bool = False
    startup_options: enums.StartupOptions | List[
        enums.StartupOptions
    ] = enums.StartupOptions.none

    # Third party api config
    weather_apikey: str | None = None
    # https://openweathermap.org/price has different URLs for different plans
    # This parameter gives the freedom to choose between different endpoints
    # Jarvis' code base currently follows: https://openweathermap.org/current
    # Legacy: "https://api.openweathermap.org/data/2.5/onecall?"
    weather_endpoint: HttpUrl = "https://api.openweathermap.org/data/2.5/weather"
    maps_apikey: str | None = None
    news_apikey: str | None = None

    # Machine learning model config
    ollama_model: str = "llama3.2"
    ollama_server: HttpUrl | None = None
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
    event_app: enums.EventApp | None = None
    ics_url: HttpUrl | None = None
    # Set background sync limits to range: 15 minutes to 12 hours
    sync_meetings: int | None = Field(None, ge=900, le=43_200)
    sync_events: int | None = Field(None, ge=900, le=43_200)

    # Stock monitor apikey
    stock_monitor_api: Dict[EmailStr, str] = Field(default_factory=dict)

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
    git_token: str | None = None

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
    porcupine_key: str | None = None
    listener_timeout: PositiveFloat | PositiveInt = 3
    listener_phrase_limit: PositiveFloat | PositiveInt = 5
    listener_spectrum_key: str | None = None
    recognizer_confidence: float | PositiveInt = Field(0, le=1, ge=0)

    # Telegram config
    bot_token: str | None = None
    bot_chat_ids: List[int] = Field(default_factory=list)
    bot_users: List[str] = Field(default_factory=list)
    # Telegram Webhook specific
    bot_webhook: HttpUrl | None = None
    bot_webhook_ip: IPv4Address | None = None
    bot_endpoint: str = Field("/telegram-webhook", pattern=r"^\/")
    bot_secret: str | None = Field(None, pattern="^[A-Za-z0-9_-]{1,256}$")
    bot_certificate: FilePath | None = None

    # Speech synthesis config (disabled for speaker by default)
    speech_synthesis_timeout: int = 0
    speech_synthesis_voice: str = "en-us_northern_english_male-glow_tts"
    speech_synthesis_quality: enums.SSQuality = enums.SSQuality.Medium
    speech_synthesis_api: HttpUrl | None = None

    # Background tasks
    weather_alert: str | datetime | None = None
    weather_alert_min: int | PositiveInt = 36
    weather_alert_max: int | PositiveInt = 104

    # WiFi config
    wifi_ssid: str | None = None
    wifi_password: str | None = None
    connection_retry: PositiveInt | PositiveFloat = 10

    wake_words: List[str] = Field(["jarvis"])

    class Config:
        """Environment variables configuration."""

        env_prefix = ""
        extra = "allow"

    @classmethod
    def from_env_file(cls, filename: pathlib.Path) -> "EnvConfig":
        """Create an instance of EnvConfig from environment file.

        Args:
            filename: Name of the env file.

        See Also:
            - Loading environment variables from files are an additional feature.
            - Both the system's and session's env vars are processed by default.

        Returns:
            EnvConfig:
            Loads the ``EnvConfig`` model.
        """
        # noinspection PyArgumentList
        return cls(_env_file=filename)

    @field_validator("weather_endpoint", mode="after", check_fields=True)
    def validate_weather_endpoint(cls, value: HttpUrl) -> HttpUrl:
        """Validates the weather endpoint."""
        pattern = r"^https:\/\/api\.openweathermap\.org\/data\/(2\.5|3\.0)\/(weather|onecall)$"
        try:
            assert re.match(pattern, str(value))
            settings.weather_onecall = str(value).endswith("onecall") or str(
                value
            ).endswith("onecall/")
        except AssertionError:
            issue_link = "https://github.com/thevickypedia/Jarvis/issues/new/choose"
            raise ValueError(
                "\n\nInvalid URL:\n"
                "\t1. The URL scheme must be 'https'\n"
                "\t2. The host must be 'api.openweathermap.org'\n"
                "\t3. Versions can either be '2.5' or '3.0'\n"
                "\t4. Finally the bearer must be 'data' pointing to 'weather' or 'onecall'\n\n"
                # rf'Regex pattern: r"^https:\/\/api\.openweathermap\.org\/data\/(2\.5|3\.0)\/(weather|onecall)$"'
                f"If you think, this is a mistake, please raise a bug report at: {issue_link}\n"
            )
        return value

    @field_validator("website", mode="after", check_fields=True)
    def validate_websites(cls, value: HttpUrl | List[HttpUrl]) -> List[HttpUrl]:
        """Validate websites."""
        if isinstance(value, list):
            return value
        return [value]

    @field_validator("notify_reminders", mode="after", check_fields=True)
    def validate_notify_reminders(
        cls, value: enums.ReminderOptions | List[enums.ReminderOptions]
    ) -> List[enums.ReminderOptions]:
        """Validate reminder options."""
        if isinstance(value, list):
            if enums.ReminderOptions.all in value:
                return [enums.ReminderOptions.all]
            return value
        return [value]

    @field_validator("startup_options", mode="after", check_fields=True)
    def validate_startup_options(
        cls, value: enums.StartupOptions | List[enums.StartupOptions] | None
    ) -> List[enums.StartupOptions] | List:
        """Validate startup options."""
        if value == "None":
            return []
        if isinstance(value, list):
            if enums.StartupOptions.all in value:
                return [enums.StartupOptions.all]
            return value
        return [value]

    @field_validator("microphone_index", mode="before", check_fields=True)
    def validate_microphone_index(
        cls, value: int | PositiveInt
    ) -> int | PositiveInt | None:
        """Validates microphone index."""
        return squire.channel_validator(value, "input")

    @field_validator("speaker_index", mode="before", check_fields=True)
    def validate_speaker_index(
        cls, value: int | PositiveInt
    ) -> int | PositiveInt | None:
        """Validates speaker index."""
        # fixme: Create an OS agnostic model for usage (currently the index value is unused)
        return squire.channel_validator(value, "output")

    @field_validator("birthday", mode="before", check_fields=True)
    def validate_birthday(cls, value: str) -> str | None:
        """Validates date value to be in DD-MM format."""
        if not value:
            return
        try:
            if datetime.strptime(value, "%d-%B"):
                return value
        except ValueError:
            raise InvalidEnvVars("format should be 'DD-MM'")

    @field_validator("vpn_password", mode="before", check_fields=True)
    def validate_vpn_password(cls, v: str) -> str | NoReturn:
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
    def validate_weather_alert(cls, value: str) -> str | None:
        """Validates date value to be in DD-MM format."""
        if not value:
            return
        try:
            # Convert datetime to string as the '07' for '%I' will pass validation but fail comparison
            if val := datetime.strptime(value, "%I:%M %p"):
                return val.strftime("%I:%M %p")
        except ValueError:
            raise InvalidEnvVars("format should be '%I:%M %p'")


def env_vault_loader() -> EnvConfig | None:
    """Load env config by retrieving a DB table.

    Notes:
        Looks for the environment variable ``vault_env`` or ``env_file``
        Defaults to ``.vault.env`` to load env vars specific to vault.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    if not env_file.vault:
        # noinspection PyArgumentList
        return EnvConfig()

    dotenv.load_dotenv(env_file.vault.filepath, override=True)

    import vaultapi

    env_vars = vaultapi.VaultAPIClient().get_table(
        table_name=env_file.get_env(["vault_table_name", "table_name"], "jarvis")
    )

    # Load all secrets as env vars
    for key, value in env_vars.items():
        os.environ[key] = value

    # noinspection PyArgumentList
    env_config = EnvConfig()

    # Remove all secrets from env vars
    for key, value in env_vars.items():
        os.environ.pop(key)

    return env_config


def env_file_loader() -> EnvConfig:
    """Loads environment variables based on filetypes.

    Notes:
        Looks for the environment variable ``jarvis_env`` or ``env_file``
        Defaults to ``.env`` to load env vars specific to Jarvis.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    if not env_file.jarvis:
        # noinspection PyArgumentList
        return EnvConfig()

    if env_file.jarvis.filepath.suffix.lower() == ".json":
        with open(env_file.jarvis.filepath) as stream:
            env_data = json.load(stream)
        return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    elif env_file.jarvis.filepath.suffix.lower() in (".yaml", ".yml"):
        with open(env_file.jarvis.filepath) as stream:
            env_data = yaml.load(stream, yaml.FullLoader)
        return EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    elif (
        not env_file.jarvis.filepath.suffix
        or env_file.jarvis.filepath.suffix.lower()
        in (
            ".text",
            ".txt",
            ".env",
            "",
        )
    ):
        return EnvConfig.from_env_file(env_file.jarvis.filepath)
    else:
        raise ValueError(
            f"\n\tUnsupported format for {env_file.jarvis.filepath!r}, "
            "can be one of (.json, .yaml, .yml, .txt, .text, .env)"
        )


# noinspection PyBroadException
try:
    env = env_vault_loader()
except Exception:
    env = env_file_loader()


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
    ip_info: FilePath = os.path.join(root, "ip_info.yaml")

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
