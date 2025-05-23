import os
from http import HTTPStatus
from json import JSONDecodeError
from threading import Thread
from urllib.parse import urljoin

import requests
from fastapi.responses import FileResponse

from jarvis.api.logger import logger
from jarvis.api.models import modals
from jarvis.modules.audio import speaker
from jarvis.modules.exceptions import APIResponse, EgressErrors
from jarvis.modules.models import models
from jarvis.modules.utils import support


async def speech_synthesis_voices():
    """Get all available voices in speech synthesis.

    Raises:

        - 200: If call to speech synthesis endpoint was successful.
        - 500: If call to speech synthesis fails.
    """
    if not models.env.speech_synthesis_api:
        raise APIResponse(
            status_code=HTTPStatus.NOT_FOUND.real,
            detail="Speech synthesis API endpoint is unavailable",
        )
    url = urljoin(str(models.env.speech_synthesis_api), "/api/voices")
    try:
        response = requests.get(url=url, timeout=3)
    except EgressErrors as error:
        logger.error(error)
        raise APIResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.real, detail=str(error)
        )
    if response.ok:
        try:
            json_response = response.json()
        except JSONDecodeError as error:
            logger.error(error)
            raise APIResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.real, detail=str(error)
            )
        available_voices = [
            value.get("id").replace("/", "_") for key, value in json_response.items()
        ]
        logger.info("Available voices: %d", len(available_voices))
        logger.debug(available_voices)
        raise APIResponse(status_code=HTTPStatus.OK.real, detail=available_voices)
    else:
        logger.error(response.content)
        raise APIResponse(status_code=response.status_code, detail=response.content)


async def speech_synthesis(
    input_data: modals.SpeechSynthesisModal, raise_for_status: bool = True
):
    """Process request to convert text to speech using the speech-synthesis API endpoint.

    Args:

        - input_data: Takes the following arguments as GetText class instead of a QueryString.
        - raise_for_status: Takes a boolean flag to determine whether the result should be raised as an API response.

            - text: Text to be processed with speech synthesis.
            - timeout: Timeout for speech-synthesis API call.
            - quality: Quality of audio conversion.
            - voice: Voice model ot be used.

    Raises:

        APIResponse:
        - 404: If audio file was not found after successful response.
        - 500: If the connection to speech synthesizer fails.
        - 204: If speech synthesis file wasn't found.

    Returns:

        FileResponse:
        Audio file to be downloaded.
    """
    if not (text := input_data.text.strip()):
        logger.error("Empty requests cannot be processed.")
        if raise_for_status:
            raise APIResponse(
                status_code=HTTPStatus.NO_CONTENT.real,
                detail=HTTPStatus.NO_CONTENT.phrase,
            )
        else:
            return
    if not speaker.speech_synthesizer(
        text=text,
        timeout=input_data.timeout or len(text),
        quality=input_data.quality,
        voice=input_data.voice,
    ):
        logger.error("Speech synthesis could not process the request.")
        if raise_for_status:
            raise APIResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.real,
                detail=HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            )
        else:
            return
    if os.path.isfile(path=models.fileio.speech_synthesis_wav):
        logger.debug("Speech synthesis file generated for '%s'", text)
        Thread(
            target=support.remove_file,
            kwargs={"delay": 2, "filepath": models.fileio.speech_synthesis_wav},
            daemon=True,
        ).start()
        return FileResponse(
            path=models.fileio.speech_synthesis_wav,
            media_type="application/octet-stream",
            filename="synthesized.wav",
            status_code=HTTPStatus.OK.real,
        )
    logger.error("File Not Found: %s", models.fileio.speech_synthesis_wav)
    if raise_for_status:
        raise APIResponse(
            status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.phrase
        )
