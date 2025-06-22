import os
import pathlib
import shutil
import socket
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware

from jarvis.api.logger import logger
from jarvis.executors import crontab, resource_tracker
from jarvis.modules.models import models


# noinspection HttpUrlsUsage
def get_cors_params() -> dict:
    """Allow CORS: Cross-Origin Resource Sharing to allow restricted resources on the API."""
    logger.info("Setting CORS policy.")
    origins = [
        f"http://localhost:{models.env.offline_port}",
        f"http://0.0.0.0:{models.env.offline_port}",
        f"http://{socket.gethostname()}:{models.env.offline_port}",
        f"http://{socket.gethostbyname('localhost')}:{models.env.offline_port}",
    ]
    for website in models.env.website:
        origins.extend([f"http://{website.host}", f"https://{website.host}"])
    logger.info("Allowed origins: %s", ", ".join(origins))

    return dict(
        middleware_class=CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=[
            "host",
            "user-agent",  # Default headers
            "authorization",
            "apikey",  # Offline auth and stock monitor apikey headers
            "email-otp",
            "email_otp",  # One time passcode sent via email
            "access-token",
            "access_token",  # Access token sent via email
        ],
    )


def startup() -> None:
    """Runs startup scripts (``.py``, ``.sh``, ``.zsh``) stored in ``fileio/startup`` directory."""
    if not os.path.isdir(models.fileio.startup_dir):
        return
    for startup_script in os.listdir(models.fileio.startup_dir):
        startup_script = pathlib.Path(startup_script)
        logger.info("Executing startup script: '%s'", startup_script)
        if startup_script.suffix in (
            ".py",
            ".sh",
            ".zsh",
        ) and not startup_script.stem.startswith("_"):
            starter = None
            if startup_script.suffix == ".py":
                starter = shutil.which(cmd="python")
            if startup_script.suffix == ".sh":
                starter = shutil.which(cmd="bash")
            if startup_script.suffix == ".zsh":
                starter = shutil.which(cmd="zsh")
            if not starter:
                continue
            script = (
                starter + " " + os.path.join(models.fileio.startup_dir, startup_script)
            )
            logger.debug("Running %s", script)
            log_file = datetime.now().strftime(
                os.path.join("logs", "startup_script_%d-%m-%Y.log")
            )
            resource_tracker.semaphores(
                crontab.executor, (script, log_file, "startup_script")
            )
        else:
            logger.warning(
                "Unsupported file format for startup script: %s", startup_script
            )
