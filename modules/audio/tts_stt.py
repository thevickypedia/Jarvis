# noinspection PyUnresolvedReferences
"""Module for text to speech and speech to text conversions.

>>> TTS and STT

"""

import os
import time
from multiprocessing import Process
from typing import NoReturn, Union

import soundfile
from pydantic import FilePath
from speech_recognition import AudioFile, Recognizer, UnknownValueError

from executors.logger import logger
from modules.audio import voices
from modules.utils import shared

recognizer = Recognizer()

audio_driver = voices.voice_default()


def _generate_audio_file(filename: Union[FilePath, str], text: str) -> NoReturn:
    """Generates an audio file from text.

    Args:
        filename: Filename to be generated.
        text: Text that has to be converted into audio.
    """
    logger.info(f"Generating audio into {filename} from the text: {text}")
    audio_driver.save_to_file(filename=filename, text=text)
    audio_driver.runAndWait()


def text_to_audio(text: str, filename: Union[FilePath, str] = None) -> Union[FilePath, str]:
    """Converts text into an audio file.

    Args:
        filename: Name of the file that has to be generated.
        text: Text that has to be converted to audio.
    """
    if not filename:
        if shared.offline_caller:
            filename = f"{shared.offline_caller}.wav"
            shared.offline_caller = None  # Reset caller after using it
        else:
            filename = f"{int(time.time())}.wav"
    process = Process(target=_generate_audio_file, kwargs={'filename': filename, 'text': text})
    process.start()
    while True:
        if os.path.isfile(filename) and os.stat(filename).st_size:
            time.sleep(0.5)
            break
    logger.info(f"Generated {filename}")
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
