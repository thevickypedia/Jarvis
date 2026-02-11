import asyncio
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI

from jarvis import version
from jarvis.api import entrypoint
from jarvis.api.background_task import task
from jarvis.api.logger import logger
from jarvis.api.routers import routes
from jarvis.api.squire import stockanalysis_squire
from jarvis.modules.models import enums, models


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Simple startup function to add anything that has to be triggered when Jarvis API starts up."""
    # noinspection HttpUrlsUsage
    logger.info("Hosting at http://%s:%s", models.env.offline_host, models.env.offline_port)
    if models.env.author_mode:
        Thread(target=stockanalysis_squire.nasdaq).start()
    entrypoint.startup()
    logger.info("Initiating background tasks...")
    bg_task = asyncio.create_task(task.background_tasks())
    yield
    bg_task.cancel()


# Initiate API
app = FastAPI(
    title="Jarvis API",
    description="#### Gateway to communicate with Jarvis, and an entry point for the UI.\n\n"
    "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version=version,
    lifespan=lifespan,
)

# Include all the routers
# Avoid looping when called by subprocesses
if models.settings.pname == enums.ProcessNames.jarvis_api:
    # Cannot add middleware after an application has started
    app.add_middleware(**entrypoint.get_cors_params())
    app.routes.extend(routes.get_all_routes())
