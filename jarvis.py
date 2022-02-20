import os
import random
import struct
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from pathlib import PurePath
from threading import Thread, Timer
from time import perf_counter, sleep, time

import psutil
import pvporcupine
from playsound import playsound
from pyaudio import PyAudio, paInt16

from api.server import trigger_api
from executors import controls, offline
from executors.alarm import alarm_executor, kill_alarm, set_alarm
from executors.automation import auto_helper, automation_handler
from executors.bluetooth import bluetooth
from executors.car import car
from executors.communicator import read_gmail, send_sms
from executors.date_time import current_date, current_time
from executors.display_functions import brightness
from executors.face import face_detection
from executors.github import github
from executors.guard import guard_enable
from executors.internet import get_ssid, internet_checker, ip_info, speed_test
from executors.lights import lights
from executors.location import (current_location, directions, distance, locate,
                                locate_places, location)
from executors.logger import logger
from executors.meetings import (meeting_file_writer, meeting_reader, meetings,
                                meetings_gatherer)
from executors.others import (apps, facts, flip_a_coin, google_home, jokes,
                              meaning, music, news, notes, repeat)
from executors.personalcloud import personal_cloud
from executors.remind import reminder, reminder_executor
from executors.robinhood import robinhood
from executors.system import hosted_device_info, system_info, system_vitals
from executors.todo_list import (add_todo, create_db, delete_db, delete_todo,
                                 todo)
from executors.tv import television
from executors.unconditional import alpha, google, google_maps, google_search
from executors.vpn_server import vpn_server
from executors.weather import weather
from executors.wiki import wikipedia_
from modules.audio.listener import listen
from modules.audio.speaker import audio_driver, speak
from modules.audio.voices import voice_changer, voice_default
from modules.audio.volume import switch_volumes, volume
from modules.conditions import conversation, keywords
from modules.utils import globals, support


def split(key: str, should_return: bool = False) -> bool:
    """Splits the input at 'and' or 'also' and makes it multiple commands to execute if found in statement.

    Args:
        key: Takes the voice recognized statement as argument.
        should_return: A boolean flag sent to ``conditions`` to indicate that the ``else`` part shouldn't be executed.

    Returns:
        bool:
        Return value from ``conditions()``
    """
    exit_check = False  # this is specifically to catch the sleep command which should break the while loop in renew()
    if ' and ' in key and not any(word in key.lower() for word in keywords.avoid):
        for each in key.split(' and '):
            exit_check = conditions(converted=each.strip(), should_return=should_return)
    elif ' also ' in key and not any(word in key.lower() for word in keywords.avoid):
        for each in key.split(' also '):
            exit_check = conditions(converted=each.strip(), should_return=should_return)
    else:
        exit_check = conditions(converted=key.strip(), should_return=should_return)
    return exit_check


def initialize() -> None:
    """Awakens from sleep mode. ``greet_check`` is to ensure greeting is given only for the first function call."""
    if globals.greet_check.get('status'):
        speak(text="What can I do for you?")
    else:
        speak(text=f'Good {support.part_of_day()}.')
        globals.greet_check['status'] = True
    renew()


def renew() -> None:
    """Keeps listening and sends the response to ``conditions()`` function.

    Notes:
        - This function runs only for a minute.
        - split(converted) is a condition so that, loop breaks when if sleep in ``conditions()`` returns True.
    """
    speak(run=True)
    waiter = 0
    while waiter < 12:
        waiter += 1
        if waiter == 1:
            converted = listen(timeout=3, phrase_limit=5)
        else:
            converted = listen(timeout=3, phrase_limit=5, sound=False)
        if converted == 'SR_ERROR':
            continue
        remove = ['buddy', 'jarvis', 'hey', 'hello', 'sr_error']
        converted = ' '.join([i for i in converted.split() if i.lower() not in remove])
        if converted:
            if split(key=converted):  # should_return flag is not passed which will default to False
                break  # split() returns what conditions function returns. Condition() returns True only for sleep.
        elif any(word in converted.lower() for word in remove):
            continue
        speak(run=True)


def conditions(converted: str, should_return: bool = False) -> bool:
    """Conditions function is used to check the message processed.

    Uses the keywords to do a regex match and trigger the appropriate function which has dedicated task.

    Args:
        converted: Takes the voice recognized statement as argument.
        should_return: A boolean flag sent by ``Activator`` to indicate that the ``else`` part shouldn't be executed.

    Returns:
        bool:
        Boolean True only when asked to sleep for conditioned sleep message.
    """
    logger.info(f'Request: {converted}')
    converted_lower = converted.lower()
    todo_checks = ['to do', 'to-do', 'todo']
    if any(word in converted_lower for word in keywords.current_date) and \
            not any(word in converted_lower for word in keywords.avoid):
        current_date()

    elif any(word in converted_lower for word in keywords.current_time) and \
            not any(word in converted_lower for word in keywords.avoid):
        current_time()

    elif any(word in converted_lower for word in keywords.weather) and \
            not any(word in converted_lower for word in keywords.avoid):
        weather(phrase=converted)

    elif any(word in converted_lower for word in keywords.system_info):
        system_info()

    elif any(word in converted for word in keywords.ip_info) or 'IP' in converted.split():
        ip_info(phrase=converted)

    elif any(word in converted_lower for word in keywords.wikipedia_):
        wikipedia_()

    elif any(word in converted_lower for word in keywords.news):
        news()

    elif any(word in converted_lower for word in keywords.report):
        report()

    elif any(word in converted_lower for word in keywords.robinhood):
        robinhood()

    elif any(word in converted_lower for word in keywords.repeat):
        repeat()

    elif any(word in converted_lower for word in keywords.location):
        location()

    elif any(word in converted_lower for word in keywords.locate):
        locate(phrase=converted)

    elif any(word in converted_lower for word in keywords.read_gmail):
        read_gmail()

    elif any(word in converted_lower for word in keywords.meaning):
        meaning(phrase=converted)

    elif any(word in converted_lower for word in keywords.delete_todo) and \
            any(word in converted_lower for word in todo_checks):
        delete_todo()

    elif any(word in converted_lower for word in keywords.todo):
        todo()

    elif any(word in converted_lower for word in keywords.add_todo) and \
            any(word in converted_lower for word in todo_checks):
        add_todo()

    elif any(word in converted_lower for word in keywords.delete_db):
        delete_db()

    elif any(word in converted_lower for word in keywords.create_db):
        create_db()

    elif any(word in converted_lower for word in keywords.distance) and \
            not any(word in converted_lower for word in keywords.avoid):
        distance(phrase=converted)

    elif any(word in converted_lower for word in keywords.car):
        car(phrase=converted_lower)

    elif any(word in converted_lower for word in conversation.form):
        speak(text="I am a program, I'm without form.")

    elif any(word in converted_lower for word in keywords.locate_places):
        locate_places(phrase=converted)

    elif any(word in converted_lower for word in keywords.directions):
        directions(phrase=converted)

    elif any(word in converted_lower for word in keywords.kill_alarm):
        kill_alarm()

    elif any(word in converted_lower for word in keywords.set_alarm):
        set_alarm(phrase=converted)

    elif any(word in converted_lower for word in keywords.google_home):
        google_home()

    elif any(word in converted_lower for word in keywords.jokes):
        jokes()

    elif any(word in converted_lower for word in keywords.reminder):
        reminder(phrase=converted)

    elif any(word in converted_lower for word in keywords.notes):
        notes()

    elif any(word in converted_lower for word in keywords.github):
        github(phrase=converted)

    elif any(word in converted_lower for word in keywords.send_sms):
        send_sms(phrase=converted)

    elif any(word in converted_lower for word in keywords.google_search):
        google_search(phrase=converted)

    elif any(word in converted_lower for word in keywords.television):
        television(phrase=converted)

    elif any(word in converted_lower for word in keywords.apps):
        apps(phrase=converted)

    elif any(word in converted_lower for word in keywords.music):
        music(phrase=converted)

    elif any(word in converted_lower for word in keywords.volume):
        volume(phrase=converted)

    elif any(word in converted_lower for word in keywords.face_detection):
        face_detection()

    elif any(word in converted_lower for word in keywords.speed_test):
        speed_test()

    elif any(word in converted_lower for word in keywords.bluetooth):
        bluetooth(phrase=converted)

    elif any(word in converted_lower for word in keywords.brightness) and 'lights' not in converted_lower:
        brightness(phrase=converted)

    elif any(word in converted_lower for word in keywords.lights):
        lights(phrase=converted)

    elif any(word in converted_lower for word in keywords.guard_enable):
        guard_enable()

    elif any(word in converted_lower for word in keywords.flip_a_coin):
        flip_a_coin()

    elif any(word in converted_lower for word in keywords.facts):
        facts()

    elif any(word in converted_lower for word in keywords.meetings):
        meetings()

    elif any(word in converted_lower for word in keywords.voice_changer):
        voice_changer(phrase=converted)

    elif any(word in converted_lower for word in keywords.system_vitals):
        system_vitals()

    elif any(word in converted_lower for word in keywords.vpn_server):
        vpn_server(phrase=converted)

    elif any(word in converted_lower for word in keywords.personal_cloud):
        personal_cloud(phrase=converted)

    elif any(word in converted_lower for word in keywords.automation):
        automation_handler(phrase=converted_lower)

    elif any(word in converted_lower for word in conversation.greeting):
        speak(text='I am spectacular. I hope you are doing fine too.')

    elif any(word in converted_lower for word in conversation.capabilities):
        speak(text='There is a lot I can do. For example: I can get you the weather at any location, news around '
                   'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                   'system configuration, tell your investment details, locate your phone, find distance between '
                   'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
                   ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')

    elif any(word in converted_lower for word in conversation.languages):
        speak(text="Tricky question!. I'm configured in python, and I can speak English.")

    elif any(word in converted_lower for word in conversation.whats_up):
        speak(text="My listeners are up. There is nothing I cannot process. So ask me anything..")

    elif any(word in converted_lower for word in conversation.what):
        speak(text="I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")

    elif any(word in converted_lower for word in conversation.who):
        speak(text="I am Jarvis. A virtual assistant designed by Mr.Raauv.")

    elif any(word in converted_lower for word in conversation.about_me):
        speak(text="I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        speak(text="I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")
        speak(text="I can seamlessly take care of your daily tasks, and also help with most of your work!")

    elif any(word in converted_lower for word in keywords.sleep_control):
        return controls.sleep_control(phrase=converted)

    elif any(word in converted_lower for word in keywords.restart_control):
        controls.restart_control(phrase=converted)

    elif any(word in converted_lower for word in keywords.kill) and \
            not any(word in converted_lower for word in keywords.avoid):
        raise KeyboardInterrupt

    elif any(word in converted_lower for word in keywords.shutdown):
        controls.shutdown()

    elif should_return:
        Thread(target=support.unrecognized_dumper, args=[{'ACTIVATOR': converted}]).start()
        return False

    else:
        logger.info(f'Received the unrecognized lookup parameter: {converted}')
        Thread(target=support.unrecognized_dumper, args=[{'CONDITIONS': converted}]).start()
        if alpha(text=converted):
            if google_maps(query=converted):
                if google(query=converted):
                    # if none of the conditions above are met, opens a Google search on default browser
                    search_query = str(converted).replace(' ', '+')
                    unknown_url = f"https://www.google.com/search?q={search_query}"
                    webbrowser.open(url=unknown_url)


def report() -> None:
    """Initiates a list of functions, that I tend to check first thing in the morning."""
    sys.stdout.write("\rStarting today's report")
    globals.called['report'] = True
    current_date()
    current_time()
    weather()
    todo()
    read_gmail()
    robinhood()
    news()
    globals.called['report'] = False


def time_travel() -> None:
    """Triggered only from ``initiator()`` to give a quick update on the user's daily routine."""
    part_day = support.part_of_day()
    meeting = None
    if not os.path.isfile('meetings') and part_day == 'Morning' and datetime.now().strftime('%A') not in \
            ['Saturday', 'Sunday']:
        meeting = ThreadPool(processes=1).apply_async(func=meetings_gatherer, kwds={'logger': logger})
    speak(text=f"Good {part_day} Vignesh.")
    if part_day == 'Night':
        if event := support.celebrate():
            speak(text=f'Happy {event}!')
        return
    current_date()
    current_time()
    weather()
    speak(run=True)
    if os.path.isfile('meetings') and part_day == 'Morning' and datetime.now().strftime('%A') not in \
            ['Saturday', 'Sunday']:
        meeting_reader()
    elif meeting:
        try:
            speak(text=meeting.get(timeout=30))
        except ThreadTimeoutError:
            pass  # skip terminate, close and join thread since the motive is to skip meetings info in case of a timeout
    todo()
    read_gmail()
    speak(text='Would you like to hear the latest news?', run=True)
    phrase = listen(timeout=3, phrase_limit=3)
    if any(word in phrase.lower() for word in keywords.ok):
        news()
    globals.called['time_travel'] = False


def offline_communicator(command: str = None, respond: bool = True) -> None:
    """Reads ``offline_request`` file generated by `fast.py <https://git.io/JBPFQ>`__ containing request sent via API.

    Args:
        command: Takes the command that has to be executed as an argument.
        respond: Takes the argument to decide whether to create the ``offline_response`` file.

    Env Vars:
        - ``offline_pass`` - Phrase to authenticate the requests to API. Defaults to ``jarvis``

    Notes:
        More cool stuff (Done by ``JarvisHelper``):
            - Run ``ngrok http`` on port 4483 or any desired port set as an env var ``offline_port``.
            - I have linked the ngrok ``public_url`` tunnelling the FastAPI to a JavaScript on my webpage.
            - When a request is submitted, the JavaScript makes a POST call to the API.
            - The API does the authentication and creates the ``offline_request`` file if authenticated.
            - Check it out: `JarvisOffline <https://thevickypedia.com/jarvisoffline>`__

    Warnings:
        - Restarts ``Jarvis`` quietly in case of a ``RuntimeError`` however, the offline request will still be executed.
        - This happens when ``speaker`` is stopped while another loop of speaker is in progress by regular interaction.
    """
    response = None
    try:
        if command:
            os.remove('offline_request') if respond else None
            globals.called_by_offline['status'] = True
            split(command)
            globals.called_by_offline['status'] = False
            response = globals.text_spoken.get('text')
        else:
            response = 'Received a null request. Please resend it.'
        if 'restart' not in command and respond:
            with open('offline_response', 'w') as off_response:
                off_response.write(response)
        audio_driver.stop()
        voice_default()
    except RuntimeError as error:
        if command and not response:
            with open('offline_request', 'w') as off_request:
                off_request.write(command)
        logger.fatal(f'Received a RuntimeError while executing offline request.\n{error}')
        controls.restart(quiet=True, quick=True)


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
            speak(text=f'Happy {event}!')
        if 'night' in key_split or 'goodnight' in key_split:
            Thread(target=controls.pc_sleep).start()
        time_travel()
    elif 'you there' in key:
        speak(text=f'{random.choice(conversation.wake_up1)}')
        initialize()
    elif any(word in key for word in ['look alive', 'wake up', 'wakeup', 'show time', 'showtime']):
        speak(text=f'{random.choice(conversation.wake_up2)}')
        initialize()
    else:
        converted = ' '.join([i for i in key_original.split() if i.lower() not in ['buddy', 'jarvis', 'sr_error']])
        if converted:
            split(key=converted.strip(), should_return=should_return)
        else:
            speak(text=f'{random.choice(conversation.wake_up3)}')
            initialize()


def automator(automation_file: str = 'automation.json', every_1: int = 1_800, every_2: int = 3_600) -> None:
    """Place for long-running background threads.

    Args:
        automation_file: Takes the automation filename as an argument.
        every_1: Triggers every 30 minutes in a dedicated thread, to switch volumes to time based levels.
        every_2: Triggers every 60 minutes in a dedicated thread, to initiate ``meeting_file_writer``.

    See Also:
        - Keeps looking for the ``offline_request`` file, and invokes ``offline_communicator`` with content as the arg.
        - The ``automation_file`` should be a JSON file of dictionary within a dictionary that looks like the below:

            .. code-block:: json

                {
                  "6:00 AM": {
                    "task": "set my bedroom lights to 50%",
                    "status": false
                  },
                  "9:00 PM": {
                    "task": "set my bedroom lights to 5%",
                    "status": false
                  }
                }

        - The status for all automations can be set to either ``true`` or ``false``.
        - Jarvis will swap these flags as necessary, so that the execution doesn't repeat more than once in a minute.
    """
    start_1 = start_2 = time()
    while True:
        if os.path.isfile('offline_request'):
            sleep(0.1)  # Read file after 0.1 second for the content to be written
            with open('offline_request') as off_request:
                request = off_request.read()
            Thread(target=offline_communicator, kwargs={'command': request}).start()
            support.flush_screen()
        if os.path.isfile(automation_file):
            with ThreadPoolExecutor() as executor:
                if exec_task := executor.submit(auto_helper, automation_file).result():
                    Thread(target=offline_communicator, kwargs={'command': exec_task, 'respond': False}).start()
        if start_1 + every_1 <= time():
            start_1 = time()
            Thread(target=switch_volumes).start()
        if start_2 + every_2 <= time():
            start_2 = time()
            Thread(target=meeting_file_writer).start()
        if alarm_state := support.lock_files(alarm_files=True):
            for each_alarm in alarm_state:
                if each_alarm == datetime.now().strftime("%I_%M_%p.lock"):
                    Thread(target=alarm_executor).start()
                    os.remove(f'alarm/{each_alarm}')
        if reminder_state := support.lock_files(reminder_files=True):
            for each_reminder in reminder_state:
                remind_time, remind_msg = each_reminder.split('-')
                remind_msg = remind_msg.rstrip('.lock')
                if remind_time == datetime.now().strftime("%I_%M_%p"):
                    Thread(target=reminder_executor, args=[remind_msg]).start()
                    os.remove(f'reminder/{each_reminder}')
        if globals.STOPPER['status']:
            logger.warning('Exiting automator since the STOPPER flag was set.')
            break


class Activator:
    """Awaits for the keyword ``Jarvis`` and triggers ``initiator`` when heard.

    >>> Activator

    See Also:
        - Creates an input audio stream from a microphone, monitors it, and detects the specified wake word.
        - Once detected, Jarvis triggers the ``listen()`` function with an ``acknowledgement`` sound played.
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
                    initiator(key_original=listen(timeout=env.timeout, phrase_limit=env.phrase_limit, sound=False),
                              should_return=True)
                    speak(run=True)
                elif globals.STOPPER['status']:
                    self.stop()
                    controls.restart(quiet=True)
        except KeyboardInterrupt:
            self.stop()
            if not globals.called_by_offline['status']:
                controls.exit_process()
                support.terminator()

    def stop(self) -> None:
        """Invoked when the run loop is exited or manual interrupt.

        See Also:
            - Releases resources held by porcupine.
            - Closes audio stream.
            - Releases port audio resources.
        """
        logger.info('Releasing resources acquired by Porcupine.')
        self.detector.delete()
        if self.audio_stream and self.audio_stream.is_active():
            logger.info('Closing Audio Stream.')
            self.audio_stream.close()
        logger.info('Releasing PortAudio resources.')
        self.py_audio.terminate()


def initiate_background_threads() -> None:
    """Initiate background threads.

    Methods
        - stopper: Initiates stopper to restart after a set time using ``threading.Timer``
        - initiate_tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - trigger_api: Initiates Jarvis API using uvicorn server in a thread.
        - automator: Initiates automator that executes certain functions at said time.
        - playsound: Plays a start-up sound.
    """
    Timer(interval=env.restart_interval, function=controls.stopper).start()
    Thread(target=offline.initiate_tunneling,
           kwargs={'offline_host': env.offline_host, 'offline_port': env.offline_port, 'home': env.home}).start()
    trigger_api()
    Thread(target=automator).start()
    playsound(sound='indicators/initialize.mp3', block=False)


if __name__ == '__main__':
    env = globals.ENV
    globals.hosted_device = hosted_device_info()
    if globals.hosted_device.get('os_name') != 'macOS':
        exit('Unsupported Operating System.\nWindows support was deprecated. '
             'Refer https://github.com/thevickypedia/Jarvis/commit/cf54b69363440d20e21ba406e4972eb058af98fc')

    logger.info('JARVIS::Starting Now')

    sys.stdout.write('\rVoice ID::Female: 1/17 Male: 0/7')  # Voice ID::reference
    controls.starter()  # initiates crucial functions which needs to be called during start up

    if st := internet_checker():
        sys.stdout.write(f'\rINTERNET::Connected to {get_ssid()}. Scanning router for connected devices.')
    else:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speak(text="I was unable to connect to the internet sir! Please check your connection settings and retry.",
              run=True)
        sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                         f"\nTotal runtime: {support.time_converter(perf_counter())}")
        support.terminator()

    globals.current_location_ = current_location()
    globals.smart_devices = support.scan_smart_devices()

    sys.stdout.write(f"\rCurrent Process ID: {psutil.Process(os.getpid()).pid}\tCurrent Volume: 50%")

    initiate_background_threads()

    Activator().start()
