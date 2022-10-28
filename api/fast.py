import asyncio
import imghdr
import importlib
import logging
import mimetypes
import os
import pathlib
import string
import time
from datetime import datetime
from http import HTTPStatus
from logging.config import dictConfig
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any, Dict, List, NoReturn, Union

import jinja2
import jwt
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (FileResponse, HTMLResponse, RedirectResponse,
                               StreamingResponse)
from webull import webull

from api import squire
from api.authenticator import (OFFLINE_PROTECTOR, ROBINHOOD_PROTECTOR,
                               STOCK_PROTECTOR, SURVEILLANCE_PROTECTOR)
from api.models import (CameraIndexModal, OfflineCommunicatorModal,
                        SpeechSynthesisModal, StockMonitorModal)
from api.report_gatherer import Investment
from api.settings import (ConnectionManager, robinhood, stock_monitor,
                          surveillance)
from executors.commander import timed_delay
from executors.offline import offline_communicator
from executors.word_match import word_match
from modules.audio import speaker, tts_stt
from modules.conditions import conversation, keywords
from modules.database import database
from modules.exceptions import APIResponse, CameraError
from modules.logger import config
from modules.models import models
from modules.offline import compatibles
from modules.templates import templates
from modules.utils import support

# Creates log files
if not os.path.isfile(config.APIConfig().ACCESS_LOG_FILENAME):
    pathlib.Path(config.APIConfig().ACCESS_LOG_FILENAME).touch()

if not os.path.isfile(config.APIConfig().DEFAULT_LOG_FILENAME):
    pathlib.Path(config.APIConfig().DEFAULT_LOG_FILENAME).touch()

# Get offline compatible and websocket loaded
offline_compatible = compatibles.offline_compatible()
ws_manager = ConnectionManager()

# Configure logging
importlib.reload(module=logging)
LOGGING = config.APIConfig()
dictConfig(config=LOGGING.LOG_CONFIG)
logging.getLogger("uvicorn.access").propagate = False  # Disables access logger in default logger to log independently
logger = logging.getLogger('uvicorn.default')

# Initiate api
app = FastAPI(
    title="Jarvis API",
    description="Handles offline communication with **Jarvis** and generates a one time auth token for "
                "**Robinhood** and **Surveillance endpoints.\n\n"
                "**Contact:** [https://vigneshrao.com/contact](https://vigneshrao.com/contact)",
    version="v1.0"
)

# Setup databases
db = database.Database(database=models.fileio.base_db)
stock_db = database.Database(database=models.fileio.stock_db)
stock_db.create_table(table_name="stock", columns=stock_monitor.user_info)


async def enable_cors() -> NoReturn:
    """Allow ``CORS: Cross-Origin Resource Sharing`` to allow restricted resources on the API."""
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
    from modules.logger.custom_logger import logger
    config.multiprocessing_logger(filename=LOGGING.DEFAULT_LOG_FILENAME,
                                  log_format=logging.Formatter(fmt=LOGGING.DEFAULT_LOG_FORMAT))
    await enable_cors()
    squire.nasdaq()
    logger.info(f'Hosting at http://{models.env.offline_host}:{models.env.offline_port}')
    if all([models.env.robinhood_user, models.env.robinhood_pass, models.env.robinhood_pass]):
        Process(target=run_robinhood).start()


@app.get(path="/", response_class=RedirectResponse, include_in_schema=False)
async def redirect_index() -> str:
    """Redirect to docs in ``read-only`` mode.

    Returns:
        str:
        Redirects the root endpoint ``/`` url to read-only doc location.
    """
    return app.redoc_url


@app.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse(filename='favicon.ico', path=os.getcwd(), status_code=HTTPStatus.OK.real)


@app.post(path='/keywords', dependencies=OFFLINE_PROTECTOR)
async def _keywords() -> Dict[str, List[str]]:
    """Converts the keywords.py file into a dictionary of key-value pairs.

    Returns:
        dict:
        Key-value pairs of the keywords file.
    """
    return {k: v for k, v in keywords.__dict__.items() if isinstance(v, list)}


@app.post(path='/conversation', dependencies=OFFLINE_PROTECTOR)
async def _conversations() -> Dict[str, List[str]]:
    """Converts the conversation.py file into a dictionary of key-value pairs.

    Returns:
        dict:
        Key-value pairs of the conversation file.
    """
    return {k: v for k, v in conversation.__dict__.items() if isinstance(v, list)}


@app.post(path='/api-compatible', dependencies=OFFLINE_PROTECTOR)
async def _offline_compatible() -> Dict[str, List[str]]:
    """Returns the list of api compatible words.

    Returns:
        dict:
        Returns the list of api-compatible words as a dictionary.
    """
    return {"compatible": offline_compatible}


@app.post(path='/speech-synthesis', response_class=FileResponse, dependencies=OFFLINE_PROTECTOR)
async def speech_synthesis(input_data: SpeechSynthesisModal, raise_for_status: bool = True) -> \
        Union[FileResponse, None]:
    """Process request to convert text to speech if docker container is running.

    Args:
        - input_data: Takes the following arguments as ``GetText`` class instead of a QueryString.

            - text: Text to be processed with speech synthesis.
            - timeout: Timeout for speech-synthesis API call.
            - quality: Quality of audio conversion.
            - voice: Voice model ot be used.

    Returns:
        FileResponse:
        Audio file to be downloaded.

    Raises:
        - 404: If audio file was not found after successful response.
        - 500: If the connection to speech synthesizer fails.
        - 204: If speech synthesis file wasn't found.
    """
    if not (text := input_data.text.strip()):
        logger.error('Empty requests cannot be processed.')
        if raise_for_status:
            raise APIResponse(status_code=HTTPStatus.NO_CONTENT.real, detail=HTTPStatus.NO_CONTENT.__dict__['phrase'])
        else:
            return
    if not speaker.speech_synthesizer(text=text, timeout=input_data.timeout or len(text), quality=input_data.quality,
                                      voice=input_data.voice):
        logger.error("Speech synthesis could not process the request.")
        if raise_for_status:
            raise APIResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.real,
                              detail=HTTPStatus.INTERNAL_SERVER_ERROR.__dict__['phrase'])
        else:
            return
    if os.path.isfile(path=models.fileio.speech_synthesis_wav):
        Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': models.fileio.speech_synthesis_wav}).start()
        return FileResponse(path=models.fileio.speech_synthesis_wav, media_type='application/octet-stream',
                            filename="synthesized.wav", status_code=HTTPStatus.OK.real)
    logger.error(f'File Not Found: {models.fileio.speech_synthesis_wav}')
    if raise_for_status:
        raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.__dict__['phrase'])


@app.get(path="/health", include_in_schema=False)
async def health() -> NoReturn:
    """Health Check for OfflineCommunicator."""
    raise APIResponse(status_code=HTTPStatus.OK, detail=HTTPStatus.OK.__dict__['phrase'])


@app.post(path="/offline-communicator", dependencies=OFFLINE_PROTECTOR)
async def offline_communicator_api(request: Request, input_data: OfflineCommunicatorModal) -> \
        Union[FileResponse, NoReturn]:
    """Offline Communicator API endpoint for Jarvis.

    Args:
        - request: Takes the ``Request`` class as an argument.
        - input_data: Takes the following arguments as ``OfflineCommunicatorModal`` class instead of a QueryString.

            - command: The task which Jarvis has to do.
            - native_audio: Whether the response should be as an audio file with the server's voice.
            - speech_timeout: Timeout to process speech-synthesis.

    Raises:
        - 200: A dictionary with the command requested and the response for it from Jarvis.
        - 204: If empty command was received.
        - 422: If the request is not part of offline compatible words.

    See Also:
        - Keeps waiting for the record ``response`` in the database table ``offline``
    """
    logger.info(f"Connection received from {request.client.host} via {request.headers.get('host')} using "
                f"{request.headers.get('user-agent')}")
    if not (command := input_data.command.strip()):
        raise APIResponse(status_code=HTTPStatus.NO_CONTENT.real, detail=HTTPStatus.NO_CONTENT.__dict__['phrase'])

    logger.info(f"Request: {command}")
    if 'alarm' in command.lower() or 'remind' in command.lower():
        command = command.lower()
    else:
        command = command.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string
    if command.lower() == 'test':
        logger.info("Test message received.")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail="Test message received.")

    if ' and ' in command and not word_match(phrase=command, match_list=keywords.avoid):
        and_response = ""
        for each in command.split(' and '):
            if not word_match(phrase=each, match_list=offline_compatible):
                logger.warning(f"{each!r} is not a part of offline compatible request.")
                and_response += f'{each!r} is not a part of off-line communicator compatible request.\n\n' \
                                'Please try an instruction that does not require an user interaction.'
            else:
                try:
                    and_response += f"{offline_communicator(command=each)}\n"
                except Exception as error:
                    logger.error(error)
                    and_response += error.__str__()
        logger.info(f"Response: {and_response}")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=and_response)
    elif ' also ' in command and not word_match(phrase=command, match_list=keywords.avoid):
        also_response = ""
        for each in command.split(' also '):
            if not word_match(phrase=each, match_list=offline_compatible):
                logger.warning(f"{each!r} is not a part of offline compatible request.")
                also_response += f'{each!r} is not a part of off-line communicator compatible request.\n\n' \
                                 'Please try an instruction that does not require an user interaction.'
            else:
                try:
                    also_response = f"{offline_communicator(command=each)}\n"
                except Exception as error:
                    logger.error(error)
                    also_response += error.__str__()
        logger.info(f"Response: {also_response}")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=also_response)
    if not word_match(phrase=command, match_list=offline_compatible):
        logger.warning(f"{command!r} is not a part of offline compatible request.")
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f'"{command}" is not a part of off-line communicator compatible request.\n\n'
                                 'Please try an instruction that does not require an user interaction.')
    if ' after ' in command.lower():
        if delay_info := timed_delay(phrase=command):
            logger.info(f"{delay_info[0]!r} will be executed after {support.time_converter(seconds=delay_info[1])}")
            raise APIResponse(status_code=HTTPStatus.OK.real,
                              detail=f'I will execute it after {support.time_converter(seconds=delay_info[1])} '
                                     f'{models.env.title}!')
    try:
        response = offline_communicator(command=command)
    except Exception as error:
        logger.error(error)
        response = error.__str__()
    logger.info(f"Response: {response}")
    if os.path.isfile(response) and response.endswith('.jpg'):
        logger.info("Response received as a file.")
        Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': response}).start()
        return FileResponse(path=response, media_type=f'image/{imghdr.what(file=response)}',
                            filename=os.path.split(response)[-1], status_code=HTTPStatus.OK.real)
    if input_data.native_audio:
        native_audio_wav = tts_stt.text_to_audio(text=response)
        logger.info(f"Storing response as {native_audio_wav} in native audio.")
        Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': native_audio_wav}).start()
        return FileResponse(path=native_audio_wav, media_type='application/octet-stream',
                            filename="synthesized.wav", status_code=HTTPStatus.OK.real)
    if input_data.speech_timeout:
        logger.info(f"Storing response as {models.fileio.speech_synthesis_wav}")
        if binary := await speech_synthesis(input_data=SpeechSynthesisModal(
                text=response, timeout=input_data.speech_timeout, quality="low"
        ), raise_for_status=False):
            return binary
    raise APIResponse(status_code=HTTPStatus.OK.real, detail=response)


@app.post(path="/stock-monitor/", dependencies=STOCK_PROTECTOR)
async def stock_monitor_api(request: Request, input_data: StockMonitorModal) -> NoReturn:
    """Stock monitor api endpoint.

    Args:
        - request: Takes the ``Request`` class as an argument.
        - input_data: Takes the following arguments as ``OfflineCommunicatorModal`` class instead of a QueryString.

            - token: Authentication token.
            - email: Email to which the notifications have to be triggered.

    See Also:
        - This API endpoint is simply the backend for stock price monitoring.
        - This function validates the user information and stores it to a database.
    """
    logger.info(f"Connection received from {request.client.host} via {request.headers.get('host')} using "
                f"{request.headers.get('user-agent')}")
    decoded = jwt.decode(jwt=input_data.token, options={"verify_signature": False}, algorithms="HS256")

    from modules.validators import email_validator
    result = email_validator.validate(email=input_data.email, check_smtp=False)  # SMTP check is not in a reliable state
    if result is None:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f"{input_data.email.split('@')[-1]!r} doesn't resolve to a valid mail server!")

    decoded['Ticker'] = decoded['Ticker'].upper()
    decoded['Max'] = support.extract_nos(input_=decoded['Max'], method=float)
    decoded['Min'] = support.extract_nos(input_=decoded['Min'], method=float)
    decoded['Correction'] = support.extract_nos(input_=decoded['Correction'], method=int)

    if decoded['Correction'] is None:
        decoded['Correction'] = 5
    if decoded['Max'] is None and decoded['Min'] is None:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail="Minimum and maximum values should be integers. "
                                 "If you don't want a notification for any one of of it, please mark it as 0.")
    if decoded['Max'] and decoded['Max'] <= decoded['Min']:
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real,
                          detail="'Max' should be greater than the 'Min' value.\n\nSet 'Max' or 'Min' as 0, "
                                 "if you don't wish to receive a notification for it.")
    if decoded['Correction'] > 20:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail="Allowed correction values are only up to 20%\n\nFor anything greater, "
                                 "it is better to increase/decrease the Max/Min values.")

    logger.info(f"User requested: {input_data.email} ticker alert for {decoded}")
    if decoded['Ticker'] not in stock_monitor.stock_list:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f"{decoded['Ticker']} not a part of NASDAQ stock list [OR] Jarvis currently doesn't "
                                 f"support tracking prices for {decoded['Ticker']}.")

    # Check dupes and let know the user
    new_entry = (str(decoded['Ticker']), input_data.email, float(decoded['Max']), float(decoded['Min']),
                 int(decoded['Correction']),)
    if new_entry in squire.get_stock_userdata():
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real, detail="Duplicate request!\nEntry exists in database.")

    try:
        price_check = webull().get_quote(decoded['Ticker'])
        current_price = price_check.get('close') or price_check.get('open')
        if current_price:
            current_price = float(current_price)
        else:
            raise ValueError(price_check)
    except ValueError as error:
        logger.error(error)
        raise APIResponse(status_code=HTTPStatus.BAD_GATEWAY.real,
                          detail=f"Failed to perform a price check on {decoded['Ticker']}\n\n{error}")
    if decoded['Max'] and current_price >= decoded['Max']:  # Ignore 0 which doesn't trigger a notification
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real,
                          detail=f"Current price of {decoded['Ticker']} is {current_price}.\n"
                                 "Please choose a higher 'Max' value or try at a later time.")
    if decoded['Min'] and current_price <= decoded['Min']:  # Ignore 0 which doesn't trigger a notification
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real,
                          detail=f"Current price of {decoded['Ticker']} is {current_price}.\n"
                                 "Please choose a lower 'Min' value or try at a later time.")

    squire.insert_stock_userdata(entry=new_entry)  # Store it in database

    raise APIResponse(status_code=HTTPStatus.OK.real,
                      detail=f"Entry added to the database. Jarvis will notify you at {input_data.email!r} when a "
                             f"price change occurs in {decoded['Ticker']!r}.")


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or all([models.env.robinhood_user, models.env.robinhood_pass,
                                              models.env.robinhood_pass, models.env.robinhood_endpoint_auth]):
    @app.post(path="/robinhood-authenticate", dependencies=ROBINHOOD_PROTECTOR)
    async def authenticate_robinhood() -> NoReturn:
        """Authenticates the request and generates single use token.

        Raises:
            200: If initial auth is successful and returns the single-use token.

        See Also:
            If basic auth (stored as an env var ``robinhood_endpoint_auth``) succeeds:

            - Returns ``?token=HASHED_UUID`` to access ``/investment`` via ``/investment?token=HASHED_UUID``
            - Also stores the token in the ``Robinhood`` object which is verified in the ``/investment`` endpoint.
            - The token is nullified in the object as soon as it is verified, making it single use.
        """
        robinhood.token = support.token()
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=f"?token={robinhood.token}")

# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or all([models.env.robinhood_user, models.env.robinhood_pass,
                                              models.env.robinhood_pass, models.env.robinhood_endpoint_auth]):
    @app.get(path="/investment", response_class=HTMLResponse, include_in_schema=False)
    async def robinhood_path(request: Request, token: str = None) -> HTMLResponse:
        """Serves static file.

        Args:
            - request: Takes the ``Request`` class as an argument.
            - token: Takes custom auth token as an argument.

        Returns:
            HTMLResponse:
            Renders the html page.

        Raises:
            - 403: If token is ``null``.
            - 404: If the HTML file is not found.
            - 417: If token doesn't match the auto-generated value.

        See Also:
            - This endpoint is secured behind single use token.
            - Initial check is done by the function authenticate_robinhood behind the path "/robinhood-authenticate"
            - Once the auth succeeds, a one-time usable hashed-uuid is generated and stored in the ``Robinhood`` object.
            - This UUID is sent as response to the API endpoint behind ngrok connection (if tunnelled).
            - The UUID is deleted from the object as soon as the argument is checked for the first time.
            - Page refresh is useless because the value in memory is cleared as soon as it is authed once.
        """
        logger.info(f"Connection received from {request.client.host} via {request.headers.get('host')} using "
                    f"{request.headers.get('user-agent')}")
        if not token:
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])
        if token == robinhood.token:
            robinhood.token = None
            if not os.path.isfile(models.fileio.robinhood):
                raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail='Static file was not found on server.')
            with open(models.fileio.robinhood) as static_file:
                html_content = static_file.read()
            content_type, _ = mimetypes.guess_type(html_content)
            return HTMLResponse(status_code=HTTPStatus.TEMPORARY_REDIRECT.real,
                                content=html_content, media_type=content_type)  # serves as a static webpage
        else:
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or models.env.surveillance_endpoint_auth:
    @app.post(path="/surveillance-authenticate", dependencies=SURVEILLANCE_PROTECTOR)
    async def authenticate_surveillance(cam: CameraIndexModal) -> NoReturn:
        """Tests the given camera index, generates a token for the endpoint to authenticate.

        Args:
            cam: Index number of the chosen camera.

        Raises:
            200: If initial auth is successful and returns the single-use token.

        See Also:
            If basic auth (stored as an env var ``SURVEILLANCE_ENDPOINT_AUTH``) succeeds:

            - Returns ``?token=HASHED_UUID`` to access ``/surveillance`` via ``/surveillance?token=HASHED_UUID``
            - Also stores the token in the ``Surveillance`` object which is verified in the ``/surveillance`` endpoint.
            - The token is nullified in the object as soon as it is verified, making it single use.
        """
        surveillance.camera_index = cam.index
        try:
            squire.test_camera()
        except CameraError as error:
            raise APIResponse(status_code=HTTPStatus.NOT_ACCEPTABLE.real, detail=str(error))
        surveillance.token = support.token()
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=f"?token={surveillance.token}")


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or models.env.surveillance_endpoint_auth:
    @app.get('/surveillance')
    async def monitor(token: str = None) -> HTMLResponse:
        """Serves the monitor page's frontend after updating it with video origin and websocket origins.

        Args:
            - request: Takes the ``Request`` class as an argument.
            - token: Takes custom auth token as an argument.

        Returns:
            HTMLResponse:
            Renders the html page.

        Raises:
            - 403: If token is ``null``.
            - 417: If token doesn't match the auto-generated value.

        See Also:
            This endpoint is secured behind single use token.

            - Initial check is done by ``authenticate_surveillance`` behind the path "/surveillance-authenticate"
            - Once the auth succeeds, a one-time usable hashed-uuid is generated and stored in ``Surveillance`` object.
            - This UUID is sent as response to the API endpoint behind ngrok connection (if tunnelled).
            - The UUID is deleted from the object as soon as the argument is checked for the last time.
            - Page refresh is useless because the value in memory is cleared as soon as the video is rendered.
        """
        if not token:
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])
        if token == surveillance.token:
            surveillance.client_id = int(''.join(str(time.time()).split('.')))  # include milliseconds to avoid dupes
            rendered = jinja2.Template(templates.Surveillance.source).render(CLIENT_ID=surveillance.client_id)
            content_type, _ = mimetypes.guess_type(rendered)
            return HTMLResponse(status_code=HTTPStatus.TEMPORARY_REDIRECT.real,
                                content=rendered, media_type=content_type)
        else:
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or models.env.surveillance_endpoint_auth:
    @app.get('/video-feed')
    async def video_feed(request: Request, token: str = None) -> StreamingResponse:
        """Authenticates the request, and returns the frames generated as a ``StreamingResponse``.

        Args:
            - request: Takes the ``Request`` class as an argument.
            - token: Token generated in ``/surveillance-authenticate`` endpoint to restrict direct access.

        Returns:
            StreamingResponse:
            StreamingResponse with a collective of each frame.
        """
        logger.info(f"Connection received from {request.client.host} via {request.headers.get('host')} using "
                    f"{request.headers.get('user-agent')}")
        if not token:
            logger.warning('/video-feed was accessed directly.')
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])
        if token != surveillance.token:
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')
        surveillance.token = None
        surveillance.queue_manager[surveillance.client_id] = Queue()
        process = Process(target=squire.gen_frames,
                          kwargs={"manager": surveillance.queue_manager[surveillance.client_id],
                                  "index": surveillance.camera_index,
                                  "available_cameras": surveillance.available_cameras})
        process.start()
        # Insert process IDs into the children table to kill it in case, Jarvis is stopped during an active session
        with db.connection:
            cursor = db.connection.cursor()
            cursor.execute("INSERT INTO children (surveillance) VALUES (?);", (process.pid,))
            db.connection.commit()
        surveillance.processes[surveillance.client_id] = process
        return StreamingResponse(content=squire.streamer(), media_type='multipart/x-mixed-replace; boundary=frame',
                                 status_code=HTTPStatus.PARTIAL_CONTENT.real)


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or models.env.surveillance_endpoint_auth:
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: int) -> None:
        """Initiates a websocket connection.

        Args:
            websocket: WebSocket.
            client_id: Epoch time generated when each user renders the video file.

        See Also:
            - Websocket checks the frontend and kills the backend process to release the camera if connection is closed.
            - Closing the multiprocessing queue is not required as the backend process will be terminated anyway.

        Notes:
            - Closing queue before process termination will raise ValueError as the process is still updating the queue.
            - Closing queue after process termination will raise EOFError as the queue will not be available to close.
        """
        await ws_manager.connect(websocket)
        try:
            while True:
                try:
                    data = await asyncio.wait_for(fut=websocket.receive_text(), timeout=5)
                except asyncio.TimeoutError:
                    data = None
                if data:
                    logger.info(f'Client [{client_id}] sent {data}')
                    if data == "Healthy":
                        surveillance.session_manager[client_id] = time.time()
                        timestamp = surveillance.session_manager[client_id] + models.env.surveillance_session_timeout
                        logger.info(f"Surveillance session will expire at "
                                    f"{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
                    if data == "IMG_ERROR":
                        logger.info("Sending error image frame to client.")
                        await websocket.send_bytes(data=squire.generate_error_frame(
                            dimension=surveillance.frame,
                            text="Unable to get image frame from "
                                 f"{surveillance.available_cameras[surveillance.camera_index]}"))
                        raise WebSocketDisconnect  # Raise error to release camera after a failed read
                if surveillance.session_manager[client_id] + models.env.surveillance_session_timeout <= time.time():
                    logger.info(f"Sending session timeout to client: {client_id}")
                    await websocket.send_bytes(data=squire.generate_error_frame(
                        dimension=surveillance.frame, text="SESSION EXPIRED! Re-authenticate to continue live stream."))
                    raise WebSocketDisconnect  # Raise error to release camera after a failed read
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
            logger.info(f'Client [{client_id}] disconnected.')
            if ws_manager.active_connections:
                if process := surveillance.processes.get(int(client_id)):
                    support.stop_process(pid=process.pid)
            else:
                logger.info("No active connections found.")
                for client_id, process in surveillance.processes.items():
                    support.stop_process(pid=process.pid)
