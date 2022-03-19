import os
import platform
import struct
import sys
import time
from pathlib import PurePath

import packaging.version
import pvporcupine
import speech_recognition
from playsound import playsound
from pyaudio import PyAudio, paInt16

from executors.commander import initiator
from executors.controls import exit_process, restart, starter, terminator
from executors.internet import get_ssid, internet_checker
from executors.logger import logger
from executors.processor import start_processes, stop_processes
from executors.system import hosted_device_info
from modules.audio import listener, speaker
from modules.database import database
from modules.models import models
from modules.utils import globals, support

env = models.env
fileio = models.fileio

rdb = database.Database(table_name="restart", columns=["flag", "caller"])
odb = database.Database(table_name="offline", columns=["key", "value"])


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
        logger.info(f"Initiating model with sensitivity: {env.sensitivity}")
        keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in [PurePath(__file__).stem]]
        self.input_device_index = input_device_index

        self.py_audio = PyAudio()
        self.detector = pvporcupine.create(
            library_path=pvporcupine.LIBRARY_PATH,
            model_path=pvporcupine.MODEL_PATH,
            keyword_paths=keyword_paths,
            sensitivities=[env.sensitivity]
        )
        self.audio_stream = None

    def open_stream(self) -> None:
        """Initializes an audio stream."""
        self.audio_stream = self.py_audio.open(
            rate=self.detector.sample_rate,
            channels=1,
            format=paInt16,
            input=True,
            frames_per_buffer=self.detector.frame_length,
            input_device_index=self.input_device_index
        )

    def close_stream(self) -> None:
        """Closes audio stream so that other listeners can use microphone."""
        self.py_audio.close(stream=self.audio_stream)
        self.audio_stream = None

    def start(self) -> None:
        """Runs ``audio_stream`` in a forever loop and calls ``initiator`` when the phrase ``Jarvis`` is heard."""
        try:
            while True:
                sys.stdout.write("\rSentry Mode")
                if not self.audio_stream:
                    self.open_stream()
                pcm = self.audio_stream.read(num_frames=self.detector.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.detector.frame_length, pcm)
                if self.detector.process(pcm=pcm) >= 0:
                    playsound(sound="indicators/acknowledgement.mp3", block=False)
                    self.close_stream()
                    initiator(key_original=listener.listen(timeout=env.timeout, phrase_limit=env.phrase_limit,
                                                           sound=False),
                              should_return=True)
                    speaker.speak(run=True)
                elif flag := rdb.cursor.execute("SELECT flag, caller FROM restart").fetchone():
                    logger.info(f"Restart condition is set to {flag[0]} by {flag[1]}")
                    self.stop()
                    if flag[1] == "restart_control":
                        restart()
                    else:
                        restart(quiet=True)
                    break
        except KeyboardInterrupt:
            self.stop()
            exit_process()
            terminator()

    def stop(self) -> None:
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
            self.audio_stream.close()
        logger.info("Releasing PortAudio resources.")
        self.py_audio.terminate()


def sentry_mode() -> None:
    """Listens forever and invokes ``initiator()`` when recognized. Stops when ``restart`` table has an entry.

    See Also:
        Gets invoked only when run from Mac-OS older than 14.4.
    """
    while True:
        try:
            sys.stdout.write("\rSentry Mode")
            listened = recognizer.listen(source=source, timeout=10, phrase_time_limit=1)
            sys.stdout.write("\r")
            if not any(word in recognizer.recognize_google(listened).lower() for word in [
                'friday', 'jarvis', 'buddy', 'javis', 'you there', 'jealous'
            ]):
                continue
            playsound(sound="indicators/acknowledgement.mp3", block=False)
            initiator(key_original=listener.listen(timeout=env.timeout, phrase_limit=env.phrase_limit, sound=False),
                      should_return=True)
            speaker.speak(run=True)
        except (speech_recognition.UnknownValueError,
                speech_recognition.WaitTimeoutError,
                speech_recognition.RequestError):
            sys.stdout.write("\r")
        except KeyboardInterrupt:
            stop_processes()
            exit_process()
            terminator()
            break
        if flag := rdb.cursor.execute("SELECT flag, caller FROM restart").fetchone():
            logger.info(f"Restart condition is set to {flag[0]} by {flag[1]}")
            stop_processes()
            if flag[1] == "restart_control":
                restart()
            else:
                restart(quiet=True)
            break


if __name__ == '__main__':
    globals.hosted_device = hosted_device_info()
    if globals.hosted_device.get("os_name") != "macOS":
        exit("Unsupported Operating System.\nWindows support was deprecated. "
             "Refer https://github.com/thevickypedia/Jarvis/commit/cf54b69363440d20e21ba406e4972eb058af98fc")

    logger.info("JARVIS::Starting Now")

    sys.stdout.write("\rVoice ID::Female: 1/17 Male: 0/7")  # Voice ID::reference
    starter()  # initiates crucial functions which needs to be called during start up

    if internet_checker():
        sys.stdout.write(f"\rINTERNET::Connected to {get_ssid()}. Scanning router for connected devices.")
    else:
        sys.stdout.write("\rBUMMER::Unable to connect to the Internet")
        speaker.speak(text=f"I was unable to connect to the internet {env.title}! Please check your connection.",
                      run=True)
        sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                         f"\nTotal runtime: {support.time_converter(time.perf_counter())}")
        terminator()

    sys.stdout.write(f"\rCurrent Process ID: {os.getpid()}\tCurrent Volume: 50%")

    globals.processes = start_processes()

    if packaging.version.parse(platform.mac_ver()[0]) > packaging.version.parse('10.14'):
        Activator().start()
    else:
        recognizer = speech_recognition.Recognizer()
        with speech_recognition.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            sentry_mode()
