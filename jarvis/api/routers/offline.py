import imghdr
import os
import string
import traceback
from http import HTTPStatus
from threading import Thread
from typing import NoReturn, Union

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from jarvis.api.modals.authenticator import OFFLINE_PROTECTOR
from jarvis.api.modals.models import (OfflineCommunicatorModal,
                                      SpeechSynthesisModal)
from jarvis.api.routers import speech_synthesis
from jarvis.api.squire.logger import logger
from jarvis.executors import commander, offline, others, word_match
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


async def process_ok_response(response: str, input_data: OfflineCommunicatorModal) -> Union[bytes, FileResponse]:
    """Processes responses for 200 messages. Response is framed as synthesized or native based on input data.

    Args:
        response: Takes the response as text.
        input_data: Input data modal.

    Returns:
        Union[bytes, FileResponse]:
        FileResponse in case of native audio or bytes in case of speech synthesized response.
    """
    if input_data.speech_timeout:
        logger.info("Storing response as %s", models.fileio.speech_synthesis_wav)
        if binary := await speech_synthesis.speech_synthesis(input_data=SpeechSynthesisModal(
                text=response, timeout=input_data.speech_timeout, quality="low"  # low quality to speed up response
        ), raise_for_status=False):
            return binary
        else:
            input_data.native_audio = True  # try native voice if SpeechSynthesis fails
    if input_data.native_audio:
        if native_audio_wav := tts_stt.text_to_audio(text=response):
            logger.info("Storing response as %s in native audio.", native_audio_wav)
            Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': native_audio_wav}, daemon=True).start()
            return FileResponse(path=native_audio_wav, media_type='application/octet-stream',
                                filename="synthesized.wav", status_code=HTTPStatus.OK.real)
        logger.error("Failed to generate audio file in native voice.")
    # Send response as text if requested so or if all other options fail
    raise APIResponse(status_code=HTTPStatus.OK.real, detail=response)


@router.post(path="/offline-communicator", dependencies=OFFLINE_PROTECTOR)
async def offline_communicator_api(request: Request, input_data: OfflineCommunicatorModal):
    """Offline Communicator API endpoint for Jarvis.

    Args:

        - request: Takes the Request class as an argument.
        - input_data: Takes the following arguments as an ``OfflineCommunicatorModal`` object.

            - command: The task which Jarvis has to do.
            - native_audio: Whether the response should be as an audio file with the server's built-in voice.
            - speech_timeout: Timeout to process speech-synthesis.

    Raises:

        APIResponse:
        - 200: A dictionary with the command requested and the response for it from Jarvis.
        - 204: If empty command was received.
        - 422: If the request is not part of offline compatible words.

    Returns:

        FileResponse:
        Returns the audio file as a response if the output is requested as audio.
    """
    logger.debug("Connection received from %s via %s using %s",
                 request.client.host, request.headers.get('host'), request.headers.get('user-agent'))
    if not (command := input_data.command.strip()):
        raise APIResponse(status_code=HTTPStatus.NO_CONTENT.real, detail=HTTPStatus.NO_CONTENT.phrase)

    logger.info("Request: %s", command)
    if 'alarm' in command.lower() or 'remind' in command.lower():
        command = command.lower()
    else:
        command = command.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string
    if command.lower() == 'test':
        logger.info("Test message received.")
        raise APIResponse(status_code=HTTPStatus.OK.real, detail="Test message received.")

    if word_match.word_match(phrase=command, match_list=keywords.keywords.kill) and 'override' in command.lower():
        logger.info("STOP override has been requested.")
        Thread(target=kill_power).start()
        return await process_ok_response(response=f"Shutting down now {models.env.title}!\n{support.exit_message()}",
                                         input_data=input_data)

    if word_match.word_match(phrase=command, match_list=keywords.keywords.secrets) and \
            word_match.word_match(phrase=command, match_list=('list', 'get')):
        response = others.secrets(phrase=command)
        if len(response.split()) == 1:
            response = "The secret requested can be accessed from 'secure-send' endpoint using the token below.\n" \
                       "Note that the secret cannot be retrieved again using the same token and the token will " \
                       f"expire in 5 minutes.\n\n{response}"
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=response)

    # Keywords for which the ' and ' split should not happen.
    ignore_and = keywords.keywords.send_notification + keywords.keywords.reminder + \
        keywords.keywords.distance + keywords.keywords.avoid
    if ' and ' in command and not word_match.word_match(phrase=command, match_list=ignore_and):
        and_response = ""
        for each in command.split(' and '):
            if not word_match.word_match(phrase=each, match_list=compatibles.offline_compatible()):
                logger.warning("'%s' is not a part of offline compatible request.", each)
                and_response += f'{each!r} is not a part of off-line communicator compatible request.\n\n' \
                                'Please try an instruction that does not require an user interaction.'
            else:
                try:
                    and_response += f"{offline.offline_communicator(command=each)}\n"
                except Exception as error:
                    logger.error(error)
                    logger.error(traceback.format_exc())
                    and_response += error.__str__()
        logger.info("Response: %s", and_response.strip())
        return await process_ok_response(response=and_response, input_data=input_data)

    if not word_match.word_match(phrase=command, match_list=compatibles.offline_compatible()):
        logger.warning("'%s' is not a part of offline compatible request.", command)
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f'"{command}" is not a part of off-line communicator compatible request.\n\n'
                                 'Please try an instruction that does not require an user interaction.')

    # Keywords for which the ' after ' split should not happen.
    ignore_after = keywords.keywords.meetings + keywords.keywords.avoid
    if ' after ' in command.lower() and not word_match.word_match(phrase=command, match_list=ignore_after):
        if delay_info := commander.timed_delay(phrase=command):
            logger.info("%s will be executed after %s", delay_info[0], support.time_converter(second=delay_info[1]))
            return await process_ok_response(response='I will execute it after '
                                                      f'{support.time_converter(second=delay_info[1])} '
                                                      f'{models.env.title}!', input_data=input_data)
    try:
        response = offline.offline_communicator(command=command)
    except Exception as error:
        logger.error(error)
        logger.error(traceback.format_exc())
        response = error.__str__()
    logger.info("Response: %s", response)
    if os.path.isfile(response) and response.endswith('.jpg'):
        logger.info("Response received as a file.")
        Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': response}, daemon=True).start()
        return FileResponse(path=response, media_type=f'image/{imghdr.what(file=response)}',
                            filename=os.path.basename(response), status_code=HTTPStatus.OK.real)
    return await process_ok_response(response=response, input_data=input_data)
