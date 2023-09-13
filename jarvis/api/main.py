from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from jarvis import version
from jarvis.api import routers
from jarvis.api.logger import logger
from jarvis.api.squire import discover, stockanalysis_squire
from jarvis.modules.models import models

data = {}
for router in discover.routes(routers=routers.__path__[0]):
    for route in router.routes:
        if isinstance(route, APIRoute) and route.include_in_schema:
            data[route.path] = next(iter(route.methods))

# Find the maximum lengths of URL and Method for proper alignment
max_url_length = max(len(url) for url in data.keys())
max_method_length = max(len(method) for method in data.values())

long_description = f"| {'URL'.ljust(max_url_length)} | {'Method'.ljust(max_method_length)} |\n" \
                   f"| {'-' * max_url_length} | {'-' * max_method_length} |\n"
for url, method in data.items():
    long_description += f"| {url.ljust(max_url_length)} | {method.ljust(max_method_length)} |\n"

# Initiate API
app = FastAPI(
    title="Jarvis API",
    description="#### Gateway to communicate with Jarvis, and an entry point for the UI.\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)\n\n\n"
                f"{long_description}",
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
    enable_cors()
    for route in discover.routes(routers=routers.__path__[0]):
        app.include_router(router=route)


@app.on_event(event_type='startup')
async def startup_func() -> None:
    """Simple startup function to add anything that has to be triggered when Jarvis API starts up."""
    logger.info("Hosting at http://%s:%s", models.env.offline_host, models.env.offline_port)
    if models.env.author_mode:
        Thread(target=stockanalysis_squire.nasdaq).start()
