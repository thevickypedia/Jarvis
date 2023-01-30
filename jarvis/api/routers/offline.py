import imghdr
import os
import string
import traceback
from http import HTTPStatus
from threading import Thread
from typing import NoReturn

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from jarvis.api.modals.authenticator import OFFLINE_PROTECTOR
from jarvis.api.modals.models import (OfflineCommunicatorModal,
                                      SpeechSynthesisModal)
from jarvis.api.routers import speech_synthesis
from jarvis.api.squire.logger import logger
from jarvis.executors.commander import timed_delay
from jarvis.executors.offline import offline_communicator
from jarvis.executors.word_match import word_match
from jarvis.modules.audio import tts_stt
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models
from jarvis.modules.offline import compatibles
from jarvis.modules.utils import support

router = APIRouter()
db = database.Database(database=models.fileio.base_db)


def kill_power() -> NoReturn:
    """Inserts a flag into stopper table in base database."""
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("INSERT or REPLACE INTO stopper (flag, caller) VALUES (?,?);", (True, 'FastAPI'))
        cursor.connection.commit()


@router.post(path="/offline-communicator", dependencies=OFFLINE_PROTECTOR)
async def offline_communicator_api(request: Request, input_data: OfflineCommunicatorModal):
    """Offline Communicator API endpoint for Jarvis.

    Args:

        - request: Takes the Request class as an argument.
        - input_data: Takes the following arguments as OfflineCommunicatorModal class instead of a QueryString.

            - command: The task which Jarvis has to do.
            - native_audio: Whether the response should be as an audio file with the server's built-in voice.
            - speech_timeout: Timeout to process speech-synthesis.

    Raises:

        APIResponse:
        - 200: A dictionary with the command requested and the response for it from Jarvis.
        - 204: If empty command was received.
        - 422: If the request is not part of offline compatible words.

    See Also:

        - Keeps waiting for the record response in the database table offline

    Returns:

        FileResponse:
        Returns the audio file as a response if audio request is made.
    """
    logger.debug(f"Connection received from {request.client.host} via {request.headers.get('host')} using "
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

    if word_match(phrase=command, match_list=keywords.keywords.kill) and 'override' in command.lower():
        logger.info("STOP override has been requested.")
        Thread(target=kill_power).start()
        raise APIResponse(status_code=HTTPStatus.OK.real,
                          detail=f"Shutting down now {models.env.title}!\n{support.exit_message()}")

    # Keywords for which the ' and ' split should not happen.
    multiexec = keywords.keywords.send_notification + keywords.keywords.reminder + keywords.keywords.distance

    if ' and ' in command and not word_match(phrase=command, match_list=keywords.keywords.avoid) and \
            not word_match(phrase=command, match_list=multiexec):
        and_response = ""
        for each in command.split(' and '):
            if not word_match(phrase=each, match_list=compatibles.offline_compatible()):
                logger.warning(f"{each!r} is not a part of offline compatible request.")
                and_response += f'{each!r} is not a part of off-line communicator compatible request.\n\n' \
                                'Please try an instruction that does not require an user interaction.'
            else:
                try:
                    and_response += f"{offline_communicator(command=each)}\n"
                except Exception as error:
                    logger.error(error)
                    logger.error(traceback.format_exc())
                    and_response += error.__str__()
        logger.info(f"Response: {and_response.strip()}")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=and_response.strip())

    if not word_match(phrase=command, match_list=compatibles.offline_compatible()):
        logger.warning(f"{command!r} is not a part of offline compatible request.")
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f'"{command}" is not a part of off-line communicator compatible request.\n\n'
                                 'Please try an instruction that does not require an user interaction.')
    if ' after ' in command.lower():
        if delay_info := timed_delay(phrase=command):
            logger.info(f"{delay_info[0]!r} will be executed after {support.time_converter(second=delay_info[1])}")
            raise APIResponse(status_code=HTTPStatus.OK.real,
                              detail=f'I will execute it after {support.time_converter(second=delay_info[1])} '
                                     f'{models.env.title}!')
    try:
        response = offline_communicator(command=command)
    except Exception as error:
        logger.error(error)
        logger.error(traceback.format_exc())
        response = error.__str__()
    logger.info(f"Response: {response}")
    if os.path.isfile(response) and response.endswith('.jpg'):
        logger.info("Response received as a file.")
        Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': response}, daemon=True).start()
        return FileResponse(path=response, media_type=f'image/{imghdr.what(file=response)}',
                            filename=os.path.basename(response), status_code=HTTPStatus.OK.real)
    if input_data.speech_timeout:
        logger.info(f"Storing response as {models.fileio.speech_synthesis_wav}")
        if binary := await speech_synthesis.speech_synthesis(input_data=SpeechSynthesisModal(
                text=response, timeout=input_data.speech_timeout, quality="low"  # low quality to speed up response
        ), raise_for_status=False):
            return binary
    elif input_data.native_audio:
        if native_audio_wav := tts_stt.text_to_audio(text=response):
            logger.info(f"Storing response as {native_audio_wav} in native audio.")
            Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': native_audio_wav}, daemon=True).start()
            return FileResponse(path=native_audio_wav, media_type='application/octet-stream',
                                filename="synthesized.wav", status_code=HTTPStatus.OK.real)
        else:
            raise APIResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR.real,
                              detail="Failed to generate audio file in native voice. "
                                     "This feature can be flaky at times as it relies on native wav to kernel specific "
                                     "wav conversion. Please use `speech_timeout` instead to get an audio response.")
    else:
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=response)
