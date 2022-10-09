# noinspection PyUnresolvedReferences
"""This is a space where all the validated environment variables are loaded and evalued as per requirements.

>>> Models

"""

import os
import platform
import sys
import time
from multiprocessing import current_process

import cv2
import pvporcupine
from pydantic import PositiveInt

from api.rh_helper import cron_schedule
from modules.camera.camera import Camera
from modules.crontab.expression import CronExpression
from modules.database import database
from modules.exceptions import CameraError, InvalidEnvVars
from modules.models.classes import Indicators, env, fileio, settings

indicators = Indicators()

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')

env.website = env.website.lstrip(f"{env.website.scheme}://")

if settings.legacy:
    pvporcupine.KEYWORD_PATHS = {}
    pvporcupine.MODEL_PATH = os.path.join(os.path.dirname(pvporcupine.__file__),
                                          'lib/common/porcupine_params.pv')
    pvporcupine.LIBRARY_PATH = os.path.join(os.path.dirname(pvporcupine.__file__),
                                            f'lib/mac/{platform.machine()}/libpv_porcupine.dylib')
    keyword_files = os.listdir(os.path.join(os.path.dirname(pvporcupine.__file__), "resources/keyword_files/mac/"))
    for x in keyword_files:
        pvporcupine.KEYWORD_PATHS[x.split('_')[0]] = os.path.join(os.path.dirname(pvporcupine.__file__),
                                                                  f"resources/keyword_files/mac/{x}")

if settings.bot != "sphinx-build":
    for keyword in env.wake_words:
        if not pvporcupine.KEYWORD_PATHS.get(keyword) or not os.path.isfile(pvporcupine.KEYWORD_PATHS[keyword]):
            raise InvalidEnvVars(
                f"Detecting '{keyword}' is unsupported!\n"
                f"Available keywords are: {', '.join(list(pvporcupine.KEYWORD_PATHS.keys()))}"
            )

# If sensitivity is an integer or float, converts it to a list
if isinstance(env.sensitivity, float) or isinstance(env.sensitivity, PositiveInt):
    env.sensitivity = [env.sensitivity] * len(env.wake_words)

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

# Create all necessary DB tables during startup
db = database.Database(database=fileio.base_db)
TABLES = {
    env.event_app: ["info", "date"],
    "ics": ["info", "date"],
    "stopper": ["flag", "caller"],
    "restart": ["flag", "caller"],
    "children": ["meetings", "events", "crontab", "party", "guard"],
    "vpn": ["state"],
    "party": ["pid"],
    "guard": ["state"]
}
for table, column in TABLES.items():
    db.create_table(table_name=table, columns=column)

if current_process().name == "MainProcess":
    try:
        cameras = Camera().list_cameras()
    except CameraError:
        cameras = []

    if cameras:
        if len(cameras) == 0:
            env.camera_index = 0
        else:
            if env.camera_index is None:
                env.camera_index = 0
            elif env.camera_index >= len(cameras):
                raise CameraError(
                    f"Camera index # {env.camera_index} unavailable.\n"
                    "Camera index cannot exceed the number of available cameras.\n"
                    f"Available Cameras [{len(cameras)}]: {', '.join([f'{i}-{c}' for i, c in enumerate(cameras)])}"
                )
    else:
        env.camera_index = None

    if env.camera_index is not None:
        statement = f"Using '{cameras[env.camera_index]}' for camera operations."

        cam = cv2.VideoCapture(env.camera_index)
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            raise CameraError(f"Unable to read the camera - {cameras[env.camera_index]}")
        cam.release()
        if env.camera_index == 0 and len(cameras) > 1:
            statement += f" To use `{'or '.join([n for i, n in enumerate(cameras) if i != env.camera_index])}` " \
                         f"add index # {'or '.join([str(i) for i, n in enumerate(cameras) if i != env.camera_index])}" \
                         " as env var and restart."
        sys.stdout.write(f"\r{statement}")
        time.sleep(1)
