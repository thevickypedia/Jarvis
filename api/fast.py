from datetime import datetime
from logging import getLogger
from logging.config import dictConfig
from mimetypes import guess_type
from os import environ, path, remove, stat
from threading import Thread, current_thread, get_ident
from time import sleep

from controller import (EndpointFilter, InvestmentFilter, keygen,
                        offline_compatible)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from models import GetData, GetPasscode, LogConfig
from pytz import timezone
from robinhood import Investment
from yaml import FullLoader, load

if path.isfile('../.env'):
    load_dotenv(dotenv_path='../.env', verbose=True)

dictConfig(LogConfig().dict())

getLogger("uvicorn.access").addFilter(EndpointFilter())
getLogger("uvicorn.access").addFilter(InvestmentFilter())
logger = getLogger('jarvis')

serve_file = 'robinhood.html'

app = FastAPI(
    title="Jarvis API",
    description="API to interact with Jarvis",
    version="v1.0"
)

website = environ.get('website', 'thevickypedia.com')

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


offline_compatible = offline_compatible()
zone = None
if path.isfile('../location.yaml'):
    location_details = load(open('../location.yaml'), Loader=FullLoader)
    zone = timezone(location_details.get('timezone'))


def run_robinhood(thread: int = None):
    """Initiates report gatherer and sleeps for 55 minutes."""
    logger.info(f'Initiated robinhood gatherer [{thread}]')
    Investment(logger=logger).report_gatherer()


def execute_sleep(timer: int) -> None:
    """Using a for loop instead of regular sleep to make sure daemon thread exits when STOPPER flag is set.

    Args:
        timer: Takes the amount of time sleep has to be executed as an argument.
    """
    for _ in range(timer):
        if environ.get('STOPPER'):
            break
        sleep(1)


def rh_initiator(startup: bool = False):
    """Runs in a dedicated thread at a set schedule.

    Args:
        startup: Boolean flag to indicate that an initial run is required.

    See Also:
        Schedule: Runs every hour on weekdays 8 AM to 4 PM CentralTime
    """
    thread_id = get_ident() or current_thread().ident
    if startup:
        if path.isfile(serve_file) and int(datetime.now().timestamp()) - int(stat(serve_file).st_mtime) < 3_600:
            last_modified = datetime.fromtimestamp(int(stat(serve_file).st_mtime)).strftime('%c')
            logger.info(f'{serve_file} was generated on {last_modified}.')
        else:
            logger.info('Starting portfolio gatherer to create static html file.')
            run_robinhood(thread=thread_id)

    while True:
        if environ.get('STOPPER'):
            logger.info(f'Stopping thread: {thread_id}')
            break

        if not datetime.today().isoweekday():
            # Sleeps for 8 hours, since in worse case scenario checker runs at 12 AM, 8 AM is the next run
            execute_sleep(timer=28_800)
            continue

        am_hours = ['08', '09', '10', '11']
        pm_hours = ['12', '01', '02', '03', '04']
        avoid_hours = ['05', '06', '07']

        time_now = datetime.now()
        hour = time_now.strftime("%I")
        minute = time_now.strftime("%M")
        am_pm = time_now.strftime("%p")

        if hour in avoid_hours:
            continue

        if ((hour in am_hours and am_pm == 'AM') or (hour in pm_hours and am_pm == 'PM')) and minute == '00':
            logger.info(f'Current time: {hour}:{minute} {am_pm}')
            logger.info('Starting Robinhood gatherer to create static html file.')
            run_robinhood(thread=thread_id)
            execute_sleep(timer=3_300)  # 55 minutes wait after each run


@app.on_event(event_type='startup')
async def get_compatible():
    """Calls startup method to add the list of acceptable keywords for offline_compatible."""
    Thread(target=rh_initiator, args=[True], daemon=True).start()


@app.on_event(event_type='shutdown')
async def stop_robinhood():
    """Stop the thread that creates robinhood static file in the background."""
    environ['STOPPER'] = 'True'


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def redirect_index() -> str:
    """Redirect to documents.

    Returns:
        str:
        Redirects `/` url to `/docs`
    """
    return '/docs'


@app.get('/status', include_in_schema=False)
def status() -> dict:
    """Health Check for OfflineCommunicator.

    Returns:
        dict:
        Health status in a dictionary.
    """
    return {'Message': 'Healthy'}


@app.post("/offline-communicator")
def jarvis_offline_communicator(input_data: GetData):
    """# Offline Communicator for Jarvis.

    ## Args:
        - input_data: - Takes the following arguments as data instead of a QueryString.
            - command: The task which Jarvis has to do.
            - passphrase: Pass phrase for authentication.

    ## Returns:
        - A dictionary with the command requested and the response for it from Jarvis.

    ## See Also:
        - Include response_model only when the response should have same keys as arguments
            - @app.post("/offline-communicator", response_model=GetData)
        - Keeps waiting until Jarvis sends a response back by creating the offline_response file.
        - This response will be sent as raising a HTTPException with status code 200.
    """
    passphrase = input_data.phrase
    command = input_data.command
    if passphrase.startswith('\\'):  # Since passphrase is converted to Hexadecimal using a JavaScript in JarvisHelper
        passphrase = bytes(passphrase, "utf-8").decode(encoding="unicode_escape")
    if passphrase == environ.get('offline_phrase'):
        command_lower = command.lower()
        command_split = command.split()
        if command_lower == 'test':
            current_time_ = datetime.now(zone)
            dt_string = current_time_.strftime("%A, %B %d, %Y %I:%M:%S %p")
            raise HTTPException(status_code=200, detail=f'Test message was received on {dt_string}.')
        elif 'and' in command_split or 'also' in command_split:
            raise HTTPException(status_code=413,
                                detail='Jarvis can only process one command at a time via offline communicator.')
        else:
            if any(word in command_lower for word in offline_compatible):
                with open('../offline_request', 'w') as off_request:
                    off_request.write(command)
                if 'restart' in command:
                    raise HTTPException(status_code=200,
                                        detail='Restarting now sir! I will be up and running momentarily.')
                while True:
                    # todo: Consider async functions and await instead of hard-coded sleepers
                    if path.isfile('../offline_response'):
                        sleep(0.3)  # Read file after half a second for the content to be written
                        with open('../offline_response', 'r') as off_response:
                            response = off_response.read()
                        if response:
                            remove('../offline_response')
                            raise HTTPException(status_code=200, detail=response)
                        else:
                            raise HTTPException(status_code=409, detail='Received empty payload from Jarvis.')
            else:
                raise HTTPException(status_code=422,
                                    detail=f'"{command}" is not a part of offline communicator compatible request.\n\n'
                                           'Please try an instruction that does not require an user interaction.')
    else:
        raise HTTPException(status_code=401, detail='Request not authorized.')


@app.get("/robinhood_bg.jpg", include_in_schema=False)
async def get_background() -> FileResponse:
    """Gets the robinhood_bg.jpg and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the robinhood_bg.jpg to support the robinhood script's robinhood.html.
    """
    if path.isfile('robinhood_bg.jpg'):
        return FileResponse('robinhood_bg.jpg')


@app.post("/robinhood-authenticate")
def authenticate_robinhood_report_gatherer(feeder: GetPasscode):
    """# Authenticates the request. Uses a two-factor authentication by generating single use tokens.

    ## Args:
        feeder: Takes the following arguments as dataString instead of a QueryString.
            - passphrase: Pass phrase for authentication.

    ## Raises:
        - Status code: 200, if initial auth is successful and returns the single-use token.
        - Status code: 401, if request is not authorized.

    ## See Also:
        If basic (auth stored as an env var "robinhood_auth") succeeds:
            - Returns "?token=HASHED_UUID" which can be used to access "/investment" by "/?investment?token=HASHED_UUID"
            - Also stores the token as an env var "robinhood_token" which is verified in the path "/investment"
            - The token is deleted from env var as soon as it is verified, making page-refresh useless.
    """
    environ['robinhood_token'] = keygen()
    passcode = feeder.phrase
    if not passcode:
        raise HTTPException(status_code=500, detail='Passcode was not received.')
    if passcode.startswith('\\'):  # Since passphrase is converted to Hexadecimal using a JavaScript in JarvisHelper
        passcode = bytes(passcode, "utf-8").decode(encoding="unicode_escape")
    if passcode == environ.get('robinhood_auth'):
        raise HTTPException(status_code=200, detail=f"?token={environ.get('robinhood_token')}")
    else:
        raise HTTPException(status_code=401, detail='Request not authorized.')


@app.get("/investment", response_class=HTMLResponse, include_in_schema=False)
async def robinhood(token: str = None):
    """Serves static file.

    Args:
        token: Takes custom auth token as an argument.

    See Also:
        - This endpoint is secured behind two factor authentication.
        - Initial check is done by the function robinhood_auth behind the path "/robinhood-authenticate"
        - Once the auth succeeds, a one-time usable hashed-uuid is generated and stored as an environment variable.
        - This UUID is sent as response to the API endpoint behind ngrok tunnel.
        - The UUID is deleted from env var as soon as the argument is checked for the first time.
        - Page refresh doesn't work because the env var is deleted as soon as it is authed once.
    """
    if not token:
        raise HTTPException(status_code=400, detail='Request needs to be authorized with a single-use token.')
    if token == environ.get('robinhood_token'):
        if not path.isfile(serve_file):
            raise HTTPException(status_code=404, detail='Static file was not found on server.')
        del environ['robinhood_token']
        with open(serve_file) as static_file:
            html_content = static_file.read()
        content_type, _ = guess_type(html_content)
        return HTMLResponse(content=html_content, media_type=content_type)  # serves as a static webpage
    else:
        logger.warning('/investment was accessed with an expired token.')
        raise HTTPException(status_code=401,
                            detail='Session expired. Requires authentication since endpoint uses single-use token.')


if __name__ == '__main__':
    from uvicorn import run

    run(app="fast:app", port=4483, reload=True)
