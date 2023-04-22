# noinspection PyUnresolvedReferences
"""Custom audio file IO handler for Telegram API.

>>> AudioHandler

"""

import importlib
import logging
import os
from typing import Callable, Union

from pydantic import FilePath

from jarvis.modules.logger.custom_logger import logger

importlib.reload(module=logging)


def audio_converter_mac() -> Callable:
    """Imports transcode from ftransc.

    Returns:
        Callable:
        Transcode function from ftransc.
    """
    try:
        from ftransc.core.transcoders import transcode  # noqa
        return transcode
    except (SystemExit, ModuleNotFoundError) as error:
        logger.error(error)


def audio_converter_win(input_filename: Union[FilePath, str], output_audio_format: str) -> Union[str, None]:
    """Imports AudioSegment from pydub.

    Args:
        input_filename: Input filename.
        output_audio_format: Output audio format.

    Returns:
        str:
        Output filename if conversion is successful.
    """
    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin")
    if not os.path.exists(path=ffmpeg_path):
        logger.warning("ffmpeg codec is missing!")
        return
    os.environ['PATH'] += f";{ffmpeg_path}"
    from pydub import AudioSegment  # noqa
    if input_filename.endswith(".ogg"):
        audio = AudioSegment.from_ogg(input_filename)
        output_filename = input_filename.replace(".ogg", f".{output_audio_format}")
    elif input_filename.endswith(".wav"):
        audio = AudioSegment.from_wav(input_filename)
        output_filename = input_filename.replace(".wav", f".{output_audio_format}")
    else:
        return
    try:
        audio.export(input_filename, format=output_audio_format)
        os.remove(input_filename)
        if os.path.isfile(output_filename):
            return output_filename
        raise FileNotFoundError(f"{output_filename} was not found after exporting audio to {output_audio_format}")
    except FileNotFoundError as error:  # raised by audio.export when conversion fails
        logger.error(error)
