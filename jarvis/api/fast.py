from threading import Thread
from typing import NoReturn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jarvis import version
from jarvis.api import routers
from jarvis.api.squire import discover, stockanalysis_squire
from jarvis.api.squire.logger import logger
from jarvis.modules.models import models

# Initiate API
app = FastAPI(
    title="Jarvis API",
    description="Acts as a gateway to communicate with **Jarvis**, and an entry point for the natural language UI.\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version=version
)


def enable_cors() -> NoReturn:
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
        allow_methods=["GET", "POST"],
        allow_headers=["host", "user-agent",  # Default headers
                       "authorization", "apikey",  # Offline auth and stock monitor apikey headers
                       "email-otp", "email_otp",  # One time passcode sent via email
                       "access-token", "access_token"],  # Access token sent via email
    )


# Include all the routers
# WATCH OUT: for changes in function name
if models.settings.pname == "fast_api":  # Avoid looping when called by subprocesses
    enable_cors()
    for route in discover.routes(routers=routers.__path__[0]):
        app.include_router(router=route)


@app.on_event(event_type='startup')
async def startup_func() -> NoReturn:
    """Simple startup function to add anything that has to be triggered when Jarvis API starts up."""
    logger.info("Hosting at http://{%s}:{%s}", models.env.offline_host, models.env.offline_port)
    if models.env.author_mode:
        Thread(target=stockanalysis_squire.nasdaq).start()
