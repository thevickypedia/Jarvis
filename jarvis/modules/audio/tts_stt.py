# noinspection PyUnresolvedReferences
"""Module for text to speech and speech to text conversions.

>>> TTS and STT

"""

import os
import time
from multiprocessing.context import \
    TimeoutError as ThreadTimeoutError  # noqa: PyProtectedMember
from multiprocessing.pool import ThreadPool
from typing import NoReturn, Union

import soundfile
from pydantic import FilePath
from speech_recognition import AudioFile, Recognizer, UnknownValueError

from jarvis.modules.audio import voices
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.utils import shared

recognizer = Recognizer()

audio_driver = voices.voice_default()


def generate_audio_file(filename: Union[FilePath, str], text: str) -> NoReturn:
    """Generates an audio file from text.

    Args:
        filename: Filename to be generated.
        text: Text that has to be converted into audio.
    """
    logger.info("Generating audio into %s from the text: %s", filename, text)
    audio_driver.save_to_file(filename=filename, text=text)
    audio_driver.runAndWait()


def text_to_audio(text: str, filename: Union[FilePath, str] = None) -> Union[FilePath, str, None]:
    """Converts text into an audio file using the default speaker configuration.

    Args:
        filename: Name of the file that has to be generated.
        text: Text that has to be converted to audio.

    Warnings:
        This can be flaky at times as it relies on converting native wav to kernel specific wav format.
    """
    if not filename:
        if shared.offline_caller:
            filename = f"{shared.offline_caller}.wav"
            shared.offline_caller = None  # Reset caller after using it
        else:
            filename = f"{int(time.time())}.wav"
    dynamic_timeout = len(text.split())
    logger.info("Timeout for text to speech conversion: %ds", dynamic_timeout)
    process = ThreadPool(processes=1).apply_async(func=generate_audio_file, kwds={'filename': filename, 'text': text})
    try:
        process.get(timeout=dynamic_timeout)
    except ThreadTimeoutError as error:
        logger.error(error)
        return
    if os.path.isfile(filename) and os.stat(filename).st_size:
        logger.info("Generated %s", filename)
        data, samplerate = soundfile.read(file=filename)
        soundfile.write(file=filename, data=data, samplerate=samplerate)
        return filename


def audio_to_text(filename: Union[FilePath, str]) -> str:
    """Converts audio to text using speech recognition.

    Args:
        filename: Filename to process the information from.

    Returns:
        str:
        Returns the string converted from the audio file.
    """
    try:
        file = AudioFile(filename_or_fileobject=filename)
        with file as source:
            audio = recognizer.record(source)
        os.remove(filename)
        return recognizer.recognize_google(audio)
    except UnknownValueError:
        logger.error("Unrecognized audio or language.")
