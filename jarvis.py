import os
import pathlib
import platform
import struct
import sys
from datetime import datetime
from typing import NoReturn

import numpy
import packaging.version
import pvporcupine
import soundfile
from playsound import playsound
from pyaudio import PyAudio, paInt16
from speech_recognition import Microphone

from executors.commander import initiator
from executors.controls import exit_process, restart, starter, terminator
from executors.internet import get_ssid, internet_checker
from executors.logger import logger
from executors.processor import start_processes, stop_processes
from executors.system import hosted_device_info
from modules.audio import listener, speaker
from modules.exceptions import StopSignal
from modules.models import models
from modules.timeout import timeout
from modules.utils import shared, support

env = models.env
fileio = models.FileIO()
indicators = models.Indicators()


class Activator:
    """Awaits for the keyword ``Jarvis`` and triggers ``initiator`` when heard.

    >>> Activator

    See Also:
        - Creates an input audio stream from a microphone, monitors it, and detects the specified wake word.
        - Once detected, Jarvis triggers the ``listener.listen()`` function with an ``acknowledgement`` sound played.
        - After processing the phrase, the converted text is sent as response to ``initiator()`` with a ``return`` flag.
        - The ``should_return`` flag ensures, the user is not disturbed when accidentally woke up by wake work engine.
    """

    def __init__(self, input_device_index: int = None):
        """Initiates Porcupine object for hot word detection.

        Args:
            input_device_index: Index of Input Device to use.

        See Also:
            - Instantiates an instance of Porcupine object and monitors audio stream for occurrences of keywords.
            - A higher sensitivity results in fewer misses at the cost of increasing the false alarm rate.
            - sensitivity: Tolerance/Sensitivity level. Takes argument or env var ``sensitivity`` or defaults to ``0.5``

        References:
            - `Audio Overflow <https://people.csail.mit.edu/hubert/pyaudio/docs/#pyaudio.Stream.read>`__ handling.
        """
        logger.info(f"Initiating hot-word detector with sensitivity: {env.sensitivity}")
        keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in [pathlib.PurePath(__file__).stem]]
        self.input_device_index = input_device_index
        self.recorded_frames = []

        self.py_audio = PyAudio()
        self.detector = pvporcupine.create(
            library_path=pvporcupine.LIBRARY_PATH,
            model_path=pvporcupine.MODEL_PATH,
            keyword_paths=keyword_paths,
            sensitivities=[env.sensitivity]
        )
        self.audio_stream = self.py_audio.open(
            rate=self.detector.sample_rate,
            channels=1,
            format=paInt16,
            input=True,
            frames_per_buffer=self.detector.frame_length,
            input_device_index=self.input_device_index
        )

    def start(self) -> NoReturn:
        """Runs ``audio_stream`` in a forever loop and calls ``initiator`` when the phrase ``Jarvis`` is heard."""
        try:
            while True:
                sys.stdout.write("\rSentry Mode")
                pcm = self.audio_stream.read(num_frames=self.detector.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.detector.frame_length, pcm)
                if self.detector.process(pcm=pcm) >= 0:
                    playsound(sound=indicators.acknowledgement, block=False)
                    if phrase := listener.listen(timeout=env.timeout, phrase_limit=env.phrase_limit, sound=False):
                        initiator(phrase=phrase, should_return=True)
                        speaker.speak(run=True)
                if env.save_audio_timeout:
                    self.recorded_frames.append(pcm)
                if flag := support.check_restart():
                    logger.info(f"Restart condition is set to {flag[0]} by {flag[1]}")
                    self.stop()
                    if flag[1] == "restart_control":
                        restart()
                    else:
                        restart(quiet=True)
                    break
                if flag := support.check_stop():
                    logger.info(f"Stopper condition is set to {flag[0]} by {flag[1]}")
                    self.stop()
                    terminator()
        except StopSignal:
            exit_process()
            self.stop()
            terminator()

    def stop(self) -> NoReturn:
        """Invoked when the run loop is exited or manual interrupt.

        See Also:
            - Terminates/Kills all the background processes.
            - Releases resources held by porcupine.
            - Closes audio stream.
            - Releases port audio resources.
        """
        stop_processes()
        logger.info("Releasing resources acquired by Porcupine.")
        self.detector.delete()
        if self.audio_stream and self.audio_stream.is_active():
            logger.info("Closing Audio Stream.")
            self.py_audio.close(stream=self.audio_stream)
            self.audio_stream.close()
        logger.info("Releasing PortAudio resources.")
        self.py_audio.terminate()
        if not self.recorded_frames:
            return
        logger.info("Recording is being converted to audio.")
        response = timeout.timeout(function=save_audio, seconds=env.save_audio_timeout, logger=logger,
                                   kwargs={"frames": self.recorded_frames, "sample_rate": self.detector.sample_rate})
        if response.ok:
            logger.info("Recording has been saved successfully.")
            logger.info(response.info)
        else:
            logger.error(f"Failed to save the audio file within {env.save_audio_timeout} seconds.")
            logger.error(response.info)


def save_audio(frames: list, sample_rate: int) -> NoReturn:
    """Converts audio frames into a recording to store it in a wav file.

    Args:
        frames: List of frames.
        sample_rate: Sample rate.
    """
    recordings_location = os.path.join(os.getcwd(), 'recordings')
    if not os.path.isdir(recordings_location):
        os.makedirs(recordings_location)
    filename = os.path.join(recordings_location, f"{datetime.now().strftime('%B_%d_%Y_%H%M')}.wav")
    logger.info(f"Saving {len(frames)} audio frames into {filename}")
    sys.stdout.write(f"\rSaving {len(frames)} audio frames into {filename}")
    recorded_audio = numpy.concatenate(frames, axis=0).astype(dtype=numpy.int16)
    soundfile.write(file=filename, data=recorded_audio, samplerate=sample_rate, subtype='PCM_16')
    support.flush_screen()


def sentry_mode() -> NoReturn:
    """Listens forever and invokes ``initiator()`` when recognized. Stops when ``restart`` table has an entry.

    See Also:
        - Gets invoked only when run from Mac-OS older than 10.14.
        - A regular listener is used to convert audio to text.
        - The text is then condition matched for wake-up words.
        - Additional wake words can be passed in a list as an env var ``LEGACY_KEYWORDS``.
    """
    while True:
        try:
            sys.stdout.write("\rSentry Mode")
            if wake_word := listener.listen(timeout=10, phrase_limit=2.5, sound=False):
                support.flush_screen()
                if any(word in wake_word.lower() for word in env.legacy_keywords):
                    playsound(sound=indicators.acknowledgement, block=False)
                    if phrase := listener.listen(timeout=env.timeout, phrase_limit=env.phrase_limit, sound=False):
                        initiator(phrase=phrase, should_return=True)
                        speaker.speak(run=True)
        except StopSignal:
            stop_processes()
            exit_process()
            terminator()
            break
        if flag := support.check_restart():
            logger.info(f"Restart condition is set to {flag[0]} by {flag[1]}")
            stop_processes()
            if flag[1] == "restart_control":
                restart()
            else:
                restart(quiet=True)
            break
        if flag := support.check_stop():
            logger.info(f"Stopper condition is set to {flag[0]} by {flag[1]}")
            stop_processes()
            terminator()
            break


def begin() -> None:
    """Starts main process to activate Jarvis after checking internet connection and initiating background processes."""
    starter()
    if internet_checker():
        sys.stdout.write(f"\rINTERNET::Connected to {get_ssid()}.")
    else:
        sys.stdout.write("\rBUMMER::Unable to connect to the Internet")
        speaker.speak(text=f"I was unable to connect to the internet {env.title}! Please check your connection.",
                      run=True)
    sys.stdout.write(f"\rCurrent Process ID: {os.getpid()}\tCurrent Volume: {env.volume}")
    shared.hosted_device = hosted_device_info()
    shared.processes = start_processes()
    with Microphone() as source:
        shared.source = source
        if env.macos and packaging.version.parse(platform.mac_ver()[0]) < packaging.version.parse('10.14'):
            sentry_mode()
        else:
            Activator().start()


if __name__ == '__main__':
    begin()
