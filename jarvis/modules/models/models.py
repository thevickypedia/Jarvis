# noinspection PyUnresolvedReferences
"""This is a space where all the validated environment variables are loaded and evalued as per requirements.

>>> Models

"""

import os
import pathlib
import warnings
from importlib import metadata

import pvporcupine
from cryptography.fernet import Fernet
from pydantic import PositiveInt

from jarvis.modules.database import database
from jarvis.modules.exceptions import InvalidEnvVars
from jarvis.modules.models.classes import (
    AUDIO_DRIVER,
    Indicators,
    env,
    fileio,
    settings,
)
from jarvis.modules.models.enums import (
    DistanceUnits,
    StartupOptions,
    SupportedPlatforms,
    TemperatureUnits,
)
from jarvis.modules.models.tables import tables
from jarvis.modules.models.validators import Validator

WAKE_WORD_DETECTOR = metadata.version(pvporcupine.__name__)

# Shared across other modules
voices = AUDIO_DRIVER.getProperty("voices")
indicators = Indicators()

# Database connection for base db
db = database.Database(database=fileio.base_db)

startup = settings.pname in ("JARVIS", "telegram_api", "jarvis_api")
# 'startup_gpt' is required since it has to be invoked only for certain child processes
# this will avoid running GPT instance for pre-commit as well
if startup and StartupOptions.all in env.startup_options:
    startup_car = True
    startup_gpt = True
    startup_thermostat = True
elif startup:
    startup_car = StartupOptions.car in env.startup_options
    startup_gpt = StartupOptions.gpt in env.startup_options
    startup_thermostat = StartupOptions.thermostat in env.startup_options
else:
    startup_car = False
    startup_gpt = False
    startup_thermostat = False


def _set_fernet_key() -> str:
    """Set a new Fernet key in the database.

    Returns:
        str:
        Returns 32 url-safe base64-encoded bytes.
    """
    fernet_key = Fernet.generate_key().decode()
    with db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM fernet")
        cursor.execute("INSERT INTO fernet (key) VALUES (?);", (fernet_key,))
        connection.commit()
    return fernet_key


def get_fernet_key() -> str:
    """Get the Fernet key from the database, if it does not exist, create a new one.

    Returns:
        str:
        Returns 32 url-safe base64-encoded bytes.
    """
    with db.connection as connection:
        cursor = connection.cursor()
        data = cursor.execute("SELECT key FROM fernet;")
        keys = data.fetchall()
        if len(keys) == 1:
            return keys[0][0]
    return _set_fernet_key()


def _distance_temperature_brute_force() -> None:
    """Convert distance and temperature so that, metric goes with kilometers and imperial with miles."""
    # If distance is requested in miles, then temperature is brute forced to imperial units
    if env.distance_unit == DistanceUnits.MILES:
        env.temperature_unit = TemperatureUnits.IMPERIAL

    # If temperature is requested in imperial, then distance is brute forced to miles
    if env.temperature_unit == TemperatureUnits.IMPERIAL:
        env.distance_unit = DistanceUnits.MILES

    # If neither temperature nor distance is set, then defaults temperature to imperial and distance to miles
    if not env.distance_unit and not env.temperature_unit:
        env.distance_unit = DistanceUnits.MILES
        env.temperature_unit = TemperatureUnits.IMPERIAL

    if not env.distance_unit:
        # If distance is not set, but temperature is requested as imperial, then defaults distance to miles
        if env.temperature_unit == TemperatureUnits.IMPERIAL:
            env.distance_unit = DistanceUnits.MILES
        # If distance is not set, but temperature is requested as metric, then defaults distance to kilometers
        elif env.temperature_unit == TemperatureUnits.METRIC:
            env.distance_unit = DistanceUnits.KILOMETERS

    if not env.temperature_unit:
        # If temperature is not set, but distance is requested as miles, then defaults temperature to imperial
        if env.distance_unit == DistanceUnits.MILES:
            env.temperature_unit = TemperatureUnits.IMPERIAL
        # If temperature is not set, but distance is requested as kms, then defaults temperature to metric
        elif env.distance_unit == DistanceUnits.KILOMETERS:
            env.temperature_unit = TemperatureUnits.METRIC


def _set_default_voice_name() -> None:
    """Set default voice name based on the Operating System."""
    if settings.os == SupportedPlatforms.macOS:
        env.voice_name = "Daniel"
    elif settings.os == SupportedPlatforms.windows:
        env.voice_name = "David"
    elif settings.os == SupportedPlatforms.linux:
        env.voice_name = "english-us"


def _main_process_validations() -> None:
    """Validations that should happen only when the main process is triggered."""
    validator = Validator(True, env)
    validator.validate_wake_words(WAKE_WORD_DETECTOR, settings.os)

    # If sensitivity is an integer or float, converts it to a list
    if isinstance(env.sensitivity, float) or isinstance(env.sensitivity, PositiveInt):
        env.sensitivity = [env.sensitivity] * len(env.wake_words)

    # Create all necessary DB tables during startup
    os.makedirs(fileio.root, exist_ok=True)
    for attr in tables.model_fields:
        table = getattr(tables, attr)
        db.create_table(
            table_name=table.name, columns=table.columns, primary_key=table.pkey
        )
    _set_fernet_key()
    # Create required file for alarms
    pathlib.Path(fileio.alarms).touch(exist_ok=True)
    # Create required file for reminders
    pathlib.Path(fileio.reminders).touch(exist_ok=True)
    # Create required directory for uploads
    os.makedirs(fileio.uploads, exist_ok=True)


def _global_validations() -> None:
    """Validations that should happen for all processes including parent and child."""
    main: bool = settings.pname == "JARVIS"
    validator = Validator(main=main, env=env)
    if validator.validate_builtin_voices(voices):
        _set_default_voice_name()

    if not all((env.open_gmail_user, env.open_gmail_pass)):
        env.open_gmail_user = env.gmail_user
        env.open_gmail_pass = env.gmail_pass

    # Note: Pydantic validation for ICS_URL can be implemented using regex=".*ics$"
    # However it will NOT work in this use case, since the type hint is HttpUrl
    if env.ics_url and not env.ics_url.path.endswith(".ics"):
        if main:
            raise InvalidEnvVars("'ICS_URL' should end with .ics")
        else:
            env.ics_url = None
            warnings.warn("'ICS_URL' should end with .ics")

    # Forces limited version if env var is set, otherwise it is enforced based on the number of cores
    if env.limited:
        settings.limited = True
    # If env var is set as False to brute force full version on a device with < 4 processors
    if env.limited is False:
        settings.limited = False
    if settings.limited is True and env.weather_alert:
        warnings.warn("weather alert cannot function on limited mode")
    if env.author_mode and settings.limited:
        warnings.warn(
            "'author_mode' cannot be set when 'limited' mode is enabled, disabling author mode."
        )

    env.camera_index = validator.validate_camera_indices()
    validator.validate_speech_synthesis_voices()
    _distance_temperature_brute_force()


_global_validations()

# Required at top level to let other modules access it
if env.temperature_unit == TemperatureUnits.IMPERIAL:
    temperature_symbol = "F"
elif env.temperature_unit == TemperatureUnits.METRIC:
    temperature_symbol = "C"

if settings.pname in (
    "JARVIS",
    "pre_commit",
    "startup_script",
    "plot_mic",
    "crontab_executor",
):
    _main_process_validations()
