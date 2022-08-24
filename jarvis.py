import logging
import struct
import sys
from datetime import datetime
from typing import NoReturn

import pvporcupine
from playsound import playsound
from pyaudio import PyAudio, paInt16

from executors.commander import initiator
from executors.controls import (check_memory_leak, exit_process, starter,
                                terminator)
from executors.internet import get_ssid, ip_address
from executors.logger import custom_handler, logger
from executors.offline import repeated_tasks
from executors.processor import clear_db, start_processes, stop_processes
from executors.system import hosted_device_info
from executors.word_match import word_match
from modules.audio import listener, speaker
from modules.exceptions import StopSignal
from modules.models import models
from modules.utils import shared, support


def restart_checker() -> NoReturn:
    """Operations performed during internal/external request to restart."""
    if flag := support.check_restart():
        logger.info(f"Restart condition is set to {flag[0]} by {flag[1]}")
        if flag[1] == "OFFLINE":
            stop_processes()
            logger.propagate = False
            for _handler in logger.handlers:
                if isinstance(_handler, logging.FileHandler):
                    logger.removeHandler(hdlr=_handler)
            handler = custom_handler()
            logger.info(f"Switching to {handler.baseFilename}")
            logger.addHandler(hdlr=handler)
            starter()
            shared.processes = start_processes()
        else:
            stop_processes(func_name=flag[1])
            shared.processes[flag[1]] = start_processes(flag[1])


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
        logger.info(f"Initiating hot-word detector with sensitivity: {models.env.sensitivity}")
        keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in models.env.wake_words]
        self.input_device_index = input_device_index

        self.py_audio = PyAudio()
        self.detector = pvporcupine.create(
            library_path=pvporcupine.LIBRARY_PATH,
            model_path=pvporcupine.MODEL_PATH,
            keyword_paths=keyword_paths,
            sensitivities=[models.env.sensitivity]
        )
        self.audio_stream = None
        self.tasks = repeated_tasks()

    def open_stream(self) -> NoReturn:
        """Initializes an audio stream."""
        self.audio_stream = self.py_audio.open(
            rate=self.detector.sample_rate,
            channels=1,
            format=paInt16,
            input=True,
            frames_per_buffer=self.detector.frame_length,
            input_device_index=self.input_device_index
        )

    def close_stream(self) -> NoReturn:
        """Closes audio stream so that other listeners can use microphone."""
        self.py_audio.close(stream=self.audio_stream)
        self.audio_stream = None

    def start(self) -> NoReturn:
        """Runs ``audio_stream`` in a forever loop and calls ``initiator`` when the phrase ``Jarvis`` is heard."""
        try:
            while True:
                sys.stdout.write("\rSentry Mode")
                if not self.audio_stream:
                    self.open_stream()
                pcm = struct.unpack_from("h" * self.detector.frame_length,
                                         self.audio_stream.read(num_frames=self.detector.frame_length,
                                                                exception_on_overflow=False))
                result = self.detector.process(pcm=pcm)
                if result >= 0:
                    models.settings.bot = models.env.wake_words[result]
                    logger.debug(f"Detected {models.settings.bot} at {datetime.now()}")
                    playsound(sound=models.indicators.acknowledgement, block=False)
                    self.close_stream()
                    if phrase := listener.listen(timeout=models.env.timeout, phrase_limit=models.env.phrase_limit,
                                                 sound=False):
                        initiator(phrase=phrase, should_return=True)
                        speaker.speak(run=True)
                if models.settings.limited:
                    continue
                support.flush_screen()
                restart_checker()
                if flag := support.check_stop():
                    logger.info(f"Stopper condition is set to {flag[0]} by {flag[1]}")
                    self.stop()
                    terminator()
                if proc := check_memory_leak():
                    del shared.processes[proc]
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
        for task in self.tasks:
            task.stop()
        if not models.settings.limited:
            stop_processes()
        clear_db()
        logger.info("Releasing resources acquired by Porcupine.")
        self.detector.delete()
        if self.audio_stream and self.audio_stream.is_active():
            logger.info("Closing Audio Stream.")
            self.py_audio.close(stream=self.audio_stream)
            self.audio_stream.close()
        logger.info("Releasing PortAudio resources.")
        self.py_audio.terminate()


def sentry_mode() -> NoReturn:
    """Listens forever and invokes ``initiator()`` when recognized. Stops when ``restart`` table has an entry.

    See Also:
        - Gets invoked only when run from Mac-OS older than 10.14.
        - A regular listener is used to convert audio to text.
        - The text is then condition matched for wake-up words.
        - Additional wake words can be passed in a list as an env var ``LEGACY_KEYWORDS``.
    """
    try:
        tasks = repeated_tasks()
        while True:
            sys.stdout.write("\rSentry Mode")
            if wake_word := listener.listen(timeout=10, phrase_limit=2.5, sound=False, stdout=False):
                support.flush_screen()
                if word := word_match(phrase=wake_word.lower(), match_list=models.env.wake_words):
                    models.settings.bot = word
                    logger.debug(f"Detected {word} at {datetime.now()}")
                    playsound(sound=models.indicators.acknowledgement, block=False)
                    if phrase := listener.listen(timeout=models.env.timeout, phrase_limit=models.env.phrase_limit,
                                                 sound=False):
                        initiator(phrase=phrase, should_return=True)
                        speaker.speak(run=True)
            if models.settings.limited:
                continue
            restart_checker()
            if flag := support.check_stop():
                logger.info(f"Stopper condition is set to {flag[0]} by {flag[1]}")
                for task in tasks:
                    task.stop()
                if not models.settings.limited:
                    stop_processes()
                clear_db()
                terminator()
            if proc := check_memory_leak():
                del shared.processes[proc]
    except StopSignal:
        exit_process()
        if not models.settings.limited:
            stop_processes()
        clear_db()
        terminator()


def begin() -> NoReturn:
    """Starts main process to activate Jarvis after checking internet connection and initiating background processes."""
    logger.info(f"Current Process ID: {models.settings.pid}")
    starter()
    if ip_address():
        sys.stdout.write(f"\rINTERNET::Connected to {get_ssid() or 'the internet'}.")
    else:
        sys.stdout.write("\rBUMMER::Unable to connect to the Internet")
        speaker.speak(text=f"I was unable to connect to the internet {models.env.title}! Please check your connection.",
                      run=True)
    sys.stdout.write(f"\rCurrent Process ID: {models.settings.pid}\tCurrent Volume: {models.env.volume}")
    shared.hosted_device = hosted_device_info()
    if not models.settings.limited:
        shared.processes = start_processes()
    playsound(sound=models.indicators.initialize, block=False)
    sentry_mode() if models.settings.legacy else Activator().start()


if __name__ == '__main__':
    begin()
