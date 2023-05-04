# noinspection PyUnresolvedReferences
"""This is a space where all the validated environment variables are loaded and evalued as per requirements.

>>> Models

"""

import os
import warnings
from multiprocessing import current_process
from typing import NoReturn, Union

import cv2
import pvporcupine
import requests
from pydantic import PositiveInt

from jarvis.api.squire.scheduler import rh_cron_schedule, sm_cron_schedule
from jarvis.modules.camera.camera import Camera
from jarvis.modules.database import database
from jarvis.modules.exceptions import (CameraError, EgressErrors,
                                       InvalidEnvVars, MissingEnvVars,
                                       SegmentationError)
from jarvis.modules.models.classes import (DistanceUnits, Indicators,
                                           RecognizerSettings,
                                           TemperatureUnits, audio_driver, env,
                                           fileio, settings,
                                           supported_platforms)
from jarvis.modules.utils import util

# Shared across other modules
voices: Union[list, object] = audio_driver.getProperty("voices") if audio_driver else []
indicators = Indicators()
# TABLES to be created in `fileio.base_db`
TABLES = {
    env.event_app: ("info", "date"),
    "ics": ("info", "date"),
    "stopper": ("flag", "caller"),
    "restart": ("flag", "caller"),
    "children": ("meetings", "events", "crontab", "party", "guard", "surveillance", "plot_mic"),
    "vpn": ("state",),
    "party": ("pid",),
    "guard": ("state", "trigger"),
    "listener": ("state",),
}
KEEP_TABLES = ("vpn", "party")  # TABLES to keep from `fileio.base_db`

# If distance is requested in miles, then temperature is brute forced to imperial units
if env.distance_unit == DistanceUnits.MILES:
    env.temperature_unit = TemperatureUnits.IMPERIAL
if env.temperature_unit == TemperatureUnits.IMPERIAL:
    temperature_symbol = "F"
elif env.temperature_unit == TemperatureUnits.METRIC:
    temperature_symbol = "C"
else:
    raise InvalidEnvVars  # taken care by pydantic


def _set_default_voice_name():
    """Set default voice name based on the Operating System."""
    if settings.os == supported_platforms.macOS:
        env.voice_name = "Daniel"
    elif settings.os == supported_platforms.windows:
        env.voice_name = "David"
    elif settings.os == supported_platforms.linux:
        env.voice_name = "english-us"


def _main_process_validations() -> NoReturn:
    """Validations that should happen only when the main process is triggered."""
    if not env.recognizer_settings and not env.phrase_limit:
        env.recognizer_settings = RecognizerSettings()  # Default override when phrase limit is not available

    if settings.legacy:
        pvporcupine.KEYWORD_PATHS = {}
        pvporcupine.MODEL_PATH = os.path.join(os.path.dirname(pvporcupine.__file__),
                                              'lib/common/porcupine_params.pv')
        pvporcupine.LIBRARY_PATH = os.path.join(os.path.dirname(pvporcupine.__file__),
                                                'lib/mac/x86_64/libpv_porcupine.dylib')
        keyword_files = os.listdir(os.path.join(os.path.dirname(pvporcupine.__file__),
                                                'resources/keyword_files/mac/'))

        for x in keyword_files:  # Iterates over the available flash files, to override the class
            pvporcupine.KEYWORD_PATHS[x.split('_')[0]] = os.path.join(os.path.dirname(pvporcupine.__file__),
                                                                      f'resources/keyword_files/mac/{x}')

    for keyword in env.wake_words:
        if not pvporcupine.KEYWORD_PATHS.get(keyword) or not os.path.isfile(pvporcupine.KEYWORD_PATHS[keyword]):
            raise InvalidEnvVars(f"Detecting {keyword!r} is unsupported!\n"
                                 f"Available keywords are: {', '.join(list(pvporcupine.KEYWORD_PATHS.keys()))}")

    # If sensitivity is an integer or float, converts it to a list
    if isinstance(env.sensitivity, float) or isinstance(env.sensitivity, PositiveInt):
        env.sensitivity = [env.sensitivity] * len(env.wake_words)

    # Create all necessary DB tables during startup
    db = database.Database(database=fileio.base_db)
    for table, column in TABLES.items():
        db.create_table(table_name=table, columns=column)


def _global_validations() -> NoReturn:
    """Validations that should happen for all processes including parent and child."""
    main = True if current_process().name == "MainProcess" else False
    # Validate root password present for linux systems
    if settings.os == supported_platforms.linux:
        if not env.root_password:
            raise MissingEnvVars(
                "Linux requires the host machine's password to be set as the env var: "
                "ROOT_PASSWORD due to terminal automations."
            )

    if voice_names := [__voice.name for __voice in voices]:
        if not env.voice_name:
            _set_default_voice_name()
        elif env.voice_name not in voice_names:
            if main:
                raise InvalidEnvVars(f"{env.voice_name!r} is not available.\n"
                                     f"Available voices are: {', '.join(voice_names)}")
            else:
                _set_default_voice_name()
                warnings.warn(
                    f"{env.voice_name!r} is not available. Defaulting to {env.voice_name!r}"
                )

    if env.website and env.website.startswith("http"):
        env.website = env.website.lstrip(f"{env.website.scheme}://")

    if not all((env.open_gmail_user, env.open_gmail_pass)):
        env.open_gmail_user = env.gmail_user
        env.open_gmail_pass = env.gmail_pass

    # Note: Pydantic validation for ICS_URL can be implemented using regex=".*ics$"
    # However it will NOT work in this use case, since the type hint is HttpUrl
    if env.ics_url and not env.ics_url.endswith('.ics'):
        if main:
            raise InvalidEnvVars("'ICS_URL' should end with .ics")
        else:
            env.ics_url = None
            warnings.warn(
                "'ICS_URL' should end with .ics"
            )

    if env.speech_synthesis_port == env.offline_port:
        if main:
            raise InvalidEnvVars(
                "Speech synthesizer and offline communicator cannot run simultaneously on the same port number."
            )
        else:
            env.speech_synthesis_port = util.get_free_port()
            warnings.warn(
                "Speech synthesizer and offline communicator cannot run on same port number. "
                f"Defaulting to {env.speech_synthesis_port}"
            )

    if env.author_mode:
        if all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
            env.crontab.append(rh_cron_schedule(extended=True))
        env.crontab.append(sm_cron_schedule())

    if env.limited:  # Forces limited version if env var is set, otherwise it is enforced based on the number of cores
        settings.limited = True
    if env.limited is False:  # If env var is set as False to brute force full version on a device with < 4 processors
        settings.limited = False
    if settings.limited is True and env.weather_alert:
        warnings.warn(
            "weather alert cannot function on limited mode"
        )
    if env.author_mode and settings.limited:
        warnings.warn(
            "'author_mode' cannot be set when 'limited' mode is enabled, disabling author mode."
        )

    # Validate if able to read camera only if a camera env var is set,
    try:
        if env.camera_index is None:
            cameras = []
        else:
            cameras = Camera().list_cameras()
    except CameraError:
        cameras = []
    if cameras:
        if env.camera_index >= len(cameras):
            if main:
                raise InvalidEnvVars(
                    f"Camera index # {env.camera_index} unavailable.\n"
                    "Camera index cannot exceed the number of available cameras.\n"
                    f"{len(cameras)} available cameras: {', '.join([f'{i}: {c}' for i, c in enumerate(cameras)])}"
                )
            else:
                warnings.warn(
                    f"Camera index # {env.camera_index} unavailable.\n"
                    "Camera index cannot exceed the number of available cameras.\n"
                    f"{len(cameras)} available cameras: {', '.join([f'{i}: {c}' for i, c in enumerate(cameras)])}"
                )
                env.camera_index = None
    else:
        env.camera_index = None

    if env.camera_index is None:
        env.camera_index = 0  # Set default but skip validation
    else:
        cam = cv2.VideoCapture(env.camera_index)
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            if main:
                raise CameraError(f"Unable to read the camera - {cameras[env.camera_index]}")
            else:
                warnings.warn(f"Unable to read the camera - {cameras[env.camera_index]}")
                env.camera_index = None
        cam.release()

    # Validate voice for speech synthesis
    try:
        response = requests.get(url=f"http://{env.speech_synthesis_host}:{env.speech_synthesis_port}/api/voices",
                                timeout=(3, 3))  # Set connect and read timeout explicitly
        if response.ok:
            available_voices = [value.get('id').replace('/', '_') for key, value in response.json().items()]
            if env.speech_synthesis_voice not in available_voices:
                if main:
                    raise InvalidEnvVars(
                        f"{env.speech_synthesis_voice} is not available.\n"
                        f"Available Voices for Speech Synthesis: {', '.join(available_voices).replace('/', '_')}"
                    )
                else:
                    warnings.warn(
                        f"{env.speech_synthesis_voice} is not available.\n"
                        f"Available Voices for Speech Synthesis: {', '.join(available_voices).replace('/', '_')}"
                    )
    except EgressErrors:
        if not audio_driver:
            raise SegmentationError(
                f"\n\n{settings.bot} needs either an audio driver OR speech-synthesis to run in Docker container\n"
                f"normally {settings.bot} will try to launch the Docker container to run speech-synthesis.\n"
                "However if audio driver is unavailable, the docker container should be launched manually or "
                "the audio driver should be fixed.\n"
                "Refer:\n"
                "   https://github.com/thevickypedia/Jarvis/wiki#os-agnostic-voice-model\n"
                "   https://stackoverflow.com/a/76050539/13691532"
            )


_global_validations()
# settings.bot is initiated with "jarvis" but later changed when custom wake words are used
if settings.bot == "jarvis" and current_process().name == "MainProcess":
    _main_process_validations()
