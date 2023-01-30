import os
import time
from datetime import datetime
from multiprocessing import Process, current_process
from threading import Thread
from typing import Any, NoReturn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jarvis import version
from jarvis._preexec import keywords_handler  # noqa
from jarvis.api import routers
from jarvis.api.squire import discover, stockmonitor_squire
from jarvis.api.squire.logger import logger
from jarvis.api.triggers.stock_report import Investment
from jarvis.modules.models import models

# Initiate API
app = FastAPI(
    title="Jarvis API",
    description="Acts as a gateway to communicate with **Jarvis**, and an entry point for the natural language UI.\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version=version
)

# Include all the routers
if current_process().name == "fast_api":  # Avoid looping when called by subprocesses
    for route in discover.routes(routers=routers.__path__[0]):
        app.include_router(router=route)


def update_keywords() -> NoReturn:
    """Gets initiated in a thread to update keywords upon file modification."""
    logger.info("Initiated background task to update keywords upon file modification.")
    while True:
        keywords_handler.rewrite_keywords()
        time.sleep(1)


async def enable_cors() -> NoReturn:
    """Allow CORS: Cross-Origin Resource Sharing to allow restricted resources on the API."""
    logger.info('Setting CORS policy.')
    origins = [
        "http://localhost.com",
        "https://localhost.com",
        f"http://{models.env.website}",
        f"https://{models.env.website}",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def run_robinhood() -> NoReturn:
    """Runs in a dedicated process during startup, if the file was modified earlier than the past hour."""
    if os.path.isfile(models.fileio.robinhood):
        modified = int(os.stat(models.fileio.robinhood).st_mtime)
        logger.info(f"{models.fileio.robinhood} was generated on {datetime.fromtimestamp(modified).strftime('%c')}.")
        if int(time.time()) - modified < 3_600:  # generates new file only if the file is older than an hour
            return
    logger.info('Initiated robinhood gatherer.')
    Investment(logger=logger).report_gatherer()


@app.on_event(event_type='startup')
async def start_robinhood() -> Any:
    """Initiates robinhood gatherer in a process and adds a cron schedule if not present already."""
    await enable_cors()
    stockmonitor_squire.nasdaq()
    logger.info(f'Hosting at http://{models.env.offline_host}:{models.env.offline_port}')
    if all([models.env.robinhood_user, models.env.robinhood_pass, models.env.robinhood_pass]):
        Process(target=run_robinhood).start()
    Thread(target=update_keywords).start()
