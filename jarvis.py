import os
import struct
import sys
import time
from multiprocessing import Process
from pathlib import PurePath
from typing import Dict

import pvporcupine
from playsound import playsound
from pyaudio import PyAudio, paInt16

from api.server import trigger_api
from executors.commander import initiator
from executors.controls import exit_process, starter
from executors.internet import get_ssid, internet_checker
from executors.location import write_current_location
from executors.logger import logger
from executors.offline import automator, initiate_tunneling
from executors.system import hosted_device_info
from executors.telegram import poll_for_messages
from modules.audio import listener, speaker
from modules.models import models
from modules.utils import globals, support


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
        logger.info(f'Initiating model with sensitivity: {env.sensitivity}')
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
                sys.stdout.write('\rSentry Mode')
                if not self.audio_stream:
                    self.open_stream()
                pcm = self.audio_stream.read(num_frames=self.detector.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.detector.frame_length, pcm)
                if self.detector.process(pcm=pcm) >= 0:
                    self.close_stream()
                    playsound(sound='indicators/acknowledgement.mp3', block=False)
                    initiator(key_original=listener.listen(timeout=env.timeout, phrase_limit=env.phrase_limit,
                                                           sound=False),
                              should_return=True)
                    speaker.speak(run=True)
                elif globals.STOPPER['status']:
                    logger.info('Exiting sentry mode since the STOPPER flag was set.')
                    break
        except KeyboardInterrupt:
            self.stop()
            exit_process()
            support.terminator()

    def stop(self) -> None:
        """Invoked when the run loop is exited or manual interrupt.

        See Also:
            - Terminates/Kills all the background processes.
            - Releases resources held by porcupine.
            - Closes audio stream.
            - Releases port audio resources.
        """
        for func, process in globals.processes.items():
            if process.is_alive():
                logger.info(f'Sending [SIGTERM] to {func} with PID: {process.pid}')
                process.terminate()
            if process.is_alive():
                logger.info(f'Sending [SIGKILL] to {func} with PID: {process.pid}')
                process.kill()
        logger.info('Releasing resources acquired by Porcupine.')
        self.detector.delete()
        if self.audio_stream and self.audio_stream.is_active():
            logger.info('Closing Audio Stream.')
            self.audio_stream.close()
        logger.info('Releasing PortAudio resources.')
        self.py_audio.terminate()


def initiate_processes() -> Dict[str, Process]:
    """Initiate multiple background processes to achieve parallelization.

    Methods
        - poll_for_messages: Initiates polling for messages on the telegram bot.
        - trigger_api: Initiates Jarvis API using uvicorn server to receive offline commands.
        - automator: Initiates automator that executes offline commands and certain functions at said time.
        - initiate_tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - write_current_location: Writes current location details into a yaml file.
        - playsound: Plays a start-up sound.
    """
    processes = {
        'telebot': Process(target=poll_for_messages),
        'api': Process(target=trigger_api),
        'automator': Process(target=automator),
        'ngrok': Process(target=initiate_tunneling,
                         kwargs={'offline_host': env.offline_host, 'offline_port': env.offline_port, 'home': env.home}),
        'location': Process(target=write_current_location),
    }
    for func, process in processes.items():
        process.start()
        logger.info(f'Started function: {func} {process.sentinel} with PID: {process.pid}')
    playsound(sound='indicators/initialize.mp3', block=False)
    return processes


if __name__ == '__main__':
    env = models.env
    globals.hosted_device = hosted_device_info()
    if globals.hosted_device.get('os_name') != 'macOS':
        exit('Unsupported Operating System.\nWindows support was deprecated. '
             'Refer https://github.com/thevickypedia/Jarvis/commit/cf54b69363440d20e21ba406e4972eb058af98fc')

    logger.info('JARVIS::Starting Now')

    sys.stdout.write('\rVoice ID::Female: 1/17 Male: 0/7')  # Voice ID::reference
    starter()  # initiates crucial functions which needs to be called during start up

    if internet_checker():
        sys.stdout.write(f'\rINTERNET::Connected to {get_ssid()}. Scanning router for connected devices.')
    else:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.speak(text="I was unable to connect to the internet sir! Please check your connection and retry.",
                      run=True)
        sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                         f"\nTotal runtime: {support.time_converter(time.perf_counter())}")
        support.terminator()

    sys.stdout.write(f"\rCurrent Process ID: {os.getpid()}\tCurrent Volume: 50%")

    globals.processes = initiate_processes()

    Activator().start()
