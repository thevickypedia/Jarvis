from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI

from jarvis import version
from jarvis.api import entrypoint
from jarvis.api.logger import logger
from jarvis.api.routers import routes
from jarvis.api.squire import stockanalysis_squire
from jarvis.modules.models import models


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Simple startup function to add anything that has to be triggered when Jarvis API starts up."""
    logger.info(
        "Hosting at http://%s:%s", models.env.offline_host, models.env.offline_port
    )
    if models.env.author_mode:
        Thread(target=stockanalysis_squire.nasdaq).start()
    entrypoint.startup()
    yield


# Initiate API
app = FastAPI(
    title="Jarvis API",
    description="#### Gateway to communicate with Jarvis, and an entry point for the UI.\n\n"
    "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version=version,
    lifespan=lifespan,
)

# Include all the routers
# WATCH OUT: for changes in function name
if models.settings.pname == "jarvis_api":  # Avoid looping when called by subprocesses
    # Cannot add middleware after an application has started
    app.add_middleware(**entrypoint.get_cors_params())
    app.routes.extend(routes.get_all_routes())
