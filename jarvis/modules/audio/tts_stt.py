# noinspection PyUnresolvedReferences
"""Module for text to speech and speech to text conversions.

>>> TTS and STT

"""

import os
import time

import soundfile
from pydantic import FilePath
from speech_recognition import AudioFile, Recognizer, UnknownValueError

from jarvis.modules.audio import voices
from jarvis.modules.logger import logger
from jarvis.modules.utils import shared

recognizer = Recognizer()

AUDIO_DRIVER = voices.voice_default()


def text_to_audio(text: str, filename: FilePath | str = None) -> FilePath | str | None:
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
    AUDIO_DRIVER.save_to_file(filename=filename, text=text)
    AUDIO_DRIVER.runAndWait()
    if os.path.isfile(filename) and os.stat(filename).st_size:
        logger.info("Generated %s", filename)
        data, samplerate = soundfile.read(file=filename)
        soundfile.write(file=filename, data=data, samplerate=samplerate)
        return filename


def audio_to_text(filename: FilePath | str) -> str:
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
