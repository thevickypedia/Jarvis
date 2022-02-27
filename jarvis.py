import os
import random
import struct
import sys
import time
from multiprocessing import Process
from pathlib import PurePath
from threading import Thread
from typing import Dict

import pvporcupine
from playsound import playsound
from pyaudio import PyAudio, paInt16

from api.server import trigger_api
from executors.controls import exit_process, pc_sleep, restart, starter
from executors.internet import get_ssid, internet_checker
from executors.location import write_current_location
from executors.logger import logger
from executors.offline import automator, initiate_tunneling
from executors.others import time_travel
from executors.splitter import split_phrase
from executors.system import hosted_device_info
from modules.audio import listener, speaker
from modules.conditions import conversation
from modules.models import models
from modules.utils import globals, support

env = models.env


def initialize() -> None:
    """Awakens from sleep mode. ``greet_check`` is to ensure greeting is given only for the first function call."""
    if globals.greet_check.get('status'):
        speaker.speak(text="What can I do for you?")
    else:
        speaker.speak(text=f'Good {support.part_of_day()}.')
        globals.greet_check['status'] = True
    renew()


def renew() -> None:
    """Keeps listening and sends the response to ``conditions()`` function.

    Notes:
        - This function runs only for a minute.
        - split_phrase(converted) is a condition so that, loop breaks when if sleep in ``conditions()`` returns True.
    """
    speaker.speak(run=True)
    waiter = 0
    while waiter < 12:
        waiter += 1
        if waiter == 1:
            converted = listener.listen(timeout=3, phrase_limit=5)
        else:
            converted = listener.listen(timeout=3, phrase_limit=5, sound=False)
        if converted == 'SR_ERROR':
            continue
        remove = ['buddy', 'jarvis', 'hey', 'hello', 'sr_error']
        converted = ' '.join([i for i in converted.split() if i.lower() not in remove])
        if converted:
            if split_phrase(key=converted):  # should_return flag is not passed which will default to False
                break  # split_phrase() returns a boolean flag from conditions. conditions return True only for sleep
        elif any(word in converted.lower() for word in remove):
            continue
        speaker.speak(run=True)


def initiator(key_original: str, should_return: bool = False) -> None:
    """When invoked by ``Activator``, checks for the right keyword to wake up and gets into action.

    Args:
        key_original: Takes the processed string from ``SentryMode`` as input.
        should_return: Flag to return the function if nothing is heard.
    """
    if key_original == 'SR_ERROR' and should_return:
        return
    support.flush_screen()
    key = key_original.lower()
    key_split = key.split()
    if [word for word in key_split if word in ['morning', 'night', 'afternoon', 'after noon', 'evening', 'goodnight']]:
        globals.called['time_travel'] = True
        if event := support.celebrate():
            speaker.speak(text=f'Happy {event}!')
        if 'night' in key_split or 'goodnight' in key_split:
            Thread(target=pc_sleep).start()
        time_travel()
    elif 'you there' in key:
        speaker.speak(text=f'{random.choice(conversation.wake_up1)}')
        initialize()
    elif any(word in key for word in ['look alive', 'wake up', 'wakeup', 'show time', 'showtime']):
        speaker.speak(text=f'{random.choice(conversation.wake_up2)}')
        initialize()
    else:
        converted = ' '.join([i for i in key_original.split() if i.lower() not in ['buddy', 'jarvis', 'sr_error']])
        if converted:
            split_phrase(key=converted.strip(), should_return=should_return)
        else:
            speaker.speak(text=f'{random.choice(conversation.wake_up3)}')
            initialize()


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
                    self.stop()
                    restart(quiet=True)
                    break
        except KeyboardInterrupt:
            self.stop()
            if not globals.called_by_offline['status']:
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
                logger.info(f'Terminating {func} sending [SIGTERM] signal: {process.pid}')
                process.terminate()
                if process.is_alive():
                    logger.info(f'Killing {func} sending [SIGKILL] signal: {process.pid}')
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
        - initiate_tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - write_current_location: Writes current location details into a yaml file.
        - trigger_api: Initiates Jarvis API using uvicorn server to receive offline commands.
        - automator: Initiates automator that executes offline commands and certain functions at said time.
        - playsound: Plays a start-up sound.
    """
    processes = {
        'ngrok': Process(target=initiate_tunneling,
                         kwargs={'offline_host': env.offline_host, 'offline_port': env.offline_port, 'home': env.home}),
        'location': Process(target=write_current_location),
        'api': Process(target=trigger_api),
        'automator': Process(target=automator)
    }
    for func, process in processes.items():
        process.start()
        logger.info(f'Started function: {func} {process.sentinel} with PID: {process.pid}')
    playsound(sound='indicators/initialize.mp3', block=False)
    return processes


if __name__ == '__main__':
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
