import importlib
import logging
import mimetypes
import os
import string
from datetime import datetime, timezone
from logging.config import dictConfig
from multiprocessing import Process
from pathlib import Path
from typing import Any, NoReturn

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from api import authenticator, cron
from api.controller import keygen, offline_compatible
from api.models import GetData, InvestmentFilter
from api.report_gatherer import Investment
from modules.database import database
from modules.models import config, models

env = models.env
db = database.Database(table_name='offline', columns=['key', 'value'])

OFFLINE_PROTECTOR = [Depends(dependency=authenticator.offline_has_access)]
ROBINHOOD_PROTECTOR = [Depends(dependency=authenticator.robinhood_has_access)]

robinhood_token = {'token': ''}

if not os.path.isfile(config.APIConfig().ACCESS_LOG_FILENAME):
    Path(config.APIConfig().ACCESS_LOG_FILENAME).touch()

if not os.path.isfile(config.APIConfig().DEFAULT_LOG_FILENAME):
    Path(config.APIConfig().DEFAULT_LOG_FILENAME).touch()

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo

offline_compatible = offline_compatible()

importlib.reload(module=logging)
dictConfig(config=config.APIConfig().LOGGING_CONFIG)

logging.getLogger("uvicorn.access").addFilter(InvestmentFilter())  # Adds token filter to the access logger
logging.getLogger("uvicorn.access").propagate = False  # Disables access logger in default logger to log independently

logger = logging.getLogger('uvicorn.default')

serve_file = 'api/robinhood.html'

app = FastAPI(
    title="Jarvis API",
    description="Handles offline communication with **Jarvis** and generates a one time auth token for **Robinhood**."
                "\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version="v1.0"
)


def run_robinhood() -> NoReturn:
    """Runs in a dedicated process during startup, if the file was modified earlier than the past hour."""
    if os.path.isfile(serve_file):
        modified = int(os.stat(serve_file).st_mtime)
        logger.info(f"{serve_file} was generated on {datetime.fromtimestamp(modified).strftime('%c')}.")
        if int(datetime.now().timestamp()) - modified < 3_600:
            return
    else:
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
        cron.CronScheduler(logger=logger).controller()


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def redirect_index() -> str:
    """Redirect to docs in ``read-only`` mode.

    Returns:
        str:
        Redirects the root endpoint ``/`` url to read-only docs location.
    """
    return app.redoc_url


@app.get('/health', include_in_schema=False)
async def health() -> NoReturn:
    """Health Check for OfflineCommunicator."""
    raise HTTPException(status_code=200, detail=status.HTTP_200_OK)


@app.post("/offline-communicator", dependencies=OFFLINE_PROTECTOR)
async def offline_communicator(input_data: GetData) -> NoReturn:
    """Offline Communicator for Jarvis.

    Args:
        - input_data: Takes the following arguments as data instead of a QueryString.

            - command: The task which Jarvis has to do.

    Raises:
        - 200: A dictionary with the command requested and the response for it from Jarvis.
        - 413: If request command has 'and' or 'also' in the phrase.
        - 422: If the request is not part of offline compatible words.

    See Also:
        - Keeps waiting for the record ``response`` in the database table ``offline``
        - This response will be sent as raising a ``HTTPException`` with status code 200.
    """
    if not (command := input_data.command.strip()):
        raise HTTPException(status_code=204, detail='Empy requests cannot be processed.')

    command = command.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string
    if command.lower() == 'test':
        raise HTTPException(status_code=200, detail='Test message received.')
    if 'and' in command.split() or 'also' in command.split():
        raise HTTPException(status_code=413,
                            detail='Jarvis can only process one command at a time via offline communicator.')
    if 'after' in command.split():
        raise HTTPException(status_code=413,
                            detail='Jarvis cannot perform tasks at a later time using offline communicator.')
    if not any(word in command.lower() for word in offline_compatible):
        raise HTTPException(status_code=422,
                            detail=f'"{command}" is not a part of offline communicator compatible request.\n\n'
                                   'Please try an instruction that does not require an user interaction.')
    if existing := db.cursor.execute("SELECT value from offline WHERE key=?", ('request',)).fetchone():
        raise HTTPException(status_code=503,
                            detail=f"Processing another offline request: '{existing[0]}'.\nPlease try again.")
    db.cursor.execute(f"INSERT OR REPLACE INTO offline (key, value) VALUES {('request', command)}")
    db.connection.commit()

    dt_string = datetime.now().astimezone(tz=LOCAL_TIMEZONE).strftime("%A, %B %d, %Y %H:%M:%S")
    while True:
        if response := db.cursor.execute("SELECT value from offline WHERE key=?", ('response',)).fetchone():
            db.cursor.execute("DELETE FROM offline WHERE key=:key OR value=:value ",
                              {'key': 'response', 'value': response[0]})
            db.connection.commit()
            raise HTTPException(status_code=200, detail=f'{dt_string}\n\n{response[0]}')


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse('favicon.ico')


if os.getcwd().split('/')[-1] != 'Jarvis' or all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
    @app.post("/robinhood-authenticate", dependencies=ROBINHOOD_PROTECTOR)
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
        robinhood_token['token'] = keygen()
        raise HTTPException(status_code=200, detail=f"?token={robinhood_token['token']}")

if os.getcwd().split('/')[-1] != 'Jarvis' or all([env.robinhood_user, env.robinhood_pass, env.robinhood_pass]):
    @app.get("/investment", response_class=HTMLResponse, include_in_schema=False)
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
            raise HTTPException(status_code=400, detail='Request needs to be authorized with a single-use token.')
        if token == robinhood_token['token']:
            robinhood_token['token'] = ''
            if not os.path.isfile(serve_file):
                raise HTTPException(status_code=404, detail='Static file was not found on server.')
            with open(serve_file) as static_file:
                html_content = static_file.read()
            content_type, _ = mimetypes.guess_type(html_content)
            return HTMLResponse(content=html_content, media_type=content_type)  # serves as a static webpage
        else:
            logger.warning('/investment was accessed with an expired token.')
            raise HTTPException(status_code=419,
                                detail='Session expired. Requires authentication since endpoint uses single-use token.')
