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
from multiprocessing import Process
from threading import Thread
from typing import Any, Dict, List, NoReturn, Union

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from api import authenticator
from api.models import GetData, GetText, InvestmentFilter
from api.report_gatherer import Investment
from executors.commander import timed_delay
from executors.offline import offline_communicator
from executors.word_match import word_match
from modules.audio import speaker, tts_stt
from modules.conditions import conversation, keywords
from modules.exceptions import APIResponse
from modules.models import config, models
from modules.offline import compatibles
from modules.utils import support

OFFLINE_PROTECTOR = [Depends(dependency=authenticator.offline_has_access)]
ROBINHOOD_PROTECTOR = [Depends(dependency=authenticator.robinhood_has_access)]

robinhood_token = {'token': ''}

if not os.path.isfile(config.APIConfig().ACCESS_LOG_FILENAME):
    pathlib.Path(config.APIConfig().ACCESS_LOG_FILENAME).touch()

if not os.path.isfile(config.APIConfig().DEFAULT_LOG_FILENAME):
    pathlib.Path(config.APIConfig().DEFAULT_LOG_FILENAME).touch()

offline_compatible = compatibles.offline_compatible()

importlib.reload(module=logging)
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
    if os.path.isfile(models.fileio.robinhood):
        modified = int(os.stat(models.fileio.robinhood).st_mtime)
        logger.info(f"{models.fileio.robinhood} was generated on {datetime.fromtimestamp(modified).strftime('%c')}.")
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
        f"http://{models.env.website}",
        f"https://{models.env.website}",
        f"http://{models.env.website}/*",
        f"https://{models.env.website}/*",
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
async def speech_synthesis(input_data: GetText, raise_for_status: bool = True) -> Union[FileResponse, None]:
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
        Thread(target=remove_file, kwargs={'delay': 2, 'filepath': models.fileio.speech_synthesis_wav}).start()
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
async def offline_communicator_api(request: Request, input_data: GetData) -> Union[FileResponse, NoReturn]:
    """Offline Communicator API endpoint for Jarvis.

    Args:
        - request: Takes the ``Request`` class as an argument.
        - input_data: Takes the following arguments as ``GetData`` class instead of a QueryString.

            - command: The task which Jarvis has to do.

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
                logger.warning(f"'{each}' is not a part of offline compatible request.")
                and_response += f'"{each}" is not a part of off-line communicator compatible request.\n\n' \
                                'Please try an instruction that does not require an user interaction.'
            else:
                and_response += f"{offline_communicator(command=each)}\n"
        logger.info(f"Response: {and_response}")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=and_response)
    elif ' also ' in command and not word_match(phrase=command, match_list=keywords.avoid):
        also_response = ""
        for each in command.split(' also '):
            if not word_match(phrase=each, match_list=offline_compatible):
                logger.warning(f"'{each}' is not a part of offline compatible request.")
                also_response += f'"{each}" is not a part of off-line communicator compatible request.\n\n' \
                                 'Please try an instruction that does not require an user interaction.'
            else:
                also_response = f"{offline_communicator(command=each)}\n"
        logger.info(f"Response: {also_response}")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=also_response)
    if not word_match(phrase=command, match_list=offline_compatible):
        logger.warning(f"'{command}' is not a part of offline compatible request.")
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f'"{command}" is not a part of off-line communicator compatible request.\n\n'
                                 'Please try an instruction that does not require an user interaction.')
    if ' after ' in command.lower():
        if delay_info := timed_delay(phrase=command):
            logger.info(f"'{delay_info[0]}' will be executed after {support.time_converter(seconds=delay_info[1])}")
            raise APIResponse(status_code=HTTPStatus.OK.real,
                              detail=f'I will execute it after {support.time_converter(seconds=delay_info[1])} '
                                     f'{models.env.title}!')
    response = offline_communicator(command=command)
    logger.info(f"Response: {response}")
    if input_data.native_audio:
        native_audio_wav = tts_stt.text_to_audio(text=response)
        logger.info(f"Storing response as {native_audio_wav} in native audio.")
        Thread(target=remove_file, kwargs={'delay': 2, 'filepath': native_audio_wav}).start()
        return FileResponse(path=native_audio_wav, media_type='application/octet-stream',
                            filename="synthesized.wav", status_code=HTTPStatus.OK.real)
    if input_data.speech_timeout:
        logger.info(f"Storing response as {models.fileio.speech_synthesis_wav}")
        if binary := await speech_synthesis(input_data=GetText(text=response, timeout=input_data.speech_timeout,
                                                               quality="low"), raise_for_status=False):
            return binary
    raise APIResponse(status_code=HTTPStatus.OK.real, detail=response)


@app.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse(filename='favicon.ico', path=os.getcwd(), status_code=HTTPStatus.OK.real)


# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or all([models.env.robinhood_user, models.env.robinhood_pass,
                                              models.env.robinhood_pass]):
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
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=f"?token={robinhood_token['token']}")

# Conditional endpoint: Condition matches without env vars during docs generation
if not os.getcwd().endswith("Jarvis") or all([models.env.robinhood_user, models.env.robinhood_pass,
                                              models.env.robinhood_pass]):
    @app.get(path="/investment", response_class=HTMLResponse, include_in_schema=False)
    async def robinhood(token: str = None) -> HTMLResponse:
        """Serves static file.

        Args:
            token: Takes custom auth token as an argument.

        Returns:
            HTMLResponse:
            Renders the html page.

        Raises:
            - 403: If token is ``null``.
            - 404: If the HTML file is not found.
            - 417: If token doesn't match the auto-generated value.

        See Also:
            - This endpoint is secured behind two-factor authentication.
            - Initial check is done by the function authenticate_robinhood behind the path "/robinhood-authenticate"
            - Once the auth succeeds, a one-time usable hashed-uuid is generated and stored as an environment variable.
            - This UUID is sent as response to the API endpoint behind ngrok tunnel.
            - The UUID is deleted from env var as soon as the argument is checked for the first time.
            - Page refresh doesn't work because the env var is deleted as soon as it is authed once.
        """
        if not token:
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.__dict__['phrase'])
        if token == robinhood_token['token']:
            robinhood_token['token'] = ''
            if not os.path.isfile(models.fileio.robinhood):
                raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail='Static file was not found on server.')
            with open(models.fileio.robinhood) as static_file:
                html_content = static_file.read()
            content_type, _ = mimetypes.guess_type(html_content)
            return HTMLResponse(status_code=HTTPStatus.TEMPORARY_REDIRECT.real,
                                content=html_content, media_type=content_type)  # serves as a static webpage
        else:
            logger.warning('/investment was accessed with an expired token.')
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')
