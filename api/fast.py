import importlib
import logging
import mimetypes
import os
import pathlib
import string
import time
from datetime import datetime
from logging.config import dictConfig
from multiprocessing import Process
from threading import Thread
from typing import Any, NoReturn

import requests
from fastapi import Depends, FastAPI
from fastapi import status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from api import authenticator
from api.models import GetData, InvestmentFilter
from api.report_gatherer import Investment
from executors.offline import offline_communicator
from modules.audio import speaker
from modules.exceptions import APIResponse
from modules.models import config, models
from modules.offline import compatibles
from modules.utils import shared, support

env = models.env
fileio = models.FileIO()

OFFLINE_PROTECTOR = [Depends(dependency=authenticator.offline_has_access)]
ROBINHOOD_PROTECTOR = [Depends(dependency=authenticator.robinhood_has_access)]

robinhood_token = {'token': ''}

if not os.path.isfile(config.APIConfig().ACCESS_LOG_FILENAME):
    pathlib.Path(config.APIConfig().ACCESS_LOG_FILENAME).touch()

if not os.path.isfile(config.APIConfig().DEFAULT_LOG_FILENAME):
    pathlib.Path(config.APIConfig().DEFAULT_LOG_FILENAME).touch()

offline_compatible = compatibles.offline_compatible()

importlib.reload(module=logging) if env.macos else None
dictConfig(config=config.APIConfig().LOGGING_CONFIG)

logging.getLogger("uvicorn.access").addFilter(InvestmentFilter())  # Adds token filter to the access logger
logging.getLogger("uvicorn.access").propagate = False  # Disables access logger in default logger to log independently

logger = logging.getLogger('uvicorn.default')

app = FastAPI(
    title="Jarvis API",
    description="Handles offline communication with **Jarvis** and generates a one time auth token for **Robinhood**."
                "\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version="v1.0"
)


def remove_file(delay: int, filepath: str) -> NoReturn:
    """Deletes the requested file after a certain time.

    Args:
        delay: Delay in seconds after which the requested file is to be deleted.
        filepath: Filepath that has to be removed.
    """
    time.sleep(delay)
    os.remove(filepath) if os.path.isfile(filepath) else logger.error(f"{filepath} not found.")


def run_robinhood() -> NoReturn:
    """Runs in a dedicated process during startup, if the file was modified earlier than the past hour."""
    if os.path.isfile(fileio.robinhood):
        modified = int(os.stat(fileio.robinhood).st_mtime)
        logger.info(f"{fileio.robinhood} was generated on {datetime.fromtimestamp(modified).strftime('%c')}.")
        if int(time.time()) - modified < 3_600:  # generates new file only if the file is older than an hour
            return
    logger.info('Initiated robinhood gatherer.')
    Investment(logger=logger).report_gatherer()


async def enable_cors() -> NoReturn:
    """Allow ``CORS: Cross-Origin Resource Sharing`` to allow restricted resources on the API."""
    logger.info('Setting CORS policy.')
    origins = [
        "http://localhost.com",
        "https://localhost.com",
        f"http://{env.website}",
        f"https://{env.website}",
        f"http://{env.website}/*",
        f"https://{env.website}/*",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex='https://.*\.ngrok\.io/*',  # noqa: W605
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event(event_type='startup')
async def start_robinhood() -> Any:
    """Initiates robinhood gatherer in a process and adds a cron schedule if not present already."""
    await enable_cors()
    logger.info(f'Hosting at http://{env.offline_host}:{env.offline_port}')
    if all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
        Process(target=run_robinhood).start()
        if env.macos:
            from api.cron import CronScheduler
            CronScheduler(logger=logger).controller()


@app.get(path="/", response_class=RedirectResponse, include_in_schema=False)
async def redirect_index() -> str:
    """Redirect to docs in ``read-only`` mode.

    Returns:
        str:
        Redirects the root endpoint ``/`` url to read-only docs location.
    """
    return app.redoc_url


@app.post(path='/speech-synthesis', response_class=RedirectResponse, dependencies=OFFLINE_PROTECTOR)
async def speech_synthesis(text: str) -> FileResponse:
    """Process request to convert text to speech if docker container is running.

    Returns:
        FileResponse:
        Audio file to be downloaded.

    Raises:
        - 404: If audio file was not found after successful response.
        - 500: If the connection fails.
    """
    try:
        response = requests.get(url=f"http://localhost:{env.speech_synthesis_port}", timeout=1)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
        logger.error(error)
        raise APIResponse(status_code=500, detail=error)
    if response.ok:
        if not speaker.speech_synthesizer(text=text, timeout=len(text)):
            logger.error("Speech synthesis could not process the request.")
            raise APIResponse(status_code=500, detail=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        if os.path.isfile(path=fileio.speech_synthesis_wav):
            Thread(target=remove_file, kwargs={'delay': 2, 'filepath': fileio.speech_synthesis_wav}).start()
            return FileResponse(path=fileio.speech_synthesis_wav, media_type='application/octet-stream',
                                filename="synthesized.wav")
        logger.error(f'File Not Found: {fileio.speech_synthesis_wav}')
        raise APIResponse(status_code=404, detail=http_status.HTTP_404_NOT_FOUND)
    logger.error(f"{response.status_code}::{response.url} - {response.text}")
    raise APIResponse(status_code=response.status_code, detail=response.text)


@app.get(path="/health", include_in_schema=False)
async def health() -> NoReturn:
    """Health Check for OfflineCommunicator."""
    raise APIResponse(status_code=200, detail=http_status.HTTP_200_OK)


@app.post(path="/offline-communicator", dependencies=OFFLINE_PROTECTOR)
async def offline_communicator_api(input_data: GetData) -> NoReturn:
    """Offline Communicator API endpoint for Jarvis.

    Args:
        - input_data: Takes the following arguments as data instead of a QueryString.

            - command: The task which Jarvis has to do.

    Raises:
        - 200: A dictionary with the command requested and the response for it from Jarvis.
        - 413: If request command has 'and' or 'also' in the phrase.
        - 422: If the request is not part of offline compatible words.

    See Also:
        - Keeps waiting for the record ``response`` in the database table ``offline``
    """
    if not (command := input_data.command.strip()):
        raise APIResponse(status_code=204, detail='Empy requests cannot be processed.')

    command_lower = command.lower()
    if 'alarm' in command_lower or 'remind' in command_lower:
        command = command_lower
    else:
        command = command.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string
    if command_lower == 'test':
        raise APIResponse(status_code=200, detail='Test message received.')
    if 'and' in command.split() or 'also' in command.split():
        raise APIResponse(status_code=413,
                          detail='Jarvis can only process one command at a time via offline communicator.')
    if 'after' in command.split():
        raise APIResponse(status_code=413,
                          detail='Jarvis cannot perform tasks at a later time using offline communicator.')
    if not any(word in command_lower for word in offline_compatible):
        raise APIResponse(status_code=422,
                          detail=f'"{command}" is not a part of offline communicator compatible request.\n\n'
                                 'Please try an instruction that does not require an user interaction.')

    # # Alternate way for datetime conversions without first specifying a local timezone
    # import dateutil.tz
    # dt_string = datetime.now().astimezone(dateutil.tz.tzlocal()).strftime("%A, %B %d, %Y %H:%M:%S")
    dt_string = datetime.now().astimezone(tz=shared.LOCAL_TIMEZONE).strftime("%A, %B %d, %Y %H:%M:%S")
    response = offline_communicator(command=command)
    raise APIResponse(status_code=200, detail=f'{dt_string}\n\n{response}')


@app.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse('favicon.ico')


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
    @app.post(path="/robinhood-authenticate", dependencies=ROBINHOOD_PROTECTOR)
    async def authenticate_robinhood() -> NoReturn:
        """Authenticates the request. Uses a two-factor authentication by generating single use tokens.

        Raises:
            200: If initial auth is successful and returns the single-use token.

        See Also:
            If basic auth (stored as an env var ``robinhood_endpoint_auth``) succeeds:

            - Returns ``?token=HASHED_UUID`` to access ``/investment`` accessed via ``/?investment?token=HASHED_UUID``
            - Also stores the token in the dictionary ``robinhood_token`` which is verified in the path ``/investment``
            - The token is deleted from env var as soon as it is verified, making page-refresh useless.
        """
        robinhood_token['token'] = support.token()
        raise APIResponse(status_code=200, detail=f"?token={robinhood_token['token']}")


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
    @app.get(path="/investment", response_class=HTMLResponse, include_in_schema=False)
    async def robinhood(token: str = None) -> HTMLResponse:
        """Serves static file.

        Args:
            token: Takes custom auth token as an argument.

        Returns:
            HTMLResponse:
            Renders the html page.

        See Also:
            - This endpoint is secured behind two-factor authentication.
            - Initial check is done by the function authenticate_robinhood behind the path "/robinhood-authenticate"
            - Once the auth succeeds, a one-time usable hashed-uuid is generated and stored as an environment variable.
            - This UUID is sent as response to the API endpoint behind ngrok tunnel.
            - The UUID is deleted from env var as soon as the argument is checked for the first time.
            - Page refresh doesn't work because the env var is deleted as soon as it is authed once.
        """
        if not token:
            raise APIResponse(status_code=400, detail='Request needs to be authorized with a single-use token.')
        if token == robinhood_token['token']:
            robinhood_token['token'] = ''
            if not os.path.isfile(fileio.robinhood):
                raise APIResponse(status_code=404, detail='Static file was not found on server.')
            with open(fileio.robinhood) as static_file:
                html_content = static_file.read()
            content_type, _ = mimetypes.guess_type(html_content)
            return HTMLResponse(content=html_content, media_type=content_type)  # serves as a static webpage
        else:
            logger.warning('/investment was accessed with an expired token.')
            raise APIResponse(status_code=419,
                              detail='Session expired. Requires authentication since endpoint uses single-use token.')
