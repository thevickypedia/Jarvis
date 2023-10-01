import os
import pathlib
import shutil
from datetime import datetime
from multiprocessing import Process
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jarvis import version
from jarvis.api import routers
from jarvis.api.logger import logger
from jarvis.api.squire import discover, stockanalysis_squire
from jarvis.executors import crontab
from jarvis.modules.models import models

# Initiate API
app = FastAPI(
    title="Jarvis API",
    description="#### Gateway to communicate with Jarvis, and an entry point for the UI.\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version=version
)


def enable_cors() -> None:
    """Allow CORS: Cross-Origin Resource Sharing to allow restricted resources on the API."""
    logger.info('Setting CORS policy.')
    origins = [
        "http://localhost.com",
        "https://localhost.com",
        f"http://{models.env.website.host}",
        f"https://{models.env.website.host}",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["host", "user-agent",  # Default headers
                       "authorization", "apikey",  # Offline auth and stock monitor apikey headers
                       "email-otp", "email_otp",  # One time passcode sent via email
                       "access-token", "access_token"],  # Access token sent via email
    )


# Include all the routers
# WATCH OUT: for changes in function name
if models.settings.pname == "jarvis_api":  # Avoid looping when called by subprocesses
    # Cannot add middleware after an application has started
    enable_cors()
    for router in discover.routes(routers.__path__[0]):
        app.include_router(router)


@app.on_event(event_type='startup')
async def startup_func() -> None:
    """Simple startup function to add anything that has to be triggered when Jarvis API starts up."""
    logger.info("Hosting at http://%s:%s", models.env.offline_host, models.env.offline_port)
    if models.env.author_mode:
        Thread(target=stockanalysis_squire.nasdaq).start()
    if not os.path.isdir(models.fileio.startup_dir):
        return
    for startup_script in os.listdir(models.fileio.startup_dir):
        startup_script = pathlib.Path(startup_script)
        logger.info("Executing startup script: '%s'", startup_script)
        if startup_script.suffix in ('.py', '.sh', '.zsh') and not startup_script.stem.startswith('_'):
            starter = None
            if startup_script.suffix == ".py":
                starter = shutil.which(cmd='python')
            if startup_script.suffix == ".sh":
                starter = shutil.which(cmd='bash')
            if startup_script.suffix == ".zsh":
                starter = shutil.which(cmd='zsh')
            if not starter:
                continue
            script = starter + " " + os.path.join(models.fileio.startup_dir, startup_script)
            logger.debug("Running %s", script)
            log_file = datetime.now().strftime(os.path.join('logs', 'startup_script_%d-%m-%Y.log'))
            Process(target=crontab.executor, args=(script, log_file)).start()
        else:
            logger.warning("Unsupported file format for startup script: %s", startup_script)
