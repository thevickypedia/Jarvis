import os
import sys
from datetime import datetime
from logging import config, getLogger
from mimetypes import guess_type
from pathlib import PurePath
from socket import gethostbyname
from string import punctuation
from subprocess import check_output
from threading import Thread
from time import sleep

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pytz import timezone
from yaml import FullLoader, load

sys.path.append('..')
from api.controller import keygen, offline_compatible  # noqa: E402
from api.cron import CronScheduler  # noqa: E402
from api.filters import EndpointFilter, InvestmentFilter  # noqa: E402
from api.models import GetData, GetPhrase, LogConfig  # noqa: E402
from api.report_gatherer import Investment  # noqa: E402

sys.path.remove('..')

if os.path.isfile('../.env'):
    load_dotenv(dotenv_path='../.env', verbose=True)

if not os.path.isdir('logs'):
    os.system('mkdir logs')

if os.environ.get('NEVER_MATCH'):
    config.dictConfig(config=LogConfig().dict())

offline_host = gethostbyname('localhost')
offline_port = int(os.environ.get('offline_port', 4483))
offline_phrase = os.environ.get('offline_phrase', 'jarvis')

rh_env_vars = all([os.environ.get('robinhood_user'), os.environ.get('robinhood_pass'), os.environ.get('robinhood_qr')])
robinhood_token = {'token': None}
robinhood_auth = os.environ.get('robinhood_auth', 'robinhood')

offline_compatible = offline_compatible()

getLogger("uvicorn.access").addFilter(EndpointFilter())
getLogger("uvicorn.access").addFilter(InvestmentFilter())
logger = getLogger('uvicorn')

serve_file = 'robinhood.html'

app = FastAPI(
    title="Jarvis API",
    description="Handles offline communication with **Jarvis** and generates a one time auth token for **Robinhood**."
                "\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version="v1.0"
)

zone = None
if os.path.isfile('../location.yaml'):
    location_details = load(open('../location.yaml'), Loader=FullLoader)
    zone = timezone(location_details.get('timezone'))


def get_jarvis_status() -> bool:
    """Checks process information to see if Jarvis is running.

    Returns:
        bool:
        A boolean True flag is jarvis.py is found in the list of current PIDs.
    """
    pid_check = check_output("ps -ef | grep jarvis.py", shell=True)
    pid_list = pid_check.decode('utf-8').splitlines()
    for pid_info in pid_list:
        if pid_info and 'grep' not in pid_info and '/bin/sh' not in pid_info:
            return True


def run_robinhood() -> None:
    """Runs in a dedicated thread during startup, if the file was modified earlier than the past hour."""
    if os.path.isfile(serve_file):
        modified = int(os.stat(serve_file).st_mtime)
        logger.info(f"{serve_file} was generated on {datetime.fromtimestamp(modified).strftime('%c')}.")
        if int(datetime.now().timestamp()) - modified > 3_600:
            Investment(logger=logger).report_gatherer()
    else:
        logger.info('Initiated robinhood gatherer.')
        Investment(logger=logger).report_gatherer()


async def auth_offline_communicator(passphrase: str, command: str) -> bool:
    """Runs pre-checks before letting office_communicator to proceed.

    Args:
        passphrase: Takes the password as one of the arguments.
        command: Takes the command to be processed as another argument.

    Raises:
        401: If auth failed.
        503: If Jarvis is not running.
        413: If request command has 'and' or 'also' in the phrase.
        422: If the request is not part of offline compatible words.
        200: If phrase is test.

    Returns:
        bool:
        If all the pre-checks have been successful.
    """
    command_lower = command.lower()
    command_split = command.split()
    if passphrase.startswith('\\'):  # Since passphrase is converted to Hexadecimal using a JavaScript in JarvisHelper
        passphrase = bytes(passphrase, "utf-8").decode(encoding="unicode_escape")
    if passphrase != offline_phrase:
        raise HTTPException(status_code=401, detail='Request not authorized.')
    if not get_jarvis_status():
        logger.error(f'Received offline request: {command}, but Jarvis is not running.')
        raise HTTPException(status_code=503, detail='Jarvis is currently un-reachable.')
    if command_lower == 'test':
        raise HTTPException(status_code=200, detail='Test message received.')
    if 'and' in command_split or 'also' in command_split:
        raise HTTPException(status_code=413,
                            detail='Jarvis can only process one command at a time via offline communicator.')
    if not any(word in command_lower for word in offline_compatible):
        raise HTTPException(status_code=422,
                            detail=f'"{command}" is not a part of offline communicator compatible request.\n\n'
                                   'Please try an instruction that does not require an user interaction.')
    return True


async def enable_cors() -> None:
    """Allow ``CORS: Cross-Origin Resource Sharing`` to allow restricted resources on the API."""
    logger.info('Setting CORS policy.')
    website = os.environ.get('website', 'thevickypedia.com')

    origins = [
        "http://localhost.com",
        "https://localhost.com",
        f"http://{website}",
        f"https://{website}",
        f"http://{website}/*",
        f"https://{website}/*",
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
async def start_robinhood() -> None:
    """Initiates robinhood gatherer in a thread and adds a cron schedule if not present already."""
    await enable_cors()
    logger.info(f'Hosting at http://{offline_host}:{offline_port}')
    if rh_env_vars:
        global thread  # noqa
        thread = Thread(target=run_robinhood, daemon=True)
        thread.start()
        CronScheduler(logger=logger).controller()


@app.on_event(event_type='shutdown')
async def stop_robinhood() -> None:
    """If active, stops the thread that creates robinhood static file in the background."""
    if thread.is_alive():
        logger.warning(f'Hanging thread: {thread.ident}')
        thread.join(timeout=3)


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def redirect_index() -> str:
    """Redirect to docs in ``read-only`` mode.

    Returns:
        str:
        Redirects the root endpoint ``/`` url to read-only docs location.
    """
    return app.redoc_url


@app.get('/status', include_in_schema=False)
async def status() -> dict:
    """Health Check for OfflineCommunicator.

    Returns:
        dict:
        Health status in a dictionary.
    """
    return {'Message': 'Healthy'}


@app.post("/offline-communicator")
async def offline_communicator(input_data: GetData) -> None:
    """Offline Communicator for Jarvis.

    Args:
        - input_data: Takes the following arguments as data instead of a QueryString.

            - command: The task which Jarvis has to do.
            - passphrase: Pass phrase for authentication.

    Raises:
        200: A dictionary with the command requested and the response for it from Jarvis.

    See Also:
        - Include response_model only when the response should have same keys as arguments
        - Keeps waiting until Jarvis sends a response back by creating the offline_response file.
        - This response will be sent as raising a HTTPException with status code 200.
    """
    passphrase = input_data.phrase
    command = input_data.command
    command = command.translate(str.maketrans('', '', punctuation))  # Remove punctuations from the str
    await auth_offline_communicator(passphrase=passphrase, command=command)

    with open('../offline_request', 'w') as off_request:
        off_request.write(command)
    dt_string = datetime.now(zone).strftime("%A, %B %d, %Y %I:%M:%S %p")
    if 'restart' in command:
        raise HTTPException(status_code=200,
                            detail='Restarting now sir! I will be up and running momentarily.')
    while True:
        if os.path.isfile('../offline_response'):
            sleep(0.1)  # Read file after 0.1 second for the content to be written
            with open('../offline_response', 'r') as off_response:
                response = off_response.read()
            if response:
                os.remove('../offline_response')
                raise HTTPException(status_code=200, detail=f'{dt_string}\n\n{response}')
            else:
                raise HTTPException(status_code=409, detail='Received empty payload from Jarvis.')


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse('favicon.ico')


if rh_env_vars:
    @app.post("/robinhood-authenticate")
    async def authenticate_robinhood(feeder: GetPhrase) -> None:
        """Authenticates the request. Uses a two-factor authentication by generating single use tokens.

        Args:
            feeder: Takes the following argument(s) as dataString instead of a QueryString.

                - passphrase: Pass phrase for authentication.

        Raises:
            200: If initial auth is successful and returns the single-use token.
            401: If request is not authorized.

        See Also:
            If basic auth (stored as an env var ``robinhood_auth``) succeeds:

            - Returns ``?token=HASHED_UUID`` to access ``/investment`` accessed via ``/?investment?token=HASHED_UUID``
            - Also stores the token in the dictionary ``robinhood_token`` which is verified in the path ``/investment``
            - The token is deleted from env var as soon as it is verified, making page-refresh useless.
        """
        robinhood_token['token'] = keygen() or None
        passcode = feeder.phrase
        if not passcode:
            raise HTTPException(status_code=500, detail='Passcode was not received.')
        if passcode.startswith('\\'):  # Since passphrase is converted to Hexadecimal using a JavaScript in JarvisHelper
            passcode = bytes(passcode, "utf-8").decode(encoding="unicode_escape")
        if passcode == robinhood_auth:
            raise HTTPException(status_code=200, detail=f"?token={robinhood_token['token']}")
        else:
            raise HTTPException(status_code=401, detail='Request not authorized.')


if rh_env_vars:
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
            - Initial check is done by the function robinhood_auth behind the path "/robinhood-authenticate"
            - Once the auth succeeds, a one-time usable hashed-uuid is generated and stored as an environment variable.
            - This UUID is sent as response to the API endpoint behind ngrok tunnel.
            - The UUID is deleted from env var as soon as the argument is checked for the first time.
            - Page refresh doesn't work because the env var is deleted as soon as it is authed once.
        """
        if not token:
            raise HTTPException(status_code=400, detail='Request needs to be authorized with a single-use token.')
        if token == robinhood_token['token']:
            robinhood_token['token'] = None
            if not os.path.isfile(serve_file):
                raise HTTPException(status_code=404, detail='Static file was not found on server.')
            with open(serve_file) as static_file:
                html_content = static_file.read()
            content_type, _ = guess_type(html_content)
            return HTMLResponse(content=html_content, media_type=content_type)  # serves as a static webpage
        else:
            logger.warning('/investment was accessed with an expired token.')
            raise HTTPException(status_code=401,
                                detail='Session expired. Requires authentication since endpoint uses single-use token.')


if __name__ == '__main__':
    argument_dict = {
        "app": f"{PurePath(__file__).stem or __name__}:app",
        "host": offline_host,
        "port": offline_port,
        "reload": True
    }
    uvicorn.run(**argument_dict)
