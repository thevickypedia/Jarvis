import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email import message_from_bytes
from email.header import decode_header, make_header
from imaplib import IMAP4_SSL
from json import dumps as json_dumps
from json import load as json_load
from json import loads as json_loads
from math import ceil, floor, log, pow
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from pathlib import Path
from platform import platform, system
from random import choice, choices, randrange
from shutil import disk_usage
from socket import AF_INET, SOCK_DGRAM, gethostname, socket
from ssl import create_default_context
from string import ascii_letters, digits
from struct import unpack_from
from subprocess import PIPE, Popen, call, check_output, getoutput
from threading import Thread
from time import perf_counter, sleep, time
from traceback import format_exc
from typing import Tuple, Union
from unicodedata import normalize
from urllib.request import urlopen
from webbrowser import open as web_open

from aeosa.aem.aemsend import EventError
from appscript import app as apple_script
from appscript.reference import CommandError
from certifi import where
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from dotenv import load_dotenv, set_key, unset_key
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from gmailconnector.send_email import SendEmail
from gmailconnector.send_sms import Messenger
from googlehomepush import GoogleHome
from googlehomepush.http_server import serve_file
from holidays import CountryHoliday
from inflect import engine
from joke.jokes import chucknorris, geek, icanhazdad, icndb
from newsapi import NewsApiClient, newsapi_exception
from playsound import playsound
from psutil import Process, boot_time, cpu_count, virtual_memory
from pvporcupine import KEYWORD_PATHS, LIBRARY_PATH, MODEL_PATH, create
from pyaudio import PyAudio, paInt16
from pychromecast.error import ChromecastConnectionError
from PyDictionary import PyDictionary
from pyicloud import PyiCloudService
from pyicloud.exceptions import (PyiCloudAPIResponseException,
                                 PyiCloudFailedLoginException)
from pyicloud.services.findmyiphone import AppleDevice
from pyrh import Robinhood
from pyttsx3 import init
from pytz import timezone
from randfacts import getFact
from requests import exceptions as requests_exceptions
from requests import get
from requests.auth import HTTPBasicAuth
from search_engine_parser.core.engines.google import Search as GoogleSearch
from search_engine_parser.core.exceptions import NoResultsOrTrafficError
from speech_recognition import (Microphone, Recognizer, RequestError,
                                UnknownValueError, WaitTimeoutError)
from speedtest import ConfigRetrievalError, Speedtest
from timezonefinder import TimezoneFinder
from wakeonlan import send_magic_packet as wake
from wikipedia import exceptions as wiki_exceptions
from wikipedia import summary
from wolframalpha import Client as Think
from wordninja import split as splitter
from yaml import FullLoader
from yaml import dump as yaml_dump
from yaml import load as yaml_load

from helper_functions.alarm import Alarm
from helper_functions.conversation import Conversation
from helper_functions.database import Database, file_name
from helper_functions.facial_recognition import Face
from helper_functions.ip_scanner import LocalIPScan
from helper_functions.keywords import Keywords
from helper_functions.lights import MagicHomeApi
from helper_functions.logger import logger
from helper_functions.preset_values import preset_values
from helper_functions.reminder import Reminder
from helper_functions.robinhood import RobinhoodGatherer
from helper_functions.temperature import Temperature
from helper_functions.tv_controls import TV


def listener(timeout: int, phrase_limit: int, sound: bool = True) -> str:
    """Function to activate listener, this function will be called by most upcoming functions to listen to user input.

    Args:
        timeout: Time in seconds for the overall listener to be active.
        phrase_limit: Time in seconds for the listener to actively listen to a sound.
        sound: Flag whether or not to play the listener indicator sound. Defaults to True unless set to False.

    Returns:
        str:
         - On success, returns recognized statement from the microphone.
         - On failure, returns ``SR_ERROR`` as a string which is conditioned to respond appropriately.
    """
    try:
        sys.stdout.write("\rListener activated..") and playsound('indicators/start.mp3') if sound else \
            sys.stdout.write("\rListener activated..")
        listened = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        sys.stdout.write("\r") and playsound('indicators/end.mp3') if sound else sys.stdout.write("\r")
        return_val = recognizer.recognize_google(listened)
        sys.stdout.write(f'\r{return_val}')
    except (UnknownValueError, RequestError, WaitTimeoutError):
        return_val = 'SR_ERROR'
    return return_val


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
    if ' and ' in key and not any(word in key.lower() for word in keywords.avoid()):
        for each in key.split(' and '):
            exit_check = conditions(converted=each.strip(), should_return=should_return)
    elif ' also ' in key and not any(word in key.lower() for word in keywords.avoid()):
        for each in key.split(' also '):
            exit_check = conditions(converted=each.strip(), should_return=should_return)
    else:
        exit_check = conditions(converted=key.strip(), should_return=should_return)
    return exit_check


def part_of_day() -> str:
    """Checks the current hour to determine the part of day.

    Returns:
        str:
        Morning, Afternoon, Evening or Night based on time of day.
    """
    am_pm = datetime.now().strftime("%p")
    current_hour = int(datetime.now().strftime("%I"))
    if current_hour in range(4, 12) and am_pm == 'AM':
        greet = 'Morning'
    elif am_pm == 'PM' and (current_hour == 12 or current_hour in range(1, 4)):
        greet = 'Afternoon'
    elif current_hour in range(4, 8) and am_pm == 'PM':
        greet = 'Evening'
    else:
        greet = 'Night'
    return greet


def initialize() -> None:
    """Awakens from sleep mode. ``greet_check`` is to ensure greeting is given only for the first function call."""
    if greet_check.get('status'):
        speaker.say("What can I do for you?")
    else:
        speaker.say(f'Good {part_of_day()}.')
        greet_check['status'] = True
    renew()


def renew() -> None:
    """Keeps listening and sends the response to ``conditions()`` function.

    Notes:
        - This function runs only for a minute.
        - split(converted) is a condition so that, loop breaks when if sleep in ``conditions()`` returns True.
    """
    speaker.runAndWait()
    waiter = 0
    while waiter < 12:
        waiter += 1
        try:
            if waiter == 1:
                converted = listener(timeout=3, phrase_limit=5)
            else:
                converted = listener(timeout=3, phrase_limit=5, sound=False)
            remove = ['buddy', 'jarvis', 'hey', 'hello', 'sr_error']
            converted = ' '.join([i for i in converted.split() if i.lower() not in remove])
            if converted:
                if split(key=converted):  # should_return flag is not passed which will default to False
                    break  # split() returns what conditions function returns. Condition() returns True only for sleep.
            speaker.runAndWait()
        except (UnknownValueError, RequestError, WaitTimeoutError):
            pass


def time_converter(seconds: float) -> str:
    """Modifies seconds to appropriate days/hours/minutes/seconds.

    Args:
        seconds: Takes number of seconds as argument.

    Returns:
        str:
        Seconds converted to days or hours or minutes or seconds.
    """
    days = round(seconds // 86400)
    seconds = round(seconds % (24 * 3600))
    hours = round(seconds // 3600)
    seconds %= 3600
    minutes = round(seconds // 60)
    seconds %= 60
    if days:
        return f'{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds'
    elif hours:
        return f'{hours} hours, {minutes} minutes, and {seconds} seconds'
    elif minutes:
        return f'{minutes} minutes, and {seconds} seconds'
    elif seconds:
        return f'{seconds} seconds'


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
    sys.stdout.write(f'\r{converted}')
    converted_lower = converted.lower()
    todo_checks = ['to do', 'to-do', 'todo']
    if any(word in converted_lower for word in keywords.date()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        current_date()

    elif any(word in converted_lower for word in keywords.time()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        if place and len(place) < 3:
            current_time(place)
        else:
            current_time()

    elif any(word in converted_lower for word in keywords.weather()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        weather_cond = ['tomorrow', 'day after', 'next week', 'tonight', 'afternoon', 'evening']
        if any(match in converted_lower for match in weather_cond):
            if place:
                weather_condition(msg=converted, place=place)
            else:
                weather_condition(msg=converted)
        elif place:
            weather(place)
        else:
            weather()

    elif any(word in converted_lower for word in keywords.system_info()):
        system_info()

    elif any(word in converted for word in keywords.ip_info()) or 'IP' in converted.split():
        if 'public' in converted_lower:
            if not internet_checker():
                speaker.say("You are not connected to the internet sir!")
                return False
            if ssid := get_ssid():
                ssid = f'for the connection {ssid} '
            else:
                ssid = ''
            if public_ip := json_load(urlopen('http://ipinfo.io/json')).get('ip'):
                output = f"My public IP {ssid}is {public_ip}"
            elif public_ip := json_loads(urlopen('http://ip.jsontest.com').read()).get('ip'):
                output = f"My public IP {ssid}is {public_ip}"
            else:
                output = 'I was unable to fetch the public IP sir!'
        else:
            ip_address = vpn_checker().split(':')[-1]
            output = f"My local IP address for {gethostname()} is {ip_address}"
        sys.stdout.write(f'\r{output}')
        speaker.say(output)

    elif any(word in converted_lower for word in keywords.wikipedia()):
        wikipedia_()

    elif any(word in converted_lower for word in keywords.news()):
        news()

    elif any(word in converted_lower for word in keywords.report()):
        report()

    elif any(word in converted_lower for word in keywords.robinhood()):
        robinhood()

    elif any(word in converted_lower for word in keywords.repeat()):
        repeater()

    elif any(word in converted_lower for word in keywords.location()):
        location()

    elif any(word in converted_lower for word in keywords.locate()):
        locate(converted)

    elif any(word in converted_lower for word in keywords.gmail()):
        gmail()

    elif any(word in converted_lower for word in keywords.meaning()):
        meaning(converted.split()[-1])

    elif any(word in converted_lower for word in keywords.delete_todo()) and \
            any(word in converted_lower for word in todo_checks):
        delete_todo()

    elif any(word in converted_lower for word in keywords.list_todo()):
        todo()

    elif any(word in converted_lower for word in keywords.add_todo()) and \
            any(word in converted_lower for word in todo_checks):
        add_todo()

    elif any(word in converted_lower for word in keywords.delete_db()):
        delete_db()

    elif any(word in converted_lower for word in keywords.create_db()):
        create_db()

    elif any(word in converted_lower for word in keywords.distance()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        """the loop below differentiates between two places and one place with two words
        eg: New York will be considered as one word and New York and Las Vegas will be considered as two words"""
        check = converted.split()  # str to list
        places = []
        for word in check:
            if word[0].isupper() or '.' in word:  # looks for words that start with uppercase
                try:
                    next_word = check[check.index(word) + 1]  # looks if words after an uppercase word is also one
                    if next_word[0].isupper():
                        places.append(f"{word + ' ' + check[check.index(word) + 1]}")
                    else:
                        if word not in ' '.join(places):
                            places.append(word)
                except IndexError:  # catches exception on lowercase word after an upper case word
                    if word not in ' '.join(places):
                        places.append(word)
        """the condition below assumes two different words as two places but not including two words starting upper case
        right next to each other"""
        if len(places) >= 2:
            start = places[0]
            end = places[1]
        elif len(places) == 1:
            start = None
            end = places[0]
        else:
            start, end = None, None
        distance(start, end)

    elif any(word in converted_lower for word in conversation.form()):
        speaker.say("I am a program, I'm without form.")

    elif any(word in converted_lower for word in keywords.geopy()):
        # tries to look for words starting with an upper case letter
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        # if no words found starting with an upper case letter, fetches word after the keyword 'is' eg: where is Chicago
        if not place:
            keyword = 'is'
            before_keyword, keyword, after_keyword = converted.partition(keyword)
            place = after_keyword.replace(' in', '').strip()
        locate_places(place.strip())

    elif any(word in converted_lower for word in keywords.directions()):
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        place = place.replace('I ', '').strip()
        if place:
            directions(place)
        else:
            speaker.say("I can't take you to anywhere without a location sir!")
            directions(place=None)

    elif any(word in converted_lower for word in keywords.webpage()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        converted = converted.replace(' In', 'in').replace(' Co. Uk', 'co.uk')
        host = (word for word in converted.split() if '.' in word)
        webpage(host)

    elif any(word in converted_lower for word in keywords.kill_alarm()):
        kill_alarm()

    elif any(word in converted_lower for word in keywords.alarm()):
        alarm(converted_lower)

    elif any(word in converted_lower for word in keywords.google_home()):
        google_home()

    elif any(word in converted_lower for word in keywords.jokes()):
        jokes()

    elif any(word in converted_lower for word in keywords.reminder()):
        reminder(converted_lower)

    elif any(word in converted_lower for word in keywords.notes()):
        notes()

    elif any(word in converted_lower for word in keywords.github()):
        auth = HTTPBasicAuth(git_user, git_pass)
        response = get('https://api.github.com/user/repos?type=all&per_page=100', auth=auth).json()
        result, repos, total, forked, private, archived, licensed = [], [], 0, 0, 0, 0, 0
        for i in range(len(response)):
            total += 1
            forked += 1 if response[i]['fork'] else 0
            private += 1 if response[i]['private'] else 0
            archived += 1 if response[i]['archived'] else 0
            licensed += 1 if response[i]['license'] else 0
            repos.append({response[i]['name'].replace('_', ' ').replace('-', ' '): response[i]['clone_url']})
        if 'how many' in converted:
            speaker.say(f'You have {total} repositories sir, out of which {forked} are forked, {private} are private, '
                        f'{licensed} are licensed, and {archived} archived.')
        else:
            [result.append(clone_url) if clone_url not in result and re.search(rf'\b{word}\b', repo.lower()) else None
             for word in converted_lower.split() for item in repos for repo, clone_url in item.items()]
            if result:
                github(target=result)
            else:
                speaker.say("Sorry sir! I did not find that repo.")

    elif any(word in converted_lower for word in keywords.txt_message()):
        number = '-'.join([str(s) for s in re.findall(r'\b\d+\b', converted)])
        send_sms(number)

    elif any(word in converted_lower for word in keywords.google_search()):
        phrase = converted.split('for')[-1] if 'for' in converted else None
        google_search(phrase)

    elif any(word in converted_lower for word in keywords.tv()):
        television(converted)

    elif any(word in converted_lower for word in keywords.apps()):
        apps(converted.split()[-1])

    elif any(word in converted_lower for word in keywords.music()):
        if 'speaker' in converted_lower:
            music(converted)
        else:
            music()

    elif any(word in converted_lower for word in keywords.volume()):
        if 'mute' in converted_lower:
            level = 0
        elif 'max' in converted_lower or 'full' in converted_lower:
            level = 100
        else:
            level = re.findall(r'\b\d+\b', converted)  # gets integers from string as a list
            level = int(level[0]) if level else 50  # converted to int for volume
        volume_controller(level)
        speaker.say(f"{choice(ack)}!")

    elif any(word in converted_lower for word in keywords.face_detection()):
        face_recognition_detection()

    elif any(word in converted_lower for word in keywords.speed_test()):
        speed_test()

    elif any(word in converted_lower for word in keywords.bluetooth()):
        bluetooth(phrase=converted_lower)

    elif any(word in converted_lower for word in keywords.brightness()) and 'lights' not in converted_lower:
        speaker.say(choice(ack))
        if 'set' in converted_lower or re.findall(r'\b\d+\b', converted_lower):
            level = re.findall(r'\b\d+\b', converted_lower)  # gets integers from string as a list
            if not level:
                level = ['50']  # pass as list for brightness, as args must be iterable
            Thread(target=set_brightness, args=level).start()
        elif 'decrease' in converted_lower or 'reduce' in converted_lower or 'lower' in converted_lower or \
                'dark' in converted_lower or 'dim' in converted_lower:
            Thread(target=decrease_brightness).start()
        elif 'increase' in converted_lower or 'bright' in converted_lower or 'max' in converted_lower or \
                'brighten' in converted_lower or 'light up' in converted_lower:
            Thread(target=increase_brightness).start()

    elif any(word in converted_lower for word in keywords.lights()):
        if not vpn_checker().startswith('VPN'):
            lights(converted=converted_lower)

    elif any(word in converted_lower for word in keywords.guard_enable() or keywords.guard_disable()):
        if any(word in converted_lower for word in keywords.guard_enable()):
            logger.info('Enabled Security Mode')
            speaker.say(f"Enabled security mode sir! I will look out for potential threats and keep you posted. "
                        f"Have a nice {part_of_day()}, and enjoy yourself sir!")
            speaker.runAndWait()
            guard()

    elif any(word in converted_lower for word in keywords.flip_a_coin()):
        playsound('indicators/coin.mp3')
        sleep(0.5)
        speaker.say(f"""{choice(['You got', 'It landed on', "It's"])} {choice(['heads', 'tails'])} sir""")

    elif any(word in converted_lower for word in keywords.facts()):
        speaker.say(getFact(False))

    elif any(word in converted_lower for word in keywords.meetings()):
        if os.path.isfile('meetings'):
            meeting_reader()
        else:
            if os.environ.get('called_by_offline'):
                speaker.say("Meetings file is not ready yet. Please try again in a minute or two.")
                return False
            meeting = ThreadPool(processes=1).apply_async(func=meetings)
            speaker.say("Please give me a moment sir! Let me check your calendar.")
            speaker.runAndWait()
            try:
                speaker.say(meeting.get(timeout=60))
            except ThreadTimeoutError:
                logger.error('Unable to read the calendar within 60 seconds.')
                speaker.say("I wasn't able to read your calendar within the set time limit sir!")
            speaker.runAndWait()

    elif any(word in converted_lower for word in keywords.voice_changer()):
        voice_changer(converted)

    elif any(word in converted_lower for word in keywords.system_vitals()):
        system_vitals()

    elif any(word in converted_lower for word in keywords.vpn_server()):
        if vpn_server_check():
            speaker.say('An operation for VPN Server is already in progress sir! Please wait and retry.')
        elif 'start' in converted_lower or 'trigger' in converted_lower or 'initiate' in converted_lower or \
                'enable' in converted_lower or 'spin up' in converted_lower:
            Thread(target=vpn_server, args=['START']).start()
            speaker.say('VPN Server has been initiated sir! Login details will be sent to you shortly.')
        elif 'stop' in converted_lower or 'shut' in converted_lower or 'close' in converted_lower or \
                'disable' in converted_lower:
            Thread(target=vpn_server, args=['STOP']).start()
            speaker.say('VPN Server will be shutdown sir!')
        else:
            speaker.say("I don't understand the request sir! You can ask me to enable or disable the VPN server.")

    elif any(word in converted_lower for word in keywords.personal_cloud()):
        if 'enable' in converted_lower or 'initiate' in converted_lower or 'kick off' in converted_lower or \
                'start' in converted_lower:
            Thread(target=personal_cloud.enable).start()
            speaker.say("Personal Cloud has been triggered sir! I will send the login details to your phone number "
                        "once the server is up and running.")
        elif 'disable' in converted_lower or 'stop' in converted_lower:
            Thread(target=personal_cloud.disable).start()
            speaker.say(choice(ack))
        else:
            speaker.say("I didn't quite get that sir! Please tell me if I should enable or disable your server.")

    elif any(word in converted_lower for word in conversation.greeting()):
        speaker.say('I am spectacular. I hope you are doing fine too.')

    elif any(word in converted_lower for word in conversation.capabilities()):
        speaker.say('There is a lot I can do. For example: I can get you the weather at any location, news around '
                    'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                    'system configuration, tell your investment details, locate your phone, find distance between '
                    'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
                    ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')

    elif any(word in converted_lower for word in conversation.languages()):
        speaker.say("Tricky question!. I'm configured in python, and I can speak English.")

    elif any(word in converted_lower for word in conversation.whats_up()):
        speaker.say("My listeners are up. There is nothing I cannot process. So ask me anything..")

    elif any(word in converted_lower for word in conversation.what()):
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")

    elif any(word in converted_lower for word in conversation.who()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")

    elif any(word in converted_lower for word in conversation.about_me()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")
        speaker.say("I can seamlessly take care of your daily tasks, and also help with most of your work!")

    elif any(word in converted_lower for word in keywords.sleep()):
        if 'pc' in converted_lower or 'computer' in converted_lower or 'imac' in converted_lower or \
                'screen' in converted_lower:
            pc_sleep()
        else:
            speaker.say("Activating sentry mode, enjoy yourself sir!")
            if greet_check:
                greet_check.pop('status')
        return True

    elif any(word in converted_lower for word in keywords.restart()):
        if 'pc' in converted_lower or 'computer' in converted_lower or 'imac' in converted_lower:
            logger.info(f'JARVIS::Restart for {host_info("model")} has been requested.')
            restart(target='PC')
        else:
            logger.info('JARVIS::Self reboot has been requested.')
            if 'quick' in converted_lower or 'fast' in converted_lower:
                restart(quick=True)
            else:
                restart()

    elif any(word in converted_lower for word in keywords.kill()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        raise KeyboardInterrupt

    elif any(word in converted_lower for word in keywords.shutdown()):
        shutdown()

    elif any(word in converted_lower for word in keywords.chatbot()):
        chatter_bot()

    elif should_return:
        return False

    else:
        logger.info(f'Received the unrecognized lookup parameter: {converted}')
        Thread(target=unrecognized_dumper, args=[converted]).start()  # writes to training_data.yaml in a thread
        if alpha(converted):
            if google_maps(converted):
                if google(converted):
                    # if none of the conditions above are met, opens a google search on default browser
                    sys.stdout.write(f"\r{converted}")
                    if google_maps.has_been_called:
                        google_maps.has_been_called = False
                        speaker.say("I have also opened a google search for your request.")
                    else:
                        speaker.say(f"I heard {converted}. Let me look that up.")
                        speaker.runAndWait()
                        speaker.say("I have opened a google search for your request.")
                    search = str(converted).replace(' ', '+')
                    unknown_url = f"https://www.google.com/search?q={search}"
                    web_open(unknown_url)


def unrecognized_dumper(converted: str) -> None:
    """If none of the conditions are met, converted text is written to a yaml file.

    Args:
        converted: Takes the voice recognized statement as argument.
    """
    train_file = {'Uncategorized': converted}
    if os.path.isfile('training_data.yaml'):
        content = open(r'training_data.yaml', 'r').read()
        for key, value in train_file.items():
            if str(value) not in content:  # avoids duplication in yaml file
                dict_file = [{key: [value]}]
                with open(r'training_data.yaml', 'a') as writer:
                    yaml_dump(dict_file, writer)
    else:
        for key, value in train_file.items():
            train_file = [{key: [value]}]
        with open(r'training_data.yaml', 'w') as writer:
            yaml_dump(train_file, writer)


def location_services(device: AppleDevice) -> Union[None, Tuple[str, str, str]]:
    """Gets the current location of an apple device.

    Args:
        device: Passed when locating a particular apple device.

    Returns:
        None or Tuple[str, str, str]:
        - On success, returns ``current latitude``, ``current longitude`` and ``location`` information as a ``dict``.
        - On failure, calls the ``restart()`` or ``terminator()`` function depending on the error.
    """
    try:
        # tries with icloud api to get your device's location for precise location services
        if not device:
            device = device_selector()
        raw_location = device.location()
        # noinspection PyUnresolvedReferences,PyProtectedMember
        if not raw_location and sys._getframe(1).f_code.co_name == 'locate':
            return 'None', 'None', 'None'
        elif not raw_location:
            raise PyiCloudAPIResponseException(reason=f'Unable to retrieve location for {device}')
        else:
            current_lat_ = raw_location['latitude']
            current_lon_ = raw_location['longitude']
    except (PyiCloudAPIResponseException, PyiCloudFailedLoginException):
        # uses latitude and longitude information from your IP's client when unable to connect to icloud
        icloud_error = sys.exc_info()[0]
        logger.error(f'Unable to retrieve location::{icloud_error.__name__}\n{format_exc()}')  # include traceback
        current_lat_ = st.results.client['lat']
        current_lon_ = st.results.client['lon']
        speaker.say("I have trouble accessing the i-cloud API, so I'll be using your I.P address to get your location. "
                    "Please note that this may not be accurate enough for location services.")
        speaker.runAndWait()
    except requests_exceptions.ConnectionError:
        current_lat_, current_lon_ = None, None
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet. Please check your connection settings and retry.")
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                         f"\nTotal runtime: {time_converter(perf_counter())}")
        terminator()

    try:
        # Uses the latitude and longitude information and converts to the required address.
        locator = geo_locator.reverse(f'{current_lat_}, {current_lon_}', language='en')
        return current_lat_, current_lon_, locator.raw['address']
    except (GeocoderUnavailable, GeopyError):
        logger.error('Error retrieving address from latitude and longitude information. Initiating self reboot.')
        speaker.say('Received an error while retrieving your address sir! I think a restart should fix this.')
        restart(quick=True)


def report() -> None:
    """Initiates a list of functions, that I tend to check first thing in the morning."""
    sys.stdout.write("\rStarting today's report")
    report.has_been_called = True
    current_date()
    current_time()
    weather()
    todo()
    gmail()
    robinhood()
    news()
    report.has_been_called = False


def current_date() -> None:
    """Says today's date and adds the current time in speaker queue if report or time_travel function was called."""
    dt_string = datetime.now().strftime("%A, %B")
    date_ = engine().ordinal(datetime.now().strftime("%d"))
    year = datetime.now().strftime("%Y")
    event = celebrate()
    if time_travel.has_been_called:
        dt_string = dt_string + date_
    else:
        dt_string = dt_string + date_ + ', ' + year
    speaker.say(f"It's {dt_string}")
    if event and event == 'Birthday':
        speaker.say(f"It's also your {event} sir!")
    elif event:
        speaker.say(f"It's also {event} sir!")
    if report.has_been_called or time_travel.has_been_called:
        speaker.say('The current time is, ')


def current_time(place: str = None) -> None:
    """Says current time at the requested location if any, else with respect to the current timezone.

    Args:
        place: Takes name of the place as argument.
    """
    if place:
        tf = TimezoneFinder()
        place_tz = geo_locator.geocode(place)
        coordinates = place_tz.latitude, place_tz.longitude
        located = geo_locator.reverse(coordinates, language='en')
        data = located.raw
        address = data['address']
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        time_location = f'{city} {state}'.replace('None', '') if city or state else place
        zone = tf.timezone_at(lat=place_tz.latitude, lng=place_tz.longitude)
        datetime_zone = datetime.now(timezone(zone))
        date_tz = datetime_zone.strftime("%A, %B %d, %Y")
        time_tz = datetime_zone.strftime("%I:%M %p")
        dt_string = datetime.now().strftime("%A, %B %d, %Y")
        if date_tz != dt_string:
            date_tz = datetime_zone.strftime("%A, %B %d")
            speaker.say(f'The current time in {time_location} is {time_tz}, on {date_tz}.')
        else:
            speaker.say(f'The current time in {time_location} is {time_tz}.')
    else:
        c_time = datetime.now().strftime("%I:%M %p")
        speaker.say(f'{c_time}.')


def webpage(target: str or list) -> None:
    """Opens up a webpage using the default browser to the target host.

    If no target received, will ask for user confirmation. If no '.' in the phrase heard, phrase will default to .com.

    Args:
        target: Receives the webpage that has to be opened as an argument.
    """
    host = []
    try:
        [host.append(i) for i in target]
    except TypeError:
        host = None
    if not host:
        speaker.say("Which website shall I open sir?")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            elif '.' in converted and len(list(converted)) == 1:
                _target = (word for word in converted.split() if '.' in word)
                webpage(_target)
            else:
                converted = converted.lower().replace(' ', '')
                target_ = [f"{converted}" if '.' in converted else f"{converted}.com"]
                webpage(target_)
    else:
        for web in host:
            web_url = f"https://{web}"
            web_open(web_url)
        speaker.say(f"I have opened {host}")


def weather(place: str = None) -> None:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    Args:
        place: Takes the location name as an optional argument.
    """
    sys.stdout.write('\rGetting your weather info')
    if place:
        desired_location = geo_locator.geocode(place)
        coordinates = desired_location.latitude, desired_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        data = located.raw
        address = data['address']
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        lat = located.latitude
        lon = located.longitude
    else:
        city, state = location_info['city'], location_info['state']
        lat = current_lat
        lon = current_lon
    api_endpoint = "http://api.openweathermap.org/data/2.5/"
    weather_url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={weather_api}'
    r = urlopen(weather_url)  # sends request to the url created
    response = json_loads(r.read())  # loads the response in a json

    weather_location = f'{city} {state}'.replace('None', '') if city != state else city or state
    temp = response['current']['temp']
    condition = response['current']['weather'][0]['description']
    feels_like = response['current']['feels_like']
    maxi = response['daily'][0]['temp']['max']
    high = int(round(temperature.k2f(maxi), 2))
    mini = response['daily'][0]['temp']['min']
    low = int(round(temperature.k2f(mini), 2))
    temp_f = int(round(temperature.k2f(temp), 2))
    temp_feel_f = int(round(temperature.k2f(feels_like), 2))
    sunrise = datetime.fromtimestamp(response['daily'][0]['sunrise']).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(response['daily'][0]['sunset']).strftime("%I:%M %p")
    if time_travel.has_been_called:
        if 'rain' in condition or 'showers' in condition:
            feeling = 'rainy'
            weather_suggest = 'You might need an umbrella" if you plan to head out.'
        elif temp_feel_f < 40:
            feeling = 'freezing'
            weather_suggest = 'Perhaps" it is time for winter clothing.'
        elif temp_feel_f in range(41, 60):
            feeling = 'cool'
            weather_suggest = 'I think a lighter jacket would suffice" if you plan to head out.'
        elif temp_feel_f in range(61, 75):
            feeling = 'optimal'
            weather_suggest = 'It might be a perfect weather for a hike, or perhaps a walk.'
        elif temp_feel_f in range(75, 85):
            feeling = 'warm'
            weather_suggest = 'It is a perfect weather for some outdoor entertainment.'
        elif temp_feel_f > 85:
            feeling = 'hot'
            weather_suggest = "I would not recommend thick clothes today."
        else:
            feeling, weather_suggest = '', ''
        wind_speed = response['current']['wind_speed']
        if wind_speed > 10:
            output = f'The weather in {city} is a {feeling} {temp_f}°, but due to the current wind conditions ' \
                     f'(which is {wind_speed} miles per hour), it feels like {temp_feel_f}°. {weather_suggest}'
        else:
            output = f'The weather in {city} is a {feeling} {temp_f}°, and it currently feels like {temp_feel_f}°. ' \
                     f'{weather_suggest}'
    elif place or not report.has_been_called:
        output = f'The weather in {weather_location} is {temp_f}°F, with a high of {high}, and a low of {low}. ' \
                 f'It currently feels like {temp_feel_f}°F, and the current condition is {condition}.'
    else:
        output = f'The weather in {weather_location} is {temp_f}°F, with a high of {high}, and a low of {low}. ' \
                 f'It currently feels Like {temp_feel_f}°F, and the current condition is {condition}. ' \
                 f'Sunrise at {sunrise}. Sunset at {sunset}.'
    if 'alerts' in response:
        alerts = response['alerts'][0]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
    else:
        alerts, start_alert, end_alert = None, None, None
    if alerts and start_alert and end_alert:
        output += f' You have a weather alert for {alerts} between {start_alert} and {end_alert}'
    sys.stdout.write(f"\r{output}")
    speaker.say(output)


def weather_condition(msg: str, place: str = None) -> None:
    """Weather report when phrase has conditions like tomorrow, day after, next week and specific part of the day etc.

    Notes:
        - ``weather_condition()`` uses conditional blocks to fetch keywords and determine the output.

    Args:
        place: Name of place where the weather information is needed.
        msg: Takes the voice recognized statement as argument.
    """
    if place:
        desired_location = geo_locator.geocode(place)
        coordinates = desired_location.latitude, desired_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        data = located.raw
        address = data['address']
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        lat = located.latitude
        lon = located.longitude
    else:
        city, state, = location_info['city'], location_info['state']
        lat = current_lat
        lon = current_lon
    api_endpoint = "http://api.openweathermap.org/data/2.5/"
    weather_url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={weather_api}'
    r = urlopen(weather_url)  # sends request to the url created
    response = json_loads(r.read())  # loads the response in a json
    weather_location = f'{city} {state}' if city and state else place
    if 'tonight' in msg:
        key = 0
        tell = 'tonight'
    elif 'day after' in msg:
        key = 2
        tell = 'day after tomorrow '
    elif 'tomorrow' in msg:
        key = 1
        tell = 'tomorrow '
    elif 'next week' in msg:
        key = -1
        next_week = datetime.fromtimestamp(response['daily'][-1]['dt']).strftime("%A, %B %d")
        tell = f"on {' '.join(next_week.split()[0:-1])} {engine().ordinal(next_week.split()[-1])}"
    else:
        key = 0
        tell = 'today '
    if 'morning' in msg:
        when = 'morn'
        tell += 'morning'
    elif 'evening' in msg:
        when = 'eve'
        tell += 'evening'
    elif 'tonight' in msg:
        when = 'night'
    elif 'night' in msg:
        when = 'night'
        tell += 'night'
    else:
        when = 'day'
        tell += ''
    if 'alerts' in response:
        alerts = response['alerts'][0]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
    else:
        alerts, start_alert, end_alert = None, None, None
    temp = response['daily'][key]['temp'][when]
    feels_like = response['daily'][key]['feels_like'][when]
    condition = response['daily'][key]['weather'][0]['description']
    sunrise = response['daily'][key]['sunrise']
    sunset = response['daily'][key]['sunset']
    maxi = response['daily'][key]['temp']['max']
    mini = response['daily'][1]['temp']['min']
    high = int(round(temperature.k2f(maxi), 2))
    low = int(round(temperature.k2f(mini), 2))
    temp_f = int(round(temperature.k2f(temp), 2))
    temp_feel_f = int(round(temperature.k2f(feels_like), 2))
    sunrise = datetime.fromtimestamp(sunrise).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(sunset).strftime("%I:%M %p")
    output = f'The weather in {weather_location} {tell} would be {temp_f}°F, with a high ' \
             f'of {high}, and a low of {low}. But due to {condition} it will fee like it is {temp_feel_f}°F. ' \
             f'Sunrise at {sunrise}. Sunset at {sunset}. '
    if alerts and start_alert and end_alert:
        output += f'There is a weather alert for {alerts} between {start_alert} and {end_alert}'
    sys.stdout.write(f'\r{output}')
    speaker.say(output)


def system_info() -> None:
    """Gets the system configuration."""
    total, used, free = disk_usage("/")
    total = size_converter(total)
    used = size_converter(used)
    free = size_converter(free)
    ram = size_converter(virtual_memory().total).replace('.0', '')
    ram_used = size_converter(virtual_memory().percent).replace(' B', ' %')
    physical = cpu_count(logical=False)
    logical = cpu_count(logical=True)
    o_system = platform().split('.')[0]
    sys_config = f"You're running {o_system}, with {physical} physical cores and {logical} logical cores. " \
                 f"Your physical drive capacity is {total}. You have used up {used} of space. Your free space is " \
                 f"{free}. Your RAM capacity is {ram}. You are currently utilizing {ram_used} of your memory."
    sys.stdout.write(f'\r{sys_config}')
    speaker.say(sys_config)


def wikipedia_() -> None:
    """Gets any information from wikipedia using it's API."""
    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
    keyword = listener(timeout=3, phrase_limit=5)
    if keyword != 'SR_ERROR':
        if any(word in keyword.lower() for word in keywords.exit()):
            return
        else:
            sys.stdout.write(f'\rGetting your info from Wikipedia API for {keyword}')
            try:
                result = summary(keyword)
            except wiki_exceptions.DisambiguationError as e:  # checks for the right keyword in case of 1+ matches
                sys.stdout.write(f'\r{e}')
                speaker.say('Your keyword has multiple results sir. Please pick any one displayed on your screen.')
                speaker.runAndWait()
                keyword1 = listener(timeout=3, phrase_limit=5)
                result = summary(keyword1) if keyword1 != 'SR_ERROR' else None
            except wiki_exceptions.PageError:
                speaker.say(f"I'm sorry sir! I didn't get a response for the phrase: {keyword}. Try again!")
                result = None
                wikipedia_()
            # stops with two sentences before reading whole passage
            formatted = '. '.join(result.split('. ')[0:2]) + '.'
            speaker.say(formatted)
            speaker.say("Do you want me to continue sir?")  # gets confirmation to read the whole passage
            speaker.runAndWait()
            response = listener(timeout=3, phrase_limit=3)
            if response != 'SR_ERROR':
                if any(word in response.lower() for word in keywords.ok()):
                    speaker.say('. '.join(result.split('. ')[3:-1]))
            else:
                sys.stdout.write("\r")
                speaker.say("I'm sorry sir, I didn't get your response.")


def news(news_source: str = 'fox') -> None:
    """Says news around the user's location.

    Args:
        news_source: Source from where the news has to be fetched. Defaults to ``fox``.
    """
    sys.stdout.write(f'\rGetting news from {news_source} news.')
    news_client = NewsApiClient(api_key=news_api)
    try:
        all_articles = news_client.get_top_headlines(sources=f'{news_source}-news')
    except newsapi_exception.NewsAPIException:
        all_articles = None
        speaker.say("I wasn't able to get the news sir! I think the News API broke, you may try after sometime.")

    if all_articles:
        speaker.say("News around you!")
        for article in all_articles['articles']:
            speaker.say(article['title'])
        if os.environ.get('called_by_offline'):
            return
        speaker.say("That's the end of news around you.")

    if report.has_been_called or time_travel.has_been_called:
        speaker.runAndWait()


def apps(keyword: str or None) -> None:
    """Launches the requested application and if Jarvis is unable to find the app, asks for the app name from the user.

    Args:
        keyword: Gets app name as an argument to launch the application.
    """
    offline = os.environ.get('called_by_offline')
    ignore = ['app', 'application']
    if not keyword or keyword in ignore:
        speaker.say("Which app shall I open sir?")
        if offline:
            return
        speaker.runAndWait()
        keyword = listener(timeout=3, phrase_limit=4)
        if keyword != 'SR_ERROR':
            if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                return
        else:
            speaker.say("I didn't quite get that. Try again.")
            apps(None)

    v = (check_output("ls /Applications/", shell=True))
    apps_ = (v.decode('utf-8').split('\n'))

    app_check = False
    for app in apps_:
        if re.search(keyword, app, flags=re.IGNORECASE) is not None:
            keyword = app
            app_check = True
            break

    if not app_check:
        speaker.say(f"I did not find the app {keyword}. Try again.")
        if offline:
            return
        apps(None)
    else:
        app_status = os.system(f"open /Applications/'{keyword}' > /dev/null 2>&1")
        keyword = keyword.replace('.app', '')
        if app_status == 256:
            speaker.say(f"I'm sorry sir! I wasn't able to launch {keyword}. "
                        f"You might need to check its permissions.")
        else:
            speaker.say(f"I have opened {keyword}")


def robinhood() -> None:
    """Gets investment details from robinhood API."""
    sys.stdout.write('\rGetting your investment details.')
    rh = Robinhood()
    rh.login(username=robinhood_user, password=robinhood_pass, qr_code=robinhood_qr)
    raw_result = rh.positions()
    result = raw_result['results']
    stock_value = RobinhoodGatherer().watcher(rh, result)
    sys.stdout.write(f'\r{stock_value}')
    speaker.say(stock_value)
    sys.stdout.write("\r")


def repeater() -> None:
    """Repeats whatever is heard."""
    speaker.say("Please tell me what to repeat.")
    speaker.runAndWait()
    keyword = listener(timeout=3, phrase_limit=10)
    if keyword != 'SR_ERROR':
        sys.stdout.write(f'\r{keyword}')
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            pass
        else:
            speaker.say(f"I heard {keyword}")


def chatter_bot() -> None:
    """Initiates chatter bot."""
    file1 = 'db.sqlite3'
    file2 = f"/Users/{os.environ.get('USER')}/nltk_data"
    if os.path.isfile(file1) and os.path.isdir(file2):
        bot = ChatBot("Chatterbot", storage_adapter="chatterbot.storage.SQLStorageAdapter")
    else:
        speaker.say('Give me a moment while I train the module.')
        speaker.runAndWait()
        bot = ChatBot("Chatterbot", storage_adapter="chatterbot.storage.SQLStorageAdapter")
        trainer = ChatterBotCorpusTrainer(bot)
        trainer.train("chatterbot.corpus.english")
        speaker.say('The chat-bot is ready. You may start a conversation now.')
        speaker.runAndWait()
    keyword = listener(timeout=3, phrase_limit=5)
    if keyword != 'SR_ERROR':
        if any(word in keyword.lower() for word in keywords.exit()):
            speaker.say('Let me remove the training modules.')
            os.system('rm db* > /dev/null 2>&1')
            os.system(f'rm -rf {file2}')
        else:
            response = bot.get_response(keyword)
            if response == 'What is AI?':
                speaker.say(f'The chat bot is unable to get a response for the phrase, {keyword}. Try something else.')
            else:
                speaker.say(f'{response}')
            speaker.runAndWait()
            chatter_bot()


def device_selector(converted: str = None) -> AppleDevice:
    """Selects a device using the received input string.

    See Also:
        - Opens an html table with the index value and name of device.
        - When chosen an index value, the device name will be returned.

    Args:
        converted: Takes the voice recognized statement as argument.

    Returns:
        AppleDevice:
        Returns the selected device from the class ``AppleDevice``
    """
    icloud_api = PyiCloudService(icloud_user, icloud_pass)
    devices = [device for device in icloud_api.devices]
    target_device = None
    if converted:
        # todo: remove this and automate the work some how, consider loading a mapping file upon start up
        nth = {"first or 1st or number one or 1": 1, "second or 2nd or two or 2": 2, "third or 3rd or three or 3": 3,
               "fourth or 4th or four or 4": 4, "fifth or 4th or five or 5": 5, "sixth or 6th or six or 6": 6,
               "seventh or 7th or seven or 7": 7, "eighth or 8th or eight or 8": 8, "ninth or 9th or nine or 9": 9,
               "tenth or 10th or ten or 10": 10, "eleventh or 11th or eleven or 11": 11,
               "twelfth or 12th or twelve or 12": 12}
        inject_data = ''
        for index, device in enumerate(devices):
            inject_data += f"""<tr>\n\t<td>{index + 1}</th>\n\t<td>{device}</th>\n</tr>\n"""
        inject_data += """</table>\n</body>\n</html>"""
        styling = """<head>\n<style>table {\n\tfont-family: arial, sans-serif;\n\tborder-collapse: collapse;
                width: 100%;\n}\n\ntd, th {\n\tborder: 1px solid #dddddd;\n\ttext-align: left;\n\tpadding: 8px;\n}\n\n
                tr:nth-child(even) {\n\tbackground-color: #dddddd;\n}\n</style>\n</head>"""
        html_data = f"""<!DOCTYPE html>\n<html>\n{styling}\n<body>\n<h2>Choose an index value:</h2>\n<table>\n\t
                <tr>\n\t<th>Index</th>\n\t<th>Device Info</th>\n\t</tr>\n\t{inject_data}"""
        devices_file = 'devices.html'
        with open(devices_file, 'w') as file:
            file.write(html_data)
            file.close()
        web_open('file:///' + os.getcwd() + '/' + devices_file)
        speaker.say('Choose an option from your screen sir!')
        speaker.runAndWait()
        converted = listener(timeout=5, phrase_limit=5)
        os.remove(devices_file) if os.path.isfile(devices_file) else None
        if converted != 'SR_ERROR':
            for key, value in nth.items():
                for k in key.split(' or '):
                    if k in converted:
                        target_device = icloud_api.devices[value - 1]  # index in html and nth dict are incremented by 1
    else:
        target_device = [device for device in devices if device.get('name') == gethostname() or
                         gethostname() == device.get('name') + '.local'][0]
    return target_device if target_device else icloud_api.iphone


def location() -> None:
    """Gets the user's current location."""
    city, state, country = location_info['city'], location_info['state'], location_info['country']
    speaker.say(f"You're at {city} {state}, in {country}")


def locate(converted: str, no_repeat: bool = False) -> None:
    """Locates an apple device using icloud api for python.

    Args:
        no_repeat: A place holder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
        converted: Takes the voice recognized statement as argument and extracts device name from it.
    """
    target_device = device_selector(converted)
    sys.stdout.write(f"\rLocating your {target_device}")
    if no_repeat:
        speaker.say("Would you like to get the location details?")
    else:
        target_device.play_sound()
        before_keyword, keyword, after_keyword = str(target_device).partition(':')  # partitions the hostname info
        speaker.say(f"Your {before_keyword} should be ringing now sir!")
        speaker.runAndWait()
        speaker.say("Would you like to get the location details?")
    speaker.runAndWait()
    phrase = listener(timeout=3, phrase_limit=3)
    if phrase == 'SR_ERROR':
        if no_repeat:
            return
        speaker.say("I didn't quite get that. Try again.")
        locate(converted=converted, no_repeat=True)
    else:
        if any(word in phrase.lower() for word in keywords.ok()):
            ignore_lat, ignore_lon, location_info_ = location_services(target_device)
            lookup = str(target_device).split(':')[0].strip()
            if location_info_ == 'None':
                speaker.say(f"I wasn't able to locate your {lookup} sir! It is probably offline.")
            else:
                post_code = '"'.join(list(location_info_['postcode'].split('-')[0]))
                iphone_location = f"Your {lookup} is near {location_info_['road']}, {location_info_['city']} " \
                                  f"{location_info_['state']}. Zipcode: {post_code}, {location_info_['country']}"
                speaker.say(iphone_location)
                stat = target_device.status()
                bat_percent = f"Battery: {round(stat['batteryLevel'] * 100)} %, " if stat['batteryLevel'] else ''
                device_model = stat['deviceDisplayName']
                phone_name = stat['name']
                speaker.say(f"Some more details. {bat_percent} Name: {phone_name}, Model: {device_model}")
            speaker.say("I can also enable lost mode. Would you like to do it?")
            speaker.runAndWait()
            phrase = listener(timeout=3, phrase_limit=3)
            if any(word in phrase.lower() for word in keywords.ok()):
                message = 'Return my phone immediately.'
                target_device.lost_device(number=icloud_recovery, text=message)
                speaker.say("I've enabled lost mode on your phone.")
            else:
                speaker.say("No action taken sir!")


def music(device: str = None) -> None:
    """Scans music directory in the user profile for ``.mp3`` files and plays using default player.

    Args:
        device: Takes device name as argument.
    """
    sys.stdout.write("\rScanning music files...")
    get_all_files = (os.path.join(root, f) for root, _, files in os.walk(f"{home}/Music") for f in files)
    if music_files := [file for file in get_all_files if os.path.splitext(file)[1] == '.mp3']:
        chosen = choice(music_files)
        if device:
            google_home(device, chosen)
        else:
            call(["open", chosen])
            sys.stdout.write("\r")
            speaker.say("Enjoy your music sir!")
    else:
        speaker.say('No music files were found sir!')


def gmail() -> None:
    """Reads unread emails from the gmail account for which the credentials are stored in env variables."""
    sys.stdout.write("\rFetching unread emails..")
    offline = os.environ.get('called_by_offline')
    try:
        mail = IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(gmail_user, gmail_pass)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError as TimeOut:
        logger.error(TimeOut)
        speaker.say("I wasn't able to check your emails sir. You might need to check to logs.")
        return

    return_code, messages = mail.search(None, 'UNSEEN')  # looks for unread emails
    if return_code == 'OK':
        n = len(messages[0].split())
    else:
        speaker.say("I'm unable access your email sir.")
        return
    if n == 0:
        speaker.say("You don't have any emails to catch up sir")
        return
    else:
        if not offline:
            speaker.say(f'You have {n} unread emails sir. Do you want me to check it?')
            speaker.runAndWait()
        response = listener(timeout=3, phrase_limit=3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.ok()):
                for nm in messages[0].split():
                    ignore, mail_data = mail.fetch(nm, '(RFC822)')
                    for response_part in mail_data:
                        if isinstance(response_part, tuple):  # checks for type(response_part)
                            original_email = message_from_bytes(response_part[1])
                            sender = make_header(decode_header((original_email['From']).split(' <')[0]))
                            subject = make_header(decode_header(original_email['Subject'])) \
                                if original_email['Subject'] else None
                            if subject:
                                subject = ''.join(str(subject).splitlines())
                            raw_receive = (original_email['Received'].split(';')[-1]).strip()
                            if '(PDT)' in raw_receive:
                                datetime_obj = datetime.strptime(raw_receive, "%a, %d %b %Y %H:%M:%S -0700 (PDT)") \
                                               + timedelta(hours=2)
                            elif '(PST)' in raw_receive:
                                datetime_obj = datetime.strptime(raw_receive, "%a, %d %b %Y %H:%M:%S -0800 (PST)") \
                                               + timedelta(hours=2)
                            else:
                                sys.stdout.write(f'\rEmail from {sender} has a weird time stamp. Please check.')
                                datetime_obj = datetime.now()  # sets to current date if PST or PDT are not found
                            received_date = datetime_obj.strftime("%Y-%m-%d")
                            current_date_ = datetime.today().date()
                            yesterday = current_date_ - timedelta(days=1)
                            # replaces current date with today or yesterday
                            if received_date == str(current_date_):
                                receive = datetime_obj.strftime("Today, at %I:%M %p")
                            elif received_date == str(yesterday):
                                receive = datetime_obj.strftime("Yesterday, at %I:%M %p")
                            else:
                                receive = datetime_obj.strftime("on %A, %B %d, at %I:%M %p")
                            sys.stdout.write(f'\rReceived:{receive.strip()}\tSender: {str(sender).strip()}\tSubject: '
                                             f'{subject.strip()}')
                            speaker.say(f"You have an email from, {sender}, with subject, {subject}, {receive}")
                            speaker.runAndWait() if not offline else None


def meaning(keyword: str or None) -> None:
    """Gets meaning for a word skimmed from the user statement using PyDictionary.

    Args:
        keyword: Takes a keyword as argument for which the meaning was requested.
    """
    offline = os.environ.get('called_by_offline')
    dictionary = PyDictionary()
    if keyword == 'word':
        keyword = None
    if keyword is None:
        speaker.say("Please tell a keyword.")
        speaker.runAndWait()
        response = listener(timeout=3, phrase_limit=3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.exit()):
                return
            else:
                meaning(keyword=response)
    else:
        definition = dictionary.meaning(keyword)
        if definition:
            n = 0
            vowel = ['A', 'E', 'I', 'O', 'U']
            for key, value in definition.items():
                insert = 'an' if key[0] in vowel else 'a'
                repeat = 'also' if n != 0 else ''
                n += 1
                mean = ', '.join(value[0:2])
                speaker.say(f'{keyword} is {repeat} {insert} {key}, which means {mean}.')
            if offline:
                return
            speaker.say(f'Do you wanna know how {keyword} is spelled?')
            speaker.runAndWait()
            response = listener(timeout=3, phrase_limit=3)
            if any(word in response.lower() for word in keywords.ok()):
                for letter in list(keyword.lower()):
                    speaker.say(letter)
                speaker.runAndWait()
        elif offline:
            return
        else:
            speaker.say("Keyword should be a single word sir! Try again")
            meaning(None)
    return


def create_db() -> None:
    """Creates a database for to-do list by calling the ``create_db`` function in ``database`` module."""
    speaker.say(database.create_db())
    if todo.has_been_called:
        todo.has_been_called = False
        todo()
    elif add_todo.has_been_called:
        add_todo.has_been_called = False
        add_todo()


def todo(no_repeat: bool = False) -> None:
    """Says the item and category stored in the to-do list.

    Args:
        no_repeat: A place holder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
    """
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name) and (time_travel.has_been_called or report.has_been_called):
        pass
    elif not os.path.isfile(file_name):
        if os.environ.get('called_by_offline'):
            speaker.say("Your don't have any items in your to-do list sir!")
            return
        if no_repeat:
            speaker.say("Would you like to create a database for your to-do list?")
        else:
            speaker.say("You don't have a database created for your to-do list sir. Would you like to spin up one now?")
        speaker.runAndWait()
        key = listener(timeout=3, phrase_limit=3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok()):
                todo.has_been_called = True
                sys.stdout.write("\r")
                create_db()
            else:
                return
        else:
            if no_repeat:
                return
            speaker.say("I didn't quite get that. Try again.")
            todo(no_repeat=True)
    else:
        sys.stdout.write("\rQuerying DB for to-do list..")
        result = {}
        for category, item in database.downloader():
            # condition below makes sure one category can have multiple items without repeating category for each item
            if category not in result:
                result.update({category: item})  # creates dict for category and item if category is not found in result
            else:
                result[category] = result[category] + ', ' + item  # updates category if already found in result
        sys.stdout.write("\r")
        if result:
            if os.environ.get('called_by_offline'):
                speaker.say(json_dumps(result))
                return
            speaker.say('Your to-do items are')
            for category, item in result.items():  # browses dictionary and stores result in response and says it
                response = f"{item}, in {category} category."
                speaker.say(response)
                sys.stdout.write(f"\r{response}")
        elif report.has_been_called and not time_travel.has_been_called:
            speaker.say("You don't have any tasks in your to-do list sir.")
        elif time_travel.has_been_called:
            pass
        else:
            speaker.say("You don't have any tasks in your to-do list sir.")

    if report.has_been_called or time_travel.has_been_called:
        speaker.runAndWait()


def add_todo() -> None:
    """Adds new items to the to-do list."""
    sys.stdout.write("\rLooking for to-do database..")
    # if database file is not found calls create_db()
    if not os.path.isfile(file_name):
        sys.stdout.write("\r")
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
        key = listener(timeout=3, phrase_limit=3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok()):
                add_todo.has_been_called = True
                sys.stdout.write("\r")
                create_db()
            else:
                return
    speaker.say("What's your plan sir?")
    speaker.runAndWait()
    item = listener(timeout=3, phrase_limit=5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            speaker.say('Your to-do list has been left intact sir.')
        else:
            sys.stdout.write(f"\rItem: {item}")
            speaker.say(f"I heard {item}. Which category you want me to add it to?")
            speaker.runAndWait()
            category = listener(timeout=3, phrase_limit=3)
            if category == 'SR_ERROR':
                category = 'Unknown'
            if 'exit' in category or 'quit' in category or 'Xzibit' in category:
                speaker.say('Your to-do list has been left intact sir.')
            else:
                sys.stdout.write(f"\rCategory: {category}")
                # passes the category and item to uploader() in helper_functions/database.py which updates the database
                response = database.uploader(category, item)
                speaker.say(response)
                speaker.say("Do you want to add anything else to your to-do list?")
                speaker.runAndWait()
                category_continue = listener(timeout=3, phrase_limit=3)
                if any(word in category_continue.lower() for word in keywords.ok()):
                    add_todo()
                else:
                    speaker.say('Alright')


def delete_todo() -> None:
    """Deletes items from an existing to-do list."""
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name):
        speaker.say("You don't have a database created for your to-do list sir.")
        return
    speaker.say("Which one should I remove sir?")
    speaker.runAndWait()
    item = listener(timeout=3, phrase_limit=5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            return
        response = database.deleter(keyword=item.lower())
        # if the return message from database starts with 'Looks' it means that the item wasn't matched for deletion
        sys.stdout.write(f'\r{response}')
        if response.startswith('Looks'):
            speaker.say(response)
            speaker.runAndWait()
            delete_todo()
        else:
            speaker.say(response)


def delete_db() -> None:
    """Deletes the ``tasks.db`` database file after getting confirmation."""
    if not os.path.isfile(file_name):
        speaker.say('I did not find any database sir.')
        return
    else:
        speaker.say(f'{choice(confirmation)} delete your database?')
        speaker.runAndWait()
        response = listener(timeout=3, phrase_limit=3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.ok()):
                os.remove(file_name)
                speaker.say("I've removed your database sir.")
            else:
                speaker.say("Your database has been left intact sir.")
            return


def distance(starting_point: str = None, destination: str = None) -> None:
    """Calculates distance between two locations.

    Notes:
        - If starting point is None, Jarvis takes the current location as starting point.
        - If destination is None, Jarvis will ask for a destination from the user.

    Args:
        starting_point: Takes the starting place name as an optional argument.
        destination: Takes the destination place name as optional argument.
    """
    if not destination:
        speaker.say("Destination please?")
        if os.environ.get('called_by_offline'):
            return
        speaker.runAndWait()
        destination = listener(timeout=3, phrase_limit=4)
        if destination != 'SR_ERROR':
            if len(destination.split()) > 2:
                speaker.say("I asked for a destination sir, not a sentence. Try again.")
                distance()
            if 'exit' in destination or 'quit' in destination or 'Xzibit' in destination:
                return

    if starting_point:
        # if starting_point is received gets latitude and longitude of that location
        desired_start = geo_locator.geocode(starting_point)
        sys.stdout.write(f"\r{desired_start.address} **")
        start = desired_start.latitude, desired_start.longitude
        start_check = None
    else:
        # else gets latitude and longitude information of current location
        start = (current_lat, current_lon)
        start_check = 'My Location'
    sys.stdout.write("::TO::") if starting_point else sys.stdout.write("\r::TO::")
    desired_location = geo_locator.geocode(destination)
    if desired_location:
        end = desired_location.latitude, desired_location.longitude
    else:
        end = destination[0], destination[1]
    miles = round(geodesic(start, end).miles)  # calculates miles from starting point to destination
    sys.stdout.write(f"** {desired_location.address} - {miles}")
    if directions.has_been_called:
        # calculates drive time using d = s/t and distance calculation is only if location is same country
        directions.has_been_called = False
        avg_speed = 60
        t_taken = miles / avg_speed
        if miles < avg_speed:
            drive_time = int(t_taken * 60)
            speaker.say(f"It might take you about {drive_time} minutes to get there sir!")
        else:
            drive_time = ceil(t_taken)
            if drive_time == 1:
                speaker.say(f"It might take you about {drive_time} hour to get there sir!")
            else:
                speaker.say(f"It might take you about {drive_time} hours to get there sir!")
    elif start_check:
        speaker.say(f"Sir! You're {miles} miles away from {destination}.")
        if not locate_places.has_been_called:  # promotes using locate_places() function
            speaker.say(f"You may also ask where is {destination}")
    else:
        speaker.say(f"{starting_point} is {miles} miles away from {destination}.")
    return


def locate_places(place: str or None) -> None:
    """Gets location details of a place.

    Args:
        place: Takes a place name as argument.
    """
    offline = os.environ.get('called_by_offline')
    if not place:
        if offline:
            speaker.say('I need a location to get you the details sir!')
            return
        speaker.say("Tell me the name of a place!")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            for word in converted.split():
                if word[0].isupper():
                    place += word + ' '
                elif '.' in word:
                    place += word + ' '
            if not place:
                keyword = 'is'
                before_keyword, keyword, after_keyword = converted.partition(keyword)
                place = after_keyword.replace(' in', '').strip()
    try:
        destination_location = geo_locator.geocode(place)
        coordinates = destination_location.latitude, destination_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        data = located.raw
        address = data['address']
        county = address['county'] if 'county' in address else None
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        country = address['country'] if 'country' in address else None
        if place in country:
            speaker.say(f"{place} is a country")
        elif place in (city or county):
            speaker.say(f"{place} is in {state}" if country == location_info['country'] else f"{place} is in "
                                                                                             f"{state} in {country}")
        elif place in state:
            speaker.say(f"{place} is a state in {country}")
        elif (city or county) and state and country:
            speaker.say(f"{place} is in {city or county}, {state}" if country == location_info['country']
                        else f"{place} is in {city or county}, {state}, in {country}")
        if offline:
            return
        locate_places.has_been_called = True
    except (TypeError, AttributeError):
        speaker.say(f"{place} is not a real place on Earth sir! Try again.")
        if offline:
            return
        locate_places(place=None)
    distance(starting_point=None, destination=place)


def directions(place: str or None) -> None:
    """Opens google maps for a route between starting and destination.

    Uses reverse geocoding to calculate latitude and longitude for both start and destination.

    Args:
        place: Takes a place name as argument.
    """
    if not place:
        speaker.say("You might want to give a location.")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            place = ''
            for word in converted.split():
                if word[0].isupper():
                    place += word + ' '
                elif '.' in word:
                    place += word + ' '
            place = place.replace('I ', '').strip()
            if not place:
                speaker.say("I can't take you to anywhere without a location sir!")
                directions(place=None)
            if 'exit' in place or 'quit' in place or 'Xzibit' in place:
                return
    destination_location = geo_locator.geocode(place)
    coordinates = destination_location.latitude, destination_location.longitude
    located = geo_locator.reverse(coordinates, language='en')
    data = located.raw
    address = data['address']
    end_country = address['country'] if 'country' in address else None
    end = f"{located.latitude},{located.longitude}"

    start_country = location_info['country']
    start = current_lat, current_lon
    maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
    web_open(maps_url)
    speaker.say("Directions on your screen sir!")
    if start_country and end_country:
        if re.match(start_country, end_country, flags=re.IGNORECASE):
            directions.has_been_called = True
            distance(starting_point=None, destination=place)
        else:
            speaker.say("You might need a flight to get there!")
    return


def alarm(msg: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        msg: Takes the voice recognized statement as argument and extracts time from it.
    """
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', msg) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', msg) or re.findall(r'([0-9]+\s?(?:am|pm:?))', msg)
    if extracted_time:
        extracted_time = extracted_time[0]
        am_pm = extracted_time.split()[-1]
        am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
        alarm_time = extracted_time.split()[0]
        if ":" in extracted_time:
            hour = int(alarm_time.split(":")[0])
            minute = int(alarm_time.split(":")[-1])
        else:
            hour = int(alarm_time.split()[0])
            minute = 0
        # makes sure hour and minutes are two digits
        hour, minute = f"{hour:02}", f"{minute:02}"
        am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
        if int(hour) <= 12 and int(minute) <= 59:
            open(f'alarm/{hour}_{minute}_{am_pm}.lock', 'a')
            Alarm(hour, minute, am_pm).start()
            if 'wake' in msg.lower().strip():
                speaker.say(f"{choice(ack)}! I will wake you up at {hour}:{minute} {am_pm}.")
            else:
                speaker.say(f"{choice(ack)}! Alarm has been set for {hour}:{minute} {am_pm}.")
            sys.stdout.write(f"\rAlarm has been set for {hour}:{minute} {am_pm} sir!")
        else:
            speaker.say(f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                        f"I don't think a time like that exists on Earth.")
    else:
        speaker.say('Please tell me a time sir!')
        if os.environ.get('called_by_offline'):
            return
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            else:
                alarm(converted)


def kill_alarm() -> None:
    """Removes lock file to stop the alarm which rings only when the certain lock file is present.

    Notes:
        - ``alarm_state`` is the list of lock files currently present.
    """
    alarm_state = []
    [alarm_state.append(file) for file in os.listdir('alarm') if file != '.keep']
    alarm_state.remove('.DS_Store') if '.DS_Store' in alarm_state else None
    if not alarm_state:
        speaker.say("You have no alarms set sir!")
    elif len(alarm_state) == 1:
        hour, minute, am_pm = alarm_state[0][0:2], alarm_state[0][3:5], alarm_state[0][6:8]
        os.remove(f"alarm/{alarm_state[0]}")
        speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
    else:
        sys.stdout.write(f"\r{', '.join(alarm_state).replace('.lock', '')}")
        speaker.say("Please let me know which alarm you want to remove. Current alarms on your screen sir!")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            alarm_time = converted.split()[0]
            am_pm = converted.split()[-1]
            if ":" in converted:
                hour = int(alarm_time.split(":")[0])
                minute = int(alarm_time.split(":")[-1])
            else:
                hour = int(alarm_time.split()[0])
                minute = 0
            hour, minute = f"{hour:02}", f"{minute:02}"
            am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
            if os.path.exists(f'alarm/{hour}_{minute}_{am_pm}.lock'):
                os.remove(f"alarm/{hour}_{minute}_{am_pm}.lock")
                speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
            else:
                speaker.say(f"I wasn't able to find an alarm at {hour}:{minute} {am_pm}. Try again.")
                kill_alarm()


def comma_separator(list_: list) -> str:
    """Separates commas using simple ``.join()`` function and analysis based on length of the list taken as argument.

    Args:
        list_: Takes a list of elements as an argument.

    Returns:
        str:
        Comma separated list of elements.
    """
    return ', and '.join([', '.join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_)


def google_home(device: str = None, file: str = None) -> None:
    """Uses ``socket lib`` to extract ip address and scan ip range for google home devices.

    Notes:
        - Can also play music on multiple devices at once.

    See Also:
        - Changes made to google-home-push module:
            1. Modified the way local IP is received: https://github.com/deblockt/google-home-push/pull/7
            2. Instead of commenting/removing the final print statement on: site-packages/googlehomepush/__init__.py

            - I have used ``sys.stdout = open(os.devnull, 'w')`` to suppress any print statements.
            - To enable this again at a later time use ``sys.stdout = sys.__stdout__``

        - When music is played and immediately stopped/tasked the google home device, it is most likely to except.
        - Broken Pipe error. This usually happens when a socket is written after it is fully closed.
        - This error occurs when one end of the connection tries sending data while the other has closed the connection.
        - This can simply be ignored or handled adding the code below in socket module (NOT PREFERRED).

        .. code-block:: python

            except IOError as error:
                import errno
                if error.errno != errno.EPIPE:
                    sys.stdout.write(error)

    Args:
        device: Name of the google home device on which the music has to be played.
        file: Scanned audio file to be played.
    """
    network_id = vpn_checker()
    if network_id.startswith('VPN'):
        return

    if not os.environ.get('called_by_offline'):
        speaker.say('Scanning your IP range for Google Home devices sir!')
        sys.stdout.write('\rScanning your IP range for Google Home devices..')
        speaker.runAndWait()
    network_id = '.'.join(network_id.split('.')[0:3])

    def ip_scan(host_id: int) -> Tuple[str, str]:
        """Scans the IP range using the received args as host id in an IP address.

        Args:
            host_id: Host ID passed in a multi-threaded fashion to scan for google home devices in IP range.

        Returns:
            Tuple(str, str):
            Device name and it's IP address.
        """
        try:
            device_info = GoogleHome(host=f"{network_id}.{host_id}").cc
            device_info = str(device_info)
            device_name = device_info.split("'")[3]
            device_ip = device_info.split("'")[1]
            # port = sample.split("'")[2].split()[1].replace(',', '')
            return device_name, device_ip
        except ChromecastConnectionError:
            pass

    # scan time after MultiThread: < 10 seconds (usual bs: 3 minutes)
    devices = []
    with ThreadPoolExecutor(max_workers=100) as executor:  # max workers set to 5K (to scan 255 IPs) for less wait time
        for info in executor.map(ip_scan, range(1, 101)):  # scans host IDs 1 to 255 (eg: 192.168.1.1 to 192.168.1.255)
            devices.append(info)  # this includes all the NoneType values returned by unassigned host IDs
    devices = dict([i for i in devices if i])  # removes None values and converts list to dictionary of name and ip pair

    if not device or not file:
        sys.stdout.write("\r")
        speaker.say(f"You have {len(devices)} devices in your IP range sir! {comma_separator(list(devices.keys()))}. "
                    f"You can choose one and ask me to play some music on any of these.")
        return
    else:
        chosen = [value for key, value in devices.items() if key.lower() in device.lower()]
        if not chosen:
            speaker.say("I don't see any matching devices sir!. Let me help you.")
            google_home()
        for target in chosen:
            file_url = serve_file(file, "audio/mp3")  # serves the file on local host and generates the play url
            sys.stdout.write("\r")
            sys.stdout = open(os.devnull, 'w')  # suppresses print statement from "googlehomepush/__init.py__"
            GoogleHome(host=target).play(file_url, "audio/mp3")
            sys.stdout = sys.__stdout__  # removes print statement's suppression above
        speaker.say("Enjoy your music sir!") if len(chosen) == 1 else \
            speaker.say(f"That's interesting, you've asked me to play on {len(chosen)} devices at a time. "
                        f"I hope you'll enjoy this sir.")
        speaker.runAndWait()


def jokes() -> None:
    """Uses jokes lib to say chucknorris jokes."""
    speaker.say(choice([geek, icanhazdad, chucknorris, icndb])())


def reminder(converted: str) -> None:
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder.

    Args:
        converted: Takes the voice recognized statement as argument and extracts the time and message from it.
    """
    message = re.search(' to (.*) at ', converted) or re.search(' about (.*) at ', converted)
    if not message:
        message = re.search(' to (.*)', converted) or re.search(' about (.*)', converted)
        if not message:
            speaker.say('Reminder format should be::Remind me to do something, at some time.')
            sys.stdout.write('\rReminder format should be::Remind ME to do something, AT some time.')
            return
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
        r'([0-9]+\s?(?:a.m.|p.m.:?))', converted)
    if not extracted_time:
        if os.environ.get('called_by_offline'):
            speaker.say('Reminder format should be::Remind me to do something, at some time.')
            return
        speaker.say("When do you want to be reminded sir?")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
                r'([0-9]+\s?(?:a.m.|p.m.:?))', converted)
        else:
            return
    if message and extracted_time:
        to_about = 'about' if 'about' in converted else 'to'
        message = message.group(1).strip()
        extracted_time = extracted_time[0]
        am_pm = extracted_time.split()[-1]
        am_pm = str(am_pm).replace('a.m.', 'AM').replace('p.m.', 'PM')
        alarm_time = extracted_time.split()[0]
        if ":" in extracted_time:
            hour = int(alarm_time.split(":")[0])
            minute = int(alarm_time.split(":")[-1])
        else:
            hour = int(alarm_time.split()[0])
            minute = 0
        # makes sure hour and minutes are two digits
        hour, minute = f"{hour:02}", f"{minute:02}"
        if int(hour) <= 12 and int(minute) <= 59:
            open(f'reminder/{hour}_{minute}_{am_pm}|{message.replace(" ", "_")}.lock', 'a')
            Reminder(hour, minute, am_pm, message).start()
            speaker.say(f"{choice(ack)}! I will remind you {to_about} {message}, at {hour}:{minute} {am_pm}.")
            sys.stdout.write(f"\r{message} at {hour}:{minute} {am_pm}")
        else:
            speaker.say(f"A reminder at {hour}:{minute} {am_pm}? Are you an alien? "
                        f"I don't think a time like that exists on Earth.")
    else:
        speaker.say('Reminder format should be::Remind me to do something, at some time.')
        sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
    return


def google_maps(query: str) -> bool:
    """Uses google's places api to get places near by or any particular destination.

    This function is triggered when the words in user's statement doesn't match with any predefined functions.

    Args:
        query: Takes the voice recognized statement as argument.

    Returns:
        bool:
        Boolean True if google's maps API is unable to fetch consumable results.
    """
    maps_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    response = get(maps_url + 'query=' + query + '&key=' + maps_api)
    collection = response.json()['results']
    required = []
    for element in range(len(collection)):
        try:
            name = collection[element]['name']
            rating = collection[element]['rating']
            full_address = collection[element]['formatted_address']
            geometry = collection[element]['geometry']['location']
            address = re.search('(.*)Rd|(.*)Ave|(.*)St |(.*)St,|(.*)Blvd|(.*)Ct', full_address)
            address = address.group().replace(',', '')
            new_dict = {"Name": name, "Rating": rating, "Address": address, "Location": geometry, "place": full_address}
            required.append(new_dict)
        except (AttributeError, KeyError):
            pass
    if required:
        required = sorted(required, key=lambda sort: sort['Rating'], reverse=True)
    else:
        return True
    results = len(required)
    speaker.say(f"I found {results} results sir!") if results != 1 else None
    start = current_lat, current_lon
    n = 0
    for item in required:
        item['Address'] = item['Address'].replace(' N ', ' North ').replace(' S ', ' South ').replace(' E ', ' East ') \
            .replace(' W ', ' West ').replace(' Rd', ' Road').replace(' St', ' Street').replace(' Ave', ' Avenue') \
            .replace(' Blvd', ' Boulevard').replace(' Ct', ' Court')
        # noinspection PyTypeChecker,PyUnresolvedReferences
        latitude, longitude = item['Location']['lat'], item['Location']['lng']
        end = f"{latitude},{longitude}"
        far = round(geodesic(start, end).miles)
        miles = f'{far} miles' if far > 1 else f'{far} mile'
        n += 1
        if results == 1:
            option = 'only option I found is'
            next_val = "Do you want to head there sir?"
        elif n <= 2:
            option = f'{engine().ordinal(n)} option is'
            next_val = "Do you want to head there sir?"
        elif n <= 5:
            option = 'next option would be'
            next_val = "Would you like to try that?"
        else:
            option = 'other'
            next_val = 'How about that?'
        speaker.say(f"The {option}, {item['Name']}, with {item['Rating']} rating, "
                    f"on{''.join([j for j in item['Address'] if not j.isdigit()])}, which is approximately "
                    f"{miles} away.")
        speaker.say(f"{next_val}")
        sys.stdout.write(f"\r{item['Name']} -- {item['Rating']} -- "
                         f"{''.join([j for j in item['Address'] if not j.isdigit()])}")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=3)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                break
            elif any(word in converted.lower() for word in keywords.ok()):
                maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
                web_open(maps_url)
                speaker.say("Directions on your screen sir!")
                return False
            elif results == 1:
                return False
            elif n == results:
                speaker.say("I've run out of options sir!")
                return False
            else:
                continue
        else:
            google_maps.has_been_called = True
            return False


def notes() -> None:
    """Listens to the user and saves everything to a ``notes.txt`` file."""
    converted = listener(timeout=5, phrase_limit=10)
    if converted != 'SR_ERROR':
        if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
            return
        else:
            with open(r'notes.txt', 'a') as writer:
                writer.write(f"{datetime.now().strftime('%A, %B %d, %Y')}\n{datetime.now().strftime('%I:%M %p')}\n"
                             f"{converted}\n")


def github(target: list) -> None:
    """Clones the github repository matched with existing repository in conditions function.

    Asks confirmation if the results are more than 1 but less than 3 else asks to be more specific.

    Args:
        target: Takes repository name as argument which has to be cloned.
    """
    if len(target) == 1:
        os.system(f"cd {home} && git clone -q {target[0]}")
        cloned = target[0].split('/')[-1].replace('.git', '')
        speaker.say(f"I've cloned {cloned} on your home directory sir!")
        return
    elif len(target) <= 3:
        newest = [new.split('/')[-1] for new in target]
        sys.stdout.write(f"\r{', '.join(newest)}")
        speaker.say(f"I found {len(target)} results. On your screen sir! Which one shall I clone?")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=5)
        if converted != 'SR_ERROR':
            if any(word in converted.lower() for word in keywords.exit()):
                return
            if 'first' in converted.lower():
                item = 1
            elif 'second' in converted.lower():
                item = 2
            elif 'third' in converted.lower():
                item = 3
            else:
                item = None
                speaker.say("Only first second or third can be accepted sir! Try again!")
                github(target)
            os.system(f"cd {home} && git clone -q {target[item]}")
            cloned = target[item].split('/')[-1].replace('.git', '')
            speaker.say(f"I've cloned {cloned} on your home directory sir!")
    else:
        speaker.say(f"I found {len(target)} repositories sir! You may want to be more specific.")


def notify(user: str, password: str, number: str, body: str) -> None:
    """Send text message through SMS gateway of destination number.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS.

    Args:
        user: Gmail username to authenticate SMTP lib.
        password: Gmail password to authenticate SMTP lib.
        number: Phone number stored as env var.
        body: Content of the message.
    """
    subject = "Message from Jarvis" if number == phone_number else "Jarvis::Message from Vignesh"
    Messenger(gmail_user=user, gmail_pass=password, phone_number=number, subject=subject,
              message=f'\n\n{body}').send_sms()


def send_sms(number: int or None) -> None:
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        number: Phone number to which the message has to be sent.
    """
    if not number:
        speaker.say("Please tell me a number sir!")
        speaker.runAndWait()
        number = listener(timeout=3, phrase_limit=5)
        if number != 'SR_ERROR':
            if 'exit' in number or 'quit' in number or 'Xzibit' in number:
                return
            else:
                sys.stdout.write(f'\rNumber: {number}')
    elif len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) != 10:
        sys.stdout.write(f'\r{number}')
        speaker.say("I don't think that's a right number sir! Phone numbers are 10 digits. Try again!")
        send_sms(number=None)
    if number and len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) == 10:
        speaker.say("What would you like to send sir?")
        speaker.runAndWait()
        body = listener(timeout=3, phrase_limit=5)
        if body != 'SR_ERROR':
            sys.stdout.write(f'\r{body}::to::{number}')
            speaker.say(f'{body} to {number}. Do you want me to proceed?')
            speaker.runAndWait()
            converted = listener(timeout=3, phrase_limit=3)
            if converted != 'SR_ERROR':
                if not any(word in converted.lower() for word in keywords.ok()):
                    speaker.say("Message will not be sent sir!")
                else:
                    notify(user=gmail_user, password=gmail_pass, number=number, body=body)
                    speaker.say("Message has been sent sir!")
                return


# noinspection PyUnboundLocalVariable
def television(converted: str) -> None:
    """Controls all actions on a TV (LG Web OS).

    Notes:
        - In the ``__main__`` method tv is set to None.
        - Jarvis will try to ping the TV and then power it on if the host is unreachable initially.
        - Once the tv is turned on, the TV class is also initiated and assigned to tv variable.

    Args:
        converted: Takes the voice recognized statement as argument.
    """
    phrase_exc = converted.replace('TV', '')
    phrase = phrase_exc.lower()

    # 'tv_status = lambda: os.system(f"ping ....) #noqa' is an alternate but adhering to pep 8 best practice using a def
    def tv_status():
        """Pings the tv and returns the status. 0 if able to ping, 256 if unable to ping."""
        return os.system(f"ping -c 1 -t 1 {tv_ip} >/dev/null")  # pings TV IP and returns 0 if host is reachable

    if vpn_checker().startswith('VPN'):
        return
    elif ('turn off' in phrase or 'shutdown' in phrase or 'shut down' in phrase) and tv_status() != 0:
        speaker.say("I wasn't able to connect to your TV sir! I guess your TV is powered off already.")
        return
    elif tv_status() != 0:
        Thread(target=wake, args=[tv_mac]).start()  # turns TV on in a thread
        speaker.say("Looks like your TV is powered off sir! Let me try to turn it back on!")
        speaker.runAndWait()  # speaks the message to buy some time while the TV is connecting to network

    if tv_status() != 0:  # checks if TV is reachable even before trying to launch the TV connector
        speaker.say("I wasn't able to connect to your TV sir! Please make sure you are on the "
                    "same network as your TV, and your TV is connected to a power source.")
        return

    if not tv_state.get('status'):
        try:
            tv = TV(ip_address=tv_ip, client_key=tv_client_key)
        except ConnectionResetError as error:
            logger.error(f"Failed to connect to the TV. {error}")
            speaker.say("I was unable to connect to the TV sir! It appears to be a connection issue. "
                        "You might want to try again later.")
            return
        tv_state['status'] = True
        if 'turn on' in phrase or 'connect' in phrase:
            speaker.say("TV features have been integrated sir!")
            return

    if tv_state.get('status'):
        if 'turn on' in phrase or 'connect' in phrase:
            speaker.say('Your TV is already powered on sir!')
        elif 'increase' in phrase:
            tv.increase_volume()
            speaker.say(f'{choice(ack)}!')
        elif 'decrease' in phrase or 'reduce' in phrase:
            tv.decrease_volume()
            speaker.say(f'{choice(ack)}!')
        elif 'mute' in phrase:
            tv.mute()
            speaker.say(f'{choice(ack)}!')
        elif 'pause' in phrase or 'hold' in phrase:
            tv.pause()
            speaker.say(f'{choice(ack)}!')
        elif 'resume' in phrase or 'play' in phrase:
            tv.play()
            speaker.say(f'{choice(ack)}!')
        elif 'rewind' in phrase:
            tv.rewind()
            speaker.say(f'{choice(ack)}!')
        elif 'forward' in phrase:
            tv.forward()
            speaker.say(f'{choice(ack)}!')
        elif 'stop' in phrase:
            tv.stop()
            speaker.say(f'{choice(ack)}!')
        elif 'set' in phrase:
            vol = int(''.join([str(s) for s in re.findall(r'\b\d+\b', phrase_exc)]))
            sys.stdout.write(f'\rRequested volume: {vol}')
            if vol:
                tv.set_volume(vol)
                speaker.say(f"I've set the volume to {vol}% sir.")
            else:
                speaker.say(f"{vol} doesn't match the right format sir!")
        elif 'volume' in phrase:
            speaker.say(f"The current volume on your TV is, {tv.get_volume()}%")
        elif 'app' in phrase or 'application' in phrase:
            sys.stdout.write(f'\r{tv.list_apps()}')
            speaker.say('App list on your screen sir!')
            speaker.runAndWait()
            sleep(5)
        elif 'open' in phrase or 'launch' in phrase:
            app_name = ''
            for word in phrase_exc.split():
                if word[0].isupper():
                    app_name += word + ' '
            if not app_name:
                speaker.say("I didn't quite get that.")
            else:
                try:
                    tv.launch_app(app_name.strip())
                    speaker.say(f"I've launched {app_name} on your TV sir!")
                except ValueError:
                    speaker.say(f"I didn't find the app {app_name} on your TV sir!")
        elif "what's" in phrase or 'currently' in phrase:
            speaker.say(f'{tv.current_app()} is running on your TV.')
        elif 'change' in phrase or 'source' in phrase:
            tv_source = ''
            for word in phrase_exc.split():
                if word[0].isupper():
                    tv_source += word + ' '
            if not tv_source:
                speaker.say("I didn't quite get that.")
            else:
                try:
                    tv.set_source(tv_source.strip())
                    speaker.say(f"I've changed the source to {tv_source}.")
                except ValueError:
                    speaker.say(f"I didn't find the source {tv_source} on your TV sir!")
        elif 'shutdown' in phrase or 'shut down' in phrase or 'turn off' in phrase:
            Thread(target=tv.shutdown).start()
            speaker.say(f'{choice(ack)}! Turning your TV off.')
            tv_state.pop('status')
        else:
            speaker.say("I didn't quite get that.")
    else:
        converted = converted.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speaker.say(f"I'm sorry sir! I wasn't able to {converted}, as the TV state is unknown!")


def alpha(text: str) -> bool:
    """Uses wolfram alpha API to fetch results for uncategorized phrases heard.

    Args:
        text: Takes the voice recognized statement as argument.

    Raises:
        Broad ``Exception`` clause indicating that the Full Results API did not find an input parameter while parsing.

    Returns:
        bool:
        Boolean True if wolfram alpha API is unable to fetch consumable results.

    References:
        `Error 1000 <https://products.wolframalpha.com/show-steps-api/documentation/#:~:text=(Error%201000)>`__
    """
    alpha_client = Think(app_id=think_id)
    # noinspection PyBroadException
    try:
        res = alpha_client.query(text)
    except Exception:
        return True
    if res['@success'] == 'false':
        return True
    else:
        try:
            response = next(res.results).text
            response = response.replace('\n', '. ').strip()
            sys.stdout.write(f'\r{response}')
            if response == '(no data available)':
                return True
            speaker.say(response)
        except (StopIteration, AttributeError):
            return True


def google(query: str, suggestion_count: int = 0) -> bool:
    """Uses Google's search engine parser and gets the first result that shows up on a google search.

    Notes:
        - If it is unable to get the result, Jarvis sends a request to ``suggestqueries.google.com``
        - This is to rephrase the query and then looks up using the search engine parser once again.
        - ``suggestion_count`` is used to limit the number of times suggestions are used.
        - ``suggestion_count`` is also used to make sure the suggestions and parsing don't run on an infinite loop.
        - This happens when ``google`` gets the exact search as suggested ones which failed to fetch results earlier.

    Args:
        suggestion_count: Integer value that keeps incrementing when ``Jarvis`` looks up for suggestions.
        query: Takes the voice recognized statement as argument.

    Returns:
        bool:
        Boolean ``True`` if google search engine is unable to fetch consumable results.
    """
    search_engine = GoogleSearch()
    results = []
    try:
        google_results = search_engine.search(query, cache=False)
        a = {"Google": google_results}
        results = [result['titles'] for k, v in a.items() for result in v]
    except NoResultsOrTrafficError:
        suggest_url = "http://suggestqueries.google.com/complete/search"
        params = {
            "client": "firefox",
            "q": query,
        }
        r = get(suggest_url, params)
        if not r:
            return True
        try:
            suggestion = r.json()[1][1]
            suggestion_count += 1
            if suggestion_count >= 3:  # avoids infinite suggestions over the same suggestion
                speaker.say(r.json()[1][0].replace('=', ''))  # picks the closest match and opens a google search
                speaker.runAndWait()
                return False
            else:
                google(suggestion, suggestion_count)
        except IndexError:
            return True
    if results:
        [results.remove(result) for result in results if len(result.split()) < 3]  # removes results with dummy words
    else:
        return False
    if results:
        results = results[0:3]  # picks top 3 (first appeared on Google)
        results.sort(key=lambda x: len(x.split()), reverse=True)  # sorts in reverse by the word count of each sentence
        output = results[0]  # picks the top most result
        if '\n' in output:
            required = output.split('\n')
            modify = required[0].strip()
            split_val = ' '.join(splitter(modify.replace('.', 'rEpLaCInG')))
            sentence = split_val.replace(' rEpLaCInG ', '.')
            repeats = []
            [repeats.append(word) for word in sentence.split() if word not in repeats]
            refined = ' '.join(repeats)
            output = refined + required[1] + '.' + required[2]
        output = output.replace('\\', ' or ')
        match = re.search(r'(\w{3},|\w{3}) (\d,|\d|\d{2},|\d{2}) \d{4}', output)
        if match:
            output = output.replace(match.group(), '')
        output = output.replace('\\', ' or ')
        sys.stdout.write(f'\r{output}')
        speaker.say(output)
        speaker.runAndWait()
        return False
    else:
        return True


def google_search(phrase: str or None) -> None:
    """Opens up a google search for the phrase received. If nothing was received, gets phrase from user.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    if not phrase:
        speaker.say("Please tell me the search phrase.")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=5)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'xzibit' in converted or 'cancel' in converted:
                return
            else:
                phrase = converted.lower()
    search = str(phrase).replace(' ', '+')
    unknown_url = f"https://www.google.com/search?q={search}"
    web_open(unknown_url)
    speaker.say(f"I've opened up a google search for: {phrase}.")


def volume_controller(level: int) -> None:
    """Controls volume from the numbers received. Defaults to 50%.

    Args:
        level: Level of volume to which the system has to set.
    """
    sys.stdout.write("\r")
    level = round((8 * level) / 100)
    os.system(f'osascript -e "set Volume {level}"')


def face_recognition_detection() -> None:
    """Initiates face recognition script and looks for images stored in named directories within ``train`` directory."""
    sys.stdout.write("\r")
    train_dir = 'train'
    os.mkdir(train_dir) if not os.path.isdir(train_dir) else None
    speaker.say('Initializing facial recognition. Please smile at the camera for me.')
    speaker.runAndWait()
    sys.stdout.write('\rLooking for faces to recognize.')
    try:
        result = Face().face_recognition()
    except BlockingIOError:
        logger.error('Unable to access the camera.')
        speaker.say("I was unable to access the camera. Facial recognition can work only when cameras are "
                    "present and accessible.")
        return
    if not result:
        sys.stdout.write('\rLooking for faces to detect.')
        speaker.say("No faces were recognized. Switching on to face detection.")
        speaker.runAndWait()
        result = Face().face_detection()
        if not result:
            sys.stdout.write('\rNo faces were recognized nor detected.')
            speaker.say('No faces were recognized. nor detected. Please check if your camera is working, '
                        'and look at the camera when you retry.')
            return
        sys.stdout.write('\rNew face has been detected. Like to give it a name?')
        speaker.say('I was able to detect a face, but was unable to recognize it.')
        os.system('open cv2_open.jpg')
        speaker.say("I've taken a photo of you. Preview on your screen. Would you like to give it a name, "
                    "so that I can add it to my database of known list? If you're ready, please tell me a name, "
                    "or simply say exit.")
        speaker.runAndWait()
        phrase = listener(timeout=3, phrase_limit=5)
        if any(word in phrase.lower() for word in keywords.ok()):
            sys.stdout.write(f"\r{phrase}")
            phrase = phrase.replace(' ', '_')
            # creates a named directory if it is not found already else simply ignores
            os.system(f'cd {train_dir} && mkdir {phrase}') if not os.path.exists(f'{train_dir}/{phrase}') else None
            c_time = datetime.now().strftime("%I_%M_%p")
            img_name = f"{phrase}_{c_time}.jpg"  # adds current time to image name to avoid overwrite
            os.rename('cv2_open.jpg', img_name)  # renames the files
            os.system(f"mv {img_name} {train_dir}/{phrase}")  # move files into named directory within train_dir
            speaker.say(f"Image has been saved as {img_name}. I will be able to recognize {phrase} in the future.")
        else:
            os.remove('cv2_open.jpg')
            speaker.say("I've deleted the image.")
    else:
        speaker.say(f'Hi {result}! How can I be of service to you?')


def speed_test() -> None:
    """Initiates speed test and says the ping rate, download and upload speed."""
    client_locator = geo_locator.reverse(st.lat_lon, language='en')
    client_location = client_locator.raw['address']
    city, state = client_location.get('city'), client_location.get('state')
    isp = st.results.client.get('isp').replace(',', '').replace('.', '')
    sys.stdout.write(f"\rStarting speed test with your ISP: {isp}. Location: {city}, {state}")
    speaker.say(f"Starting speed test sir! I.S.P: {isp}. Location: {city} {state}")
    speaker.runAndWait()
    st.download() and st.upload()
    ping = round(st.results.ping)
    download = size_converter(st.results.download)
    upload = size_converter(st.results.upload)
    sys.stdout.write(f'\rPing: {ping}m/s\tDownload: {download}\tUpload: {upload}')
    speaker.say(f'Ping rate: {ping} milli seconds.')
    speaker.say(f'Download speed: {download} per second.')
    speaker.say(F'Upload speed: {upload} per second.')


def connector(phrase: str, targets: dict) -> bool:
    """Scans bluetooth devices in range and establishes connection with the matching device in phrase.

    Args:
        phrase: Takes the spoken phrase as an argument.
        targets: Takes a dictionary of scanned devices as argument.

    Returns:
        bool:
        Boolean True or False based on connection status.
    """
    connection_attempt = False
    for target in targets:
        if target['name']:
            target['name'] = normalize("NFKD", target['name'])
            if any(re.search(line, target['name'], flags=re.IGNORECASE) for line in phrase.split()):
                connection_attempt = True
                if 'disconnect' in phrase:
                    output = getoutput(f"blueutil --disconnect {target['address']}")
                    if not output:
                        sys.stdout.write(f"\rDisconnected from {target['name']}")
                        sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                        speaker.say(f"Disconnected from {target['name']} sir!")
                    else:
                        speaker.say(f"I was unable to disconnect {target['name']} sir!. "
                                    f"Perhaps it was never connected.")
                elif 'connect' in phrase:
                    output = getoutput(f"blueutil --connect {target['address']}")
                    if not output:
                        sys.stdout.write(f"\rConnected to {target['name']}")
                        sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                        speaker.say(f"Connected to {target['name']} sir!")
                    else:
                        speaker.say(f"Unable to connect {target['name']} sir!, please make sure the device is "
                                    f"turned on and ready to pair.")
                break
    return connection_attempt


def bluetooth(phrase: str) -> None:
    """Find and connect to bluetooth devices near by.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    if 'turn off' in phrase or 'power off' in phrase:
        call("blueutil --power 0", shell=True)
        sys.stdout.write('\rBluetooth has been turned off')
        speaker.say("Bluetooth has been turned off sir!")
    elif 'turn on' in phrase or 'power on' in phrase:
        call("blueutil --power 1", shell=True)
        sys.stdout.write('\rBluetooth has been turned on')
        speaker.say("Bluetooth has been turned on sir!")
    elif 'disconnect' in phrase and ('bluetooth' in phrase or 'devices' in phrase):
        call("blueutil --power 0", shell=True)
        sleep(2)
        call("blueutil --power 1", shell=True)
        speaker.say('All bluetooth devices have been disconnected sir!')
    else:
        sys.stdout.write('\rScanning paired Bluetooth devices')
        paired = getoutput("blueutil --paired --format json")
        paired = json_loads(paired)
        if not connector(phrase=phrase, targets=paired):
            sys.stdout.write('\rScanning UN-paired Bluetooth devices')
            speaker.say('No connections were established sir, looking for un-paired devices.')
            speaker.runAndWait()
            unpaired = getoutput("blueutil --inquiry --format json")
            unpaired = json_loads(unpaired)
            connector(phrase=phrase, targets=unpaired) if unpaired else speaker.say('No un-paired devices found sir! '
                                                                                    'You may want to be more precise.')


def increase_brightness() -> None:
    """Increases the brightness to maximum in macOS."""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def decrease_brightness() -> None:
    """Decreases the brightness to bare minimum in macOS."""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")


def set_brightness(level: int) -> None:
    """Set brightness to a custom level.

    - Since Jarvis uses in-built apple script, the only way to achieve this is to:
        - set the brightness to bare minimum and increase [*]% from there or vice-versa.

    Args:
        level: Percentage of brightness to be set.
    """
    level = round((32 * int(level)) / 100)
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")
    for _ in range(level):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def lights(converted: str) -> None:
    """Controller for smart lights.

    Args:
        converted: Takes the voice recognized statement as argument.
    """

    def light_switch():
        """Says a message if the physical switch is toggled off."""
        speaker.say("I guess your light switch is turned off sir! I wasn't able to read the device. "
                    "Try toggling the switch and ask me to restart myself!")

    def turn_off(host: str):
        """Turns off the device.

        Args:
            host: Takes target device IP address as an argument.
        """
        controller = MagicHomeApi(device_ip=host, device_type=1, operation='Turn Off')
        controller.turn_off()

    def warm(host: str):
        """Sets lights to warm/yellow.

        Args:
            host: Takes target device IP address as an argument.
        """
        controller = MagicHomeApi(device_ip=host, device_type=1, operation='Warm Lights')
        controller.update_device(r=0, g=0, b=0, warm_white=255)

    def cool(host: str):
        """Sets lights to cool/white.

        Args:
            host: Takes target device IP address as an argument.
        """
        controller = MagicHomeApi(device_ip=host, device_type=2, operation='Cool Lights')
        controller.update_device(r=255, g=255, b=255, warm_white=255, cool_white=255)

    def preset(host: str, value: int):
        """Changes light colors to preset values.

        Args:
            host: Takes target device IP address as an argument.
            value: Preset value extracted from list of verified values.
        """
        controller = MagicHomeApi(device_ip=host, device_type=2, operation='Preset Values')
        controller.send_preset_function(preset_number=value, speed=101)

    def lumen(host: str, warm_lights: bool, rgb: int = 255):
        """Sets lights to custom brightness.

        Args:
            host: Takes target device IP address as an argument.
            warm_lights: Boolean value if lights have been set to warm or cool.
            rgb: Red, Green andBlue values to alter the brightness.
        """
        if warm_lights:
            controller = MagicHomeApi(device_ip=host, device_type=1, operation='Custom Brightness')
            controller.update_device(r=255, g=255, b=255, warm_white=rgb)
        else:
            controller = MagicHomeApi(device_ip=host, device_type=2, operation='Custom Brightness')
            controller.update_device(r=255, g=255, b=255, warm_white=rgb, cool_white=rgb)

    if 'hallway' in converted:
        if not (light_host_id := hallway_ip):
            light_switch()
            return
    elif 'kitchen' in converted:
        if not (light_host_id := kitchen_ip):
            light_switch()
            return
    elif 'bedroom' in converted:
        if not (light_host_id := bedroom_ip):
            light_switch()
            return
    else:
        light_host_id = hallway_ip + kitchen_ip + bedroom_ip

    lights_count = len(light_host_id)

    def thread_worker(function_to_call: staticmethod) -> None:
        """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        with ThreadPoolExecutor(max_workers=lights_count) as executor:
            executor.map(function_to_call, light_host_id)

    plural = 'lights!' if lights_count > 1 else 'light!'
    if 'turn on' in converted or 'cool' in converted or 'white' in converted:
        warm_light.pop('status') if warm_light.get('status') else None
        tone = 'white' if 'white' in converted else 'cool'
        speaker.say(f'{choice(ack)}! Turning on {lights_count} {plural}') if 'turn on' in converted else \
            speaker.say(f'{choice(ack)}! Setting {lights_count} {plural} to {tone}!')
        Thread(target=thread_worker, args=[cool]).start()
    elif 'turn off' in converted:
        speaker.say(f'{choice(ack)}! Turning off {lights_count} {plural}')
        Thread(target=thread_worker, args=[turn_off]).start()
    elif 'warm' in converted or 'yellow' in converted:
        warm_light['status'] = True
        speaker.say(f'{choice(ack)}! Setting {lights_count} {plural} to yellow!') if 'yellow' in converted else \
            speaker.say(f'Sure sir! Setting {lights_count} {plural} to warm!')
        Thread(target=thread_worker, args=[warm]).start()
    elif 'red' in converted:
        speaker.say(f"{choice(ack)}! I've changed {lights_count} {plural} to red!")
        for light_ip in light_host_id:
            preset(host=light_ip, value=preset_values['red'])
    elif 'blue' in converted:
        speaker.say(f"{choice(ack)}! I've changed {lights_count} {plural} to blue!")
        for light_ip in light_host_id:
            preset(host=light_ip, value=preset_values['blue'])
    elif 'green' in converted:
        speaker.say(f"{choice(ack)}! I've changed {lights_count} {plural} to green!")
        for light_ip in light_host_id:
            preset(host=light_ip, value=preset_values['green'])
    elif 'set' in converted or 'percentage' in converted or '%' in converted or 'dim' in converted \
            or 'bright' in converted:
        if 'bright' in converted:
            level = 100
        elif 'dim' in converted:
            level = 50
        else:
            if level := re.findall(r'\b\d+\b', converted):
                level = int(level[0])
            else:
                level = 100
        speaker.say(f"{choice(ack)}! I've set {lights_count} {plural} to {level}%!")
        level = round((255 * level) / 100)
        for light_ip in light_host_id:
            lumen(host=light_ip, warm_lights=warm_light.get('status'), rgb=level)
    else:
        speaker.say(f"I didn't quite get that sir! What do you want me to do to your {plural}?")


def vpn_checker() -> str:
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        str:
        Private IP address of host machine.
    """
    socket_ = socket(AF_INET, SOCK_DGRAM)
    socket_.connect(("8.8.8.8", 80))
    ip_address = socket_.getsockname()[0]
    socket_.close()
    if not (ip_address.startswith('192') | ip_address.startswith('127')):
        ip_address = 'VPN:' + ip_address
        info = json_load(urlopen('http://ipinfo.io/json'))
        sys.stdout.write(f"\rVPN connection is detected to {info.get('ip')} at {info.get('city')}, "
                         f"{info.get('region')} maintained by {info.get('org')}")
        speaker.say("You have your VPN turned on. Details on your screen sir! Please note that none of the home "
                    "integrations will work with VPN enabled.")
    return ip_address


def celebrate() -> str:
    """Function to look if the current date is a holiday or a birthday.

    Returns:
        str:
        A string of the event observed today.
    """
    day = datetime.today().date()
    today = datetime.now().strftime("%d-%B")
    us_holidays = CountryHoliday('US').get(day)  # checks if the current date is a US holiday
    in_holidays = CountryHoliday('IND', prov='TN', state='TN').get(day)  # checks if Indian (esp TN) holiday
    if in_holidays:
        return in_holidays
    elif us_holidays and 'Observed' not in us_holidays:
        return us_holidays
    elif today == birthday:
        return 'Birthday'


def time_travel() -> None:
    """Triggered only from ``initiator()`` to give a quick update on the user's daily routine."""
    part_day = part_of_day()
    meeting = None
    if not os.path.isfile('meetings') and part_day == 'Morning' and datetime.now().strftime('%A') not in \
            ['Saturday', 'Sunday']:
        meeting = ThreadPool(processes=1).apply_async(func=meetings)
    speaker.say(f"Good {part_day} Vignesh.")
    if part_day == 'Night':
        if event := celebrate():
            speaker.say(f'Happy {event}!')
        return
    current_date()
    current_time()
    weather()
    speaker.runAndWait()
    if os.path.isfile('meetings') and part_day == 'Morning' and datetime.now().strftime('%A') not in \
            ['Saturday', 'Sunday']:
        meeting_reader()
    elif meeting:
        try:
            speaker.say(meeting.get(timeout=30))
        except ThreadTimeoutError:
            pass  # skip terminate, close and join thread since the motive is to skip meetings info in case of a timeout
    todo()
    gmail()
    speaker.say('Would you like to hear the latest news?')
    speaker.runAndWait()
    phrase = listener(timeout=3, phrase_limit=3)
    if any(word in phrase.lower() for word in keywords.ok()):
        news()
    time_travel.has_been_called = False


def guard() -> None:
    """Security Mode will enable camera and microphone in the background.

    Notes:
        - If any speech is recognized or a face is detected, there will another thread triggered to send notifications.
        - Notifications will be triggered only after 5 minutes of previous notification.
    """
    import cv2
    cam_source, cam = None, None
    for i in range(0, 3):
        cam = cv2.VideoCapture(i)  # tries thrice to choose the camera for which Jarvis has access
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            pass
        else:
            cam_source = i  # source for security cam is chosen
            cam.release()
            break
    if cam_source is None:
        cam_error = 'Guarding mode disabled as I was unable to access any of the cameras.'
        logger.error(cam_error)
        response = Messenger(gmail_user=gmail_user, gmail_pass=gmail_pass, phone_number=phone_number,
                             subject="IMPORTANT::Guardian mode faced an exception.", message=cam_error).send_sms()
        if response.get('ok') and response.get('status') == 200:
            logger.info('SMS notification has been sent.')
        else:
            logger.error(f'Unable to send SMS notification.\n{response}')

    scale_factor = 1.1  # Parameter specifying how much the image size is reduced at each image scale.
    min_neighbors = 5  # Parameter specifying how many neighbors each candidate rectangle should have, to retain it.
    notified, date_extn, converted = None, None, None

    while True:
        # Listens for any recognizable speech and saves it to a notes file
        try:
            sys.stdout.write("\rSECURITY MODE")
            listened = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            converted = recognizer.recognize_google(listened)
            converted = converted.replace('Jarvis', '').strip()
            sys.stdout.write(f"\r{converted}")
        except (UnknownValueError, RequestError, WaitTimeoutError):
            pass

        if converted and any(word.lower() in converted.lower() for word in keywords.guard_disable()):
            logger.info('Disabled security mode')
            speaker.say(f'Welcome back sir! Good {part_of_day()}.')
            if os.path.exists(f'threat/{date_extn}.jpg'):
                speaker.say("We had a potential threat sir! Please check your email to confirm.")
            speaker.runAndWait()
            sys.stdout.write('\rDisabled Security Mode')
            break
        elif converted:
            logger.info(f'Conversation::{converted}')

        if cam_source is not None:
            # captures images and keeps storing it to a folder
            validation_video = cv2.VideoCapture(cam_source)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            ignore, image = validation_video.read()
            scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(scale, scale_factor, min_neighbors)
            date_extn = f"{datetime.now().strftime('%B_%d_%Y_%I_%M_%S_%p')}"
            try:
                if faces:
                    pass
            except ValueError:
                # log level set to critical because this is a known exception when try check 'if faces'
                cv2.imwrite(f'threat/{date_extn}.jpg', image)
                logger.info(f'Image of detected face stored as {date_extn}.jpg')

        if not os.path.exists(f'threat/{date_extn}.jpg'):
            date_extn = None

        # if no notification was sent yet or if a phrase or face is detected notification thread will be triggered
        if (not notified or float(time() - notified) > 300) and (converted or date_extn):
            notified = time()
            Thread(target=threat_notify, args=(converted, date_extn)).start()


def threat_notify(converted: str, date_extn: str or None) -> None:
    """Sends an SMS and email notification in case of a threat.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS and email.

    Args:
        converted: Takes the voice recognized statement as argument.
        date_extn: Name of the attachment file which is the picture of the intruder.
    """
    dt_string = f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    title_ = f'Intruder Alert on {dt_string}'

    if converted:
        response = Messenger(gmail_user=gmail_user, gmail_pass=gmail_pass, phone_number=phone_number,
                             subject="!!INTRUDER ALERT!!", message=f"{dt_string}\n{converted}").send_sms()
        body_ = f"""<html><head></head><body><h2>Conversation of Intruder:</h2><br>{converted}<br><br>
                                    <h2>Attached is a photo of the intruder.</h2>"""
    else:
        response = Messenger(gmail_user=gmail_user, gmail_pass=gmail_pass, phone_number=phone_number,
                             subject="!!INTRUDER ALERT!!",
                             message=f"{dt_string}\nCheck your email for more information.").send_sms()
        body_ = """<html><head></head><body><h2>No conversation was recorded,
                                but attached is a photo of the intruder.</h2>"""
    if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
        logger.info('SMS notification has been sent.')
    else:
        logger.error(f'Unable to send SMS notification.\n{response}')

    if date_extn:
        attachment_ = f'threat/{date_extn}.jpg'
        response_ = SendEmail(gmail_user=gmail_user, gmail_pass=gmail_pass,
                              recipient=robinhood_user, subject=title_, body=body_, attachment=attachment_).send_email()
        if response_.get('ok'):
            logger.info('Email has been sent!')
        else:
            logger.error(f"Email dispatch failed with response: {response_.get('body')}\n")


def offline_communicator_initiate() -> None:
    """Initiates Jarvis API and Ngrok for requests from external sources if they aren't running already.

    Notes:
        - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the port ``4483``.
        - The connection is tunneled through a public facing URL which is used to make ``POST`` requests to Jarvis API.
        - ``uvicorn`` command launches JarvisAPI ``fast.py`` using the same port ``4483``
    """
    ngrok_status, uvicorn_status = False, False
    target_scripts = ['forever_ngrok.py', 'uvicorn']
    for target_script in target_scripts:
        pid_check = check_output(f"ps -ef | grep {target_script}", shell=True)
        pid_list = pid_check.decode('utf-8').split('\n')
        for id_ in pid_list:
            if id_ and 'grep' not in id_ and '/bin/sh' not in id_:
                if target_script == 'forever_ngrok.py':
                    ngrok_status = True
                    logger.info('An instance of ngrok connection for offline communicator is running already.')
                elif target_script == 'uvicorn':
                    uvicorn_status = True
                    logger.info('An instance of uvicorn application for offline communicator is running already.')

    if not ngrok_status:
        logger.info('Initiating ngrok connection for offline communicator.')
        initiate = f'cd {home}/JarvisHelper && source venv/bin/activate && export ENV=1 && python3 {target_scripts[0]}'
        apple_script('Terminal').do_script(initiate)

    if not uvicorn_status:
        logger.info('Initiating FastAPI for offline listener.')
        offline_script = f'cd {os.getcwd()} && source venv/bin/activate && cd api && ' \
                         f'export offline_phrase={offline_phrase} && ' \
                         'uvicorn fast:app --reload --port=4483'
        apple_script('Terminal').do_script(offline_script)


def offline_communicator() -> None:
    """Reads ``offline_request`` file generated by `fast.py <https://git.io/JBPFQ>`__ containing request sent via API.

    See Also:
        To replicate a working model for offline communicator:
            - Run ``ngrok`` on port 4483 or any desired port.
            - The port number should match with the one in `fast.py <https://git.io/JBPFQ>`__
            - To "log" the response and send it out as notification, I made some changes to the pyttsx3 module. (below)
            - I also stop the response from being spoken.
            - ``voice_changer()`` is called as the voice property is reset when ``speaker.stop()`` is used.

        Changes in `pyttsx3`:
            - Created a global variable in ``say()`` -> ``pyttsx3/engine.py`` (before proxy) and store the response.
            - Created a new method and return the global variable which I created in ``say()``
            - The new method (``vig()`` in this case) is called to get the response which is sent as SMS notification.
            - Doing so, avoids changes to all functions within ``conditions()`` to notify the response from Jarvis.

        Env Vars:
            - ``offline_phrase`` - Unique phrase to authenticate the requests coming from an external source.

    Notes:
        More cool stuff:
            - I have linked the ngrok ``public_url`` tunnelling the FastAPI to a JavaScript on my webpage.
            - When a request is submitted, the JavaScript makes a POST call to the API.
            - The API does the authentication and creates the ``offline_request`` file if authenticated.
            - Check it out: `JarvisOffline <https://thevickypedia.com/jarvisoffline>`__

    Warnings:
        - Restarts quietly in case of a ``RuntimeError`` however, the offline request will still be be executed.
        - This happens when ``speaker`` is stopped while another loop of speaker is in progress by regular interaction.
    """
    while True:
        if os.path.isfile('offline_request'):
            sleep(0.3)  # Read file after half a second for the content to be written
            with open('offline_request', 'r') as off_request:
                command = off_request.read()
            logger.info(f'Received offline input::{command}')
            response = None
            try:
                if command:
                    os.remove('offline_request')
                    os.environ['called_by_offline'] = '1'  # Write env var so some function can use it
                    split(command)
                    del os.environ['called_by_offline']  # deletes the env var
                    sys.stdout.write('\r')
                    response = speaker.vig()
                else:
                    response = 'Received a null request. Please try to resend it'
                current_time_ = datetime.now(timezone(current_tz))
                dt_string = current_time_.strftime("%A, %B %d, %Y %I:%M:%S %p")
                if 'restart' not in command:
                    with open('offline_response', 'w') as off_response:
                        off_response.write(dt_string + '\n\n' + response)
                speaker.stop()
                voice_changer()
            except RuntimeError:
                if command and not response:
                    with open('offline_request', 'w') as off_request:
                        off_request.write(command)
                logger.error(f'Received a RuntimeError while executing offline request.\n{format_exc()}')
                restart(quiet=True, quick=True)
        if STOPPER.get('status'):
            break


def meeting_reader() -> None:
    """Speaks meeting information that ``meeting_gatherer()`` stored in a file named 'meetings'.

    If the file is not available, meeting information is directly fetched from the ``meetings()`` function.
    """
    with open('meetings', 'r') as meeting:
        meeting_info = meeting.read()
        sys.stdout.write(f'\r{meeting_info}')
        speaker.say(meeting_info)


def meeting_gatherer() -> None:
    """Gets return value from ``meetings()`` and writes it to file named ``meetings``.

    This function runs in a dedicated thread every 30 minutes to avoid wait time when meetings information is requested.
    """
    logger.info('Meeting gather has been initiated.')
    while True:
        if os.path.isfile('meetings') and int(datetime.now().timestamp()) - int(os.stat('meetings').st_mtime) < 1_800:
            os.remove('meetings')  # removes the file if it is older than 30 minutes
        data = meetings()
        if data.startswith('You'):
            with open('meetings', 'w') as gatherer:
                gatherer.write(data)
            gatherer.close()
        elif data == "The calendar Office is unavailable sir!":
            break
        if STOPPER.get('status'):
            break
        sleep(900)


def meeting_app_launcher() -> None:
    """Launches either Calendar or Outlook application which is required to read meetings."""
    if meeting_file == 'calendar.scpt':
        os.system('open /System/Applications/Calendar.app > /dev/null 2>&1')
    elif meeting_file == 'outlook.scpt':
        os.system("open /Applications/'Microsoft Outlook.app' > /dev/null 2>&1")


def meetings() -> str:
    """Uses ``applescript`` to fetch events/meetings from local Calendar (including subscriptions) or Microsoft Outlook.

    Returns:
        str:
        - On success, returns a message saying which meeting is scheduled at what time.
        - If no events, returns a message saying there are no events in the next 12 hours.
        - On failure, returns a message saying Jarvis was unable to read calendar/outlook.
    """
    args = [1, 3]
    source_app = meeting_file.replace('.scpt', '')
    failure = None
    process = Popen(['/usr/bin/osascript', meeting_file] + [str(arg) for arg in args], stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    os.system(f'git checkout -- {meeting_file}')  # Undo the unspecified changes done by ScriptEditor
    if error := process.returncode:  # stores process.returncode in error if process.returncode is not 0
        err_msg = err.decode('UTF-8')
        err_code = err_msg.split()[-1].strip()
        if err_code == '(-1728)':  # If the calendar named 'Office' in unavailable in the calendar application
            logger.error("Calendar, 'Office' is unavailable.")
            return "The calendar Office is unavailable sir!"
        elif err_code == '(-1712)':  # If an event takes 2+ minutes, the Apple Event Manager reports a time-out error.
            failure = f"{source_app}/event took an unusually long time to respond/complete.\nInclude, " \
                      f"'with timeout of 300 seconds' to your {meeting_file} right after the " \
                      f"'tell application {source_app}' step and 'end timeout' before the 'end tell' step."
        elif err_code in ['(-10810)', '(-609)', '(-600)']:  # If unable to launch the app or app terminates.
            meeting_app_launcher()
        if not failure:
            failure = f"Unable to read {source_app} - [{error}]\n{err_msg}"
        logger.error(failure)
        failure = failure.replace('"', '')  # An identifier can’t go after this “"”
        os.system(f"""osascript -e 'display notification "{failure}" with title "Jarvis"'""")
        return f"I was unable to read your {source_app} sir! Please make sure it is in sync."

    events = out.decode().strip()
    if not events or events == ',':
        return "You don't have any meetings in the next 12 hours sir!"

    events = events.replace(', date ', ' rEpLaCInG ')
    event_time = events.split('rEpLaCInG')[1:]
    event_name = events.split('rEpLaCInG')[0].split(', ')
    event_name = [i.strip() for n, i in enumerate(event_name) if i not in event_name[n + 1:]]  # remove duplicates
    count = len(event_time)
    [event_name.remove(e) for e in event_name if len(e) <= 5] if count != len(event_name) else None
    meeting_status = f'You have {count} meetings in the next 12 hours sir! ' if count > 1 else ''
    events = {}
    for i in range(count):
        if i < len(event_name):
            event_time[i] = re.search(' at (.*)', event_time[i]).group(1).strip()
            dt_string = datetime.strptime(event_time[i], '%I:%M:%S %p')
            event_time[i] = dt_string.strftime('%I:%M %p')
            events.update({event_name[i]: event_time[i]})
    ordered_data = sorted(events.items(), key=lambda x: datetime.strptime(x[1], '%I:%M %p'))
    for index, meeting in enumerate(ordered_data):
        if count == 1:
            meeting_status += f"You have a meeting at {meeting[1]} sir! {meeting[0].upper()}. "
        else:
            meeting_status += f"{meeting[0]} at {meeting[1]}, " if index + 1 < len(ordered_data) else \
                f"{meeting[0]} at {meeting[1]}."
    return meeting_status


def system_vitals() -> None:
    """Reads system vitals on MacOS.

    See Also:
        - Jarvis will suggest a reboot if the system uptime is more than 2 days.
        - If confirmed, invokes `restart <https://thevickypedia.github.io/Jarvis/#jarvis.restart>`__ function.
    """
    if not root_password:
        speaker.say("You haven't provided a root password for me to read system vitals sir! "
                    "Add the root password as an environment variable for me to read.")
        return

    version = host_info(required='version')
    model = host_info(required='model')

    cpu_temp, gpu_temp, fan_speed, output = None, None, None, ""
    if version >= 12:  # smc information is available only on 12+ versions (tested on 11.3, 12.1 and 16.1 versions)
        critical_info = [each.strip() for each in (os.popen(
            f'echo {root_password} | sudo -S powermetrics --samplers smc -i1 -n1'
        )).read().split('\n') if each != '']
        sys.stdout.write('\r')

        for info in critical_info:
            if 'CPU die temperature' in info:
                cpu_temp = info.strip('CPU die temperature: ').replace(' C', '').strip()
            if 'GPU die temperature' in info:
                gpu_temp = info.strip('GPU die temperature: ').replace(' C', '').strip()
            if 'Fan' in info:
                fan_speed = info.strip('Fan: ').replace(' rpm', '').strip()
    else:
        fan_speed = check_output(
            f'echo {root_password} | sudo -S spindump 1 1 -file /tmp/spindump.txt > /dev/null 2>&1;grep "Fan speed" '
            '/tmp/spindump.txt;sudo rm /tmp/spindump.txt', shell=True).decode('utf-8')

    if cpu_temp:
        cpu = f'Your current average CPU temperature is {format_nos(temperature.c2f(extract_nos(cpu_temp)))}°F. '
        output += cpu
        speaker.say(cpu)
    if gpu_temp:
        gpu = f'GPU temperature is {format_nos(temperature.c2f(extract_nos(gpu_temp)))}°F. '
        output += gpu
        speaker.say(gpu)
    if fan_speed:
        fan = f'Current fan speed is {format_nos(extract_nos(fan_speed))} RPM. '
        output += fan
        speaker.say(fan)

    restart_time = datetime.fromtimestamp(boot_time())
    second = (datetime.now() - restart_time).total_seconds()
    restart_time = datetime.strftime(restart_time, "%A, %B %d, at %I:%M %p")
    restart_duration = time_converter(seconds=second)
    output += f'Restarted on: {restart_time} - {restart_duration} ago from now.'
    if os.environ.get('called_by_offline'):
        speaker.say(output)
        return
    sys.stdout.write(f'\r{output}')
    speaker.say(f'Your {model} was last booted on {restart_time}. '
                f'Current boot time is: {restart_duration}.')
    if second >= 172_800:
        if boot_extreme := re.search('(.*) days', restart_duration):
            warn = int(boot_extreme.group().replace(' days', '').strip())
            speaker.say(f'Sir! your {model} has been running continuously for more than {warn} days. You must '
                        f'consider a reboot for better performance. Would you like me to restart it for you sir?')
            speaker.runAndWait()
            response = listener(timeout=3, phrase_limit=3)
            if any(word in response.lower() for word in keywords.ok()):
                logger.info(f'JARVIS::Restarting {host_info("model")}')
                restart(target='PC_Proceed')


def get_ssid() -> str:
    """Gets SSID of the network connected.

    Returns:
        str:
        WiFi or Ethernet SSID.
    """
    process = Popen(
        ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
        stdout=PIPE)
    out, err = process.communicate()
    if error := process.returncode:
        logger.error(f"Failed to fetch SSID with exit code: {error}\n{err}")
    # noinspection PyTypeChecker
    return dict(map(str.strip, info.split(': ')) for info in out.decode('utf-8').split('\n')[:-1]).get('SSID')


class PersonalCloud:
    """Controller for `Personal Cloud <https://github.com/thevickypedia/personal_cloud>`__.

    >>> PersonalCloud

    References:
        `PersonalCloud README.md <https://github.com/thevickypedia/personal_cloud/blob/main/README.md>`__

    See Also:
        PersonalCloud integration requires Admin previleages for the default ``Terminal``.

        Step 1:
            - Mac OS 10.14.* and higher - System Preferences -> Security & Privacy -> Privacy -> Full Disk Access
            - Mac OS 10.13.* and lower - System Preferences -> Security & Privacy -> Privacy -> Accessibility
        Step 2:
            Unlock for admin privileges. Click on the "+" icon. Select Applications -> Utilities -> Terminal
    """

    @staticmethod
    def get_port() -> int:
        """Chooses a TCP PORT number dynamically that is not being used to ensure we don't rely on a single port.

        - Well-Known ports: 0 to 1023
        - Registered ports: 1024 to 49151
        - Dynamically available: 49152 to 65535
        - Alternate to active_sessions ->
            - ``check_output(f"echo {PASSWORD} | sudo -S lsof -PiTCP -sTCP:LISTEN 2>&1;", shell=True).decode('utf-8')``
        - ``remove`` variable should be an actual function as per pep-8 standards, bypassing it using  # noqa

        Returns:
            int:
            Randomly chosen port number that is not in use.
        """
        active_sessions = check_output("netstat -anvp tcp | awk 'NR<3 || /LISTEN/' 2>&1;", shell=True).decode('utf-8')
        active_ports = [row.split()[3].split('.')[-1] for index, row in enumerate(active_sessions.split('\n')) if
                        row and index > 1]
        port = randrange(49152, 65535)
        if port not in active_ports:
            return port

    @staticmethod
    def delete_repo() -> None:
        """Called during enable and disable to delete any existing bits for a clean start next time."""
        os.system(f'rm -rf {home}/personal_cloud')  # delete repo for a fresh start

    # noinspection PyUnresolvedReferences
    @staticmethod
    def enable() -> None:
        """Enables `personal cloud <https://github.com/thevickypedia/personal_cloud>`__.

        Notes:
            - Clones ``personal_cloud`` repo in a dedicated Terminal.
            - Creates a virtual env and installs the requirements within it (ETA: ~20 seconds)
            - If ``personal_cloud_host`` env var is provided, Jarvis will mount the drive if connected to the device.
            - Sets env vars required for the personal cloud.
            - Generates random username and passphrase for login info.
            - Triggers personal cloud using another Terminal session.
            - Sends an SMS with ``endpoint``, ``username`` and ``password`` to the ``phone_number``.
        """
        personal_cloud.delete_repo()
        initial_script = f"cd {home} && git clone -q https://github.com/thevickypedia/personal_cloud.git && " \
                         f"cd personal_cloud && python3 -m venv venv && source venv/bin/activate && " \
                         f"pip3 install -r requirements.txt"

        try:
            apple_script('Terminal').do_script(initial_script)
        except (CommandError, EventError) as ps_error:
            logger.error(ps_error)
            notify(user=offline_receive_user, password=offline_receive_pass, number=phone_number,
                   body="Sir! I was unable to trigger your personal cloud due to lack of permissions.\n"
                        "Please check the log file.")
            return

        personal_cloud_port = personal_cloud.get_port()
        personal_cloud_username = ''.join(choices(ascii_letters, k=10))
        personal_cloud_password = ''.join(choices(ascii_letters + digits, k=10))
        personal_cloud_host = f"'{os.environ.get('personal_cloud_host')}'"

        # export PORT for both ngrok and exec scripts as they will be running in different Terminal sessions
        ngrok_script = f"cd {home}/personal_cloud && export port={personal_cloud_port} && " \
                       f"source venv/bin/activate && cd helper_functions && python3 ngrok.py"

        exec_script = f"export host_path='{personal_cloud_host}'" if personal_cloud_host and \
            os.path.isdir(personal_cloud_host) else ''
        exec_script += f"export port={personal_cloud_port} && " \
                       f"export username={personal_cloud_username} && " \
                       f"export password={personal_cloud_password} && " \
                       f"export gmail_user={gmail_user} && " \
                       f"export gmail_pass={gmail_pass} && " \
                       f"export recipient={icloud_user} && " \
                       f"cd {home}/personal_cloud && source venv/bin/activate && python3 authserver.py"

        cloned_path = f'{home}/personal_cloud'
        while True:  # wait for the requirements to be installed after the repo was cloned
            packages = [path.stem.split('-')[0] for path in Path(cloned_path).glob('**/site-packages/*')]
            if packages and not [req for req in [pkg.partition('==')[0] for pkg in
                                                 Path(f'{cloned_path}/requirements.txt').read_text().splitlines()] if
                                 req not in packages]:
                sleep(5)  # give some breathing time for indexing
                apple_script('Terminal').do_script(exec_script)
                apple_script('Terminal').do_script(ngrok_script)
                break

        while True:  # wait for the endpoint url (as file) to get generated within personal_cloud
            if os.path.exists(f'{cloned_path}/helper_functions/url'):
                with open(f'{cloned_path}/helper_functions/url', 'r') as file:
                    url = file.read()  # commit # dfc37853dfe232e268843cbe53719bd9a09903c4 on personal_cloud
                if url.startswith('http'):
                    notify(user=offline_receive_user, password=offline_receive_pass, number=phone_number,
                           body=f"URL: {url}\nUsername: {personal_cloud_username}\nPassword: {personal_cloud_password}")
                else:
                    notify(user=offline_receive_user, password=offline_receive_pass, number=phone_number,
                           body="Unable to start ngrok! Please check the logs for more information.")
                break

    @staticmethod
    def disable() -> None:
        """Kills `authserver.py <https://git.io/JchR5>`__ and `ngrok.py <https://git.io/JchBu>`__ to stop hosting.

        This eliminates the hassle of passing args and handling threads.
        """
        pid_check = check_output("ps -ef | grep 'authserver.py\\|ngrok.py'", shell=True)
        pid_list = pid_check.decode('utf-8').split('\n')
        for pid_info in pid_list:
            if pid_info and 'Library' in pid_info and ('/bin/sh' not in pid_info or 'grep' not in pid_info):
                os.system(f'kill -9 {pid_info.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout
        personal_cloud.delete_repo()


def vpn_server_check() -> bool:
    """Checks if an instance of VPN Server is running.

    Returns:
        bool:
        Returns ``True`` if an instance of ``vpn.py`` is currently running.
    """
    pid_check = check_output("ps -ef | grep vpn.py", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'grep' not in id_ and '/bin/sh' not in id_:
            return True


def vpn_server(operation: str) -> None:
    """Automator to ``START`` or ``STOP`` the VPN portal.

    Args:
        operation: Takes ``START`` or ``STOP`` as an argument.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
        - Pulls the latest version before starting the server.
        - Adds an env var ``ENV: Jarvis`` so, ``vpn-server`` can log the details in a log file.
    """
    base_script = f'cd {home}/vpn-server && git pull --quiet && source venv/bin/activate && export ENV=Jarvis'
    os.system(f'{base_script} && python vpn.py {operation} && exit')


def internet_checker() -> Union[Speedtest, bool]:
    """Uses speed test api to check for internet connection.

    Returns:
        ``Speedtest`` or bool:
        - On success, returns Speedtest module.
        - On failure, returns boolean False.
    """
    try:
        return Speedtest()
    except ConfigRetrievalError:
        return False


def morning() -> None:
    """Checks for the current time of the day and day of the week to trigger a series of morning messages."""
    clock = datetime.now()
    if clock.strftime('%A') not in ['Saturday', 'Sunday'] and int(clock.strftime('%S')) < 10:
        speaker.say("Good Morning. It's 7 AM.")
        time_travel.has_been_called = True
        weather()
        time_travel.has_been_called = False
        volume_controller(level=100)
        speaker.runAndWait()
        volume_controller(level=50)


def initiator(key_original: str, should_return: bool = False) -> None:
    """When invoked by ``Activator``, checks for the right keyword to wake up and gets into action.

    Args:
        key_original: Takes the processed string from ``SentryMode`` as input.
        should_return: Flag to return the function if nothing is heard.
    """
    if key_original == 'SR_ERROR' and should_return:
        return
    sys.stdout.write("\r")
    time_of_day = ['morning', 'night', 'afternoon', 'after noon', 'evening', 'goodnight']
    wake_up_words = ['look alive', 'wake up', 'wakeup', 'show time', 'showtime', 'time to work', 'spin up']
    key = key_original.lower()
    key_split = key.split()
    if [word for word in key_split if word in time_of_day]:
        time_travel.has_been_called = True
        if event := celebrate():
            speaker.say(f'Happy {event}!')
        if 'night' in key_split or 'goodnight' in key_split:
            Thread(target=pc_sleep).start()
        time_travel()
    elif 'you there' in key:
        speaker.say(f'{choice(wake_up1)}')
        initialize()
    elif any(word in key for word in wake_up_words):
        speaker.say(f'{choice(wake_up2)}')
        initialize()
    else:
        converted = ' '.join([i for i in key_original.split() if i.lower() not in ['buddy', 'jarvis', 'sr_error']])
        if converted:
            split(key=converted.strip(), should_return=should_return)
        else:
            speaker.say(f'{choice(wake_up3)}')
            initialize()


class Activator:
    """`Porcupine <https://github.com/Picovoice/porcupine>`__ wake word engine.

    >>> Activator

    See Also:
        - Creates an input audio stream from a microphone, monitors it, and detects the specified wake word.
        - Once detected, Jarvis triggers the ``listener()`` function with an ``acknowledgement`` sound played.
        - After processing the phrase, the converted text is sent as response to ``initiator()`` with a ``return`` flag.
        - The ``should_return`` flag ensures, the user is not disturbed when accidentally woke up by wake work engine.
    """

    @staticmethod
    def run() -> None:
        """Initiates Porcupine object for hot word detection.

        See Also:
            - Instantiates an instance of Porcupine object and monitors audio stream for occurrences of keywords.
            - A higher sensitivity results in fewer misses at the cost of increasing the false alarm rate.
            - sensitivity: Tolerance/Sensitivity level. Takes argument or env var ``sensitivity`` or defaults to ``0.5``

        References:
            - Porcupine `demo <https://git.io/JRBHb>`__ mic.
            - `Audio Overflow <https://people.csail.mit.edu/hubert/pyaudio/docs/#pyaudio.Stream.read>`__ handling.
        """
        sensitivity = float(os.environ.get('sensitivity', 0.5))
        logger.info(f'Initiating model with sensitivity: {sensitivity} - {type(sensitivity)}')
        keyword_paths = [KEYWORD_PATHS[x] for x in ['jarvis']]
        waker = create(
            library_path=LIBRARY_PATH,
            model_path=MODEL_PATH,
            keyword_paths=keyword_paths,
            sensitivities=[sensitivity]
        )

        py_audio = PyAudio()

        audio_stream = py_audio.open(
            rate=waker.sample_rate,
            channels=1,
            format=paInt16,
            input=True,
            frames_per_buffer=waker.frame_length,
            input_device_index=0)

        try:
            while True:
                sys.stdout.write('\rSentry Mode')
                pcm = audio_stream.read(waker.frame_length, exception_on_overflow=False)
                pcm = unpack_from("h" * waker.frame_length, pcm)
                if waker.process(pcm) >= 0:
                    Thread(target=playsound, args=['indicators/acknowledgement.mp3']).start()
                    initiator(key_original=listener(timeout=3, phrase_limit=5, sound=False), should_return=True)
                    speaker.runAndWait()
                elif STOPPER.get('status'):
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            logger.info('Releasing resources acquired by Porcupine.')
            waker.delete()
            logger.info('Closing Audio Stream.')
            audio_stream.close()
            logger.info('Releasing PortAudio resources.')
            py_audio.terminate()
            if os.environ.get('called_by_offline'):
                del os.environ['called_by_offline']
            else:
                exit_process()
                terminator()


def size_converter(byte_size: int) -> str:
    """Gets the current memory consumed and converts it to human friendly format.

    Args:
        byte_size: Receives byte size as argument.

    Returns:
        str:
        Converted understandable size.
    """
    if not byte_size:
        from resource import RUSAGE_SELF, getrusage
        byte_size = getrusage(RUSAGE_SELF).ru_maxrss
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    integer = int(floor(log(byte_size, 1024)))
    power = pow(1024, integer)
    size = round(byte_size / power, 2)
    return f'{size} {size_name[integer]}'


def exit_message() -> str:
    """Variety of exit messages based on day of week and time of day.

    Returns:
        str:
        A greeting bye message.
    """
    am_pm = datetime.now().strftime("%p")  # current part of day (AM/PM)
    hour = datetime.now().strftime("%I")  # current hour
    day = datetime.now().strftime("%A")  # current day

    if am_pm == 'AM' and int(hour) < 10:
        exit_msg = f"Have a nice day, and happy {day}."
    elif am_pm == 'AM' and int(hour) >= 10:
        exit_msg = f"Enjoy your {day}."
    elif am_pm == 'PM' and (int(hour) == 12 or int(hour) < 3) and day in weekend:
        exit_msg = "Have a nice afternoon, and enjoy your weekend."
    elif am_pm == 'PM' and (int(hour) == 12 or int(hour) < 3):
        exit_msg = "Have a nice afternoon."
    elif am_pm == 'PM' and int(hour) < 6 and day in weekend:
        exit_msg = "Have a nice evening, and enjoy your weekend."
    elif am_pm == 'PM' and int(hour) < 6:
        exit_msg = "Have a nice evening."
    elif day in weekend:
        exit_msg = "Have a nice night, and enjoy your weekend."
    else:
        exit_msg = "Have a nice night."

    if event := celebrate():
        exit_msg += f'\nAnd by the way, happy {event}'

    return exit_msg


def terminator() -> None:
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc.

    Using this, eliminates the hassle of forcing multiple threads to stop.
    """
    # noinspection PyUnresolvedReferences,PyProtectedMember
    os._exit(0)


def remove_files() -> None:
    """Function that deletes multiple files when called during exit operation.

    Warnings:
        Deletes:
            - all ``.lock`` files created for alarms and reminders.
            - ``location.yaml`` file, to recreate a new one next time around.
            - ``meetings`` file, to recreate a new one next time around.
    """
    [os.remove(f"alarm/{file}") for file in os.listdir('alarm') if file != '.keep']
    [os.remove(f"reminder/{file}") for file in os.listdir('reminder') if file != '.keep']
    os.remove('location.yaml') if os.path.isfile('location.yaml') else None
    os.remove('meetings') if os.path.isfile('meetings') else None


def exit_process() -> None:
    """Function that holds the list of operations done upon exit."""
    STOPPER['status'] = True
    logger.info('JARVIS::Stopping Now::STOPPER flag has been set to True')
    reminders = {}
    alarms = [file for file in os.listdir('alarm') if file != '.keep' and file != '.DS_Store']
    for file in os.listdir('reminder'):
        if file != '.keep' and file != '.DS_Store':
            split_val = file.replace('.lock', '').split('|')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        logger.info(f'JARVIS::Deleting Reminders - {reminders}')
        if len(reminders) == 1:
            speaker.say('You have a pending reminder sir!')
        else:
            speaker.say(f'You have {len(reminders)} pending reminders sir!')
        for key, value in reminders.items():
            speaker.say(f"{value.replace('_', ' ')} at "
                        f"{key.replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')}")
    if alarms:
        logger.info(f'JARVIS::Deleting Alarms - {alarms}')
        alarms = ', and '.join(alarms) if len(alarms) != 1 else ''.join(alarms)
        alarms = alarms.replace('.lock', '').replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')
        sys.stdout.write(f"\r{alarms}")
        speaker.say(f'You have a pending alarm at {alarms} sir!')
    if reminders or alarms:
        speaker.say('This will be removed while shutting down!')
    speaker.say('Shutting down now sir!')
    speaker.say(exit_message())
    try:
        speaker.runAndWait()
    except RuntimeError:
        logger.error(f'Received a RuntimeError while self terminating.\n{format_exc()}')
    remove_files()
    sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                     f"\nTotal runtime: {time_converter(perf_counter())}")


def extract_nos(input_: str) -> float:
    """Extracts number part from a string.

    Args:
        input_: Takes string as an argument.

    Returns:
        float:
        Float values.
    """
    return float('.'.join(re.findall(r"\d+", input_)))


def format_nos(input_: float) -> int:
    """Removes ``.0`` float values.

    Args:
        input_: Int if found, else returns the received float value.

    Returns:
        int:
        Formatted integer.
    """
    return int(input_) if isinstance(input_, float) and input_.is_integer() else input_


def extract_str(input_: str) -> str:
    """Extracts strings from the received input.

    Args:
        input_: Takes a string as argument.

    Returns:
        str:
        A string after removing special characters.
    """
    return ''.join([i for i in input_ if not i.isdigit() and i not in [',', '.', '?', '-', ';', '!', ':']])


def host_info(required: str) -> Union[str, float]:
    """Gets both the model and version of the hosted device.

    Args:
        required: model or version

    Returns:
        str or float:
        Model or version of the machine based on the arg received.
    """
    device = (check_output("sysctl hw.model", shell=True)).decode('utf-8').split('\n')  # gets model info
    result = list(filter(None, device))[0]  # removes empty string ('\n')
    model = extract_str(result).strip('hwmodel ')
    version = extract_nos(''.join(device))
    if required == 'model':
        return model
    elif required == 'version':
        return version


def pc_sleep() -> None:
    """Locks the host device using osascript and reduces brightness to bare minimum."""
    Thread(target=decrease_brightness).start()
    # os.system("""osascript -e 'tell app "System Events" to sleep'""")  # requires restarting Jarvis manually
    os.system("""osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'""")
    if not (report.has_been_called or time_travel.has_been_called):
        speaker.say(choice(ack))


def stop_terminal() -> None:
    """Uses pid to kill terminals as terminals await user confirmation interrupting shutdown/restart."""
    pid_check = check_output("ps -ef | grep 'iTerm\\|Terminal'", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'Applications' in id_ and '/usr/bin/login' not in id_:
            os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout


# noinspection PyUnresolvedReferences,PyProtectedMember
def restart(target: str = None, quiet: bool = False, quick: bool = False) -> None:
    """Restart triggers ``restart.py`` which in turn starts Jarvis after 5 seconds.

    Notes:
        - Doing this changes the PID to avoid any Fatal Errors occurred by long running threads.
        - restart(PC) will restart the machine after getting confirmation.

    Warnings:
        - ``restart(target=!PC)`` will restart the machine without getting any approval as the confirmation is requested
            - in `system_vitals <https://thevickypedia.github.io/Jarvis/#jarvis.system_vitals>`__.
        - This is done only when the system vitals are read, and the uptime is more than 2 days.

    Args:
        target:
            - ``None``: Restarts Jarvis to reset PID
            - ``PC``: Restarts the machine after getting confirmation.
        quiet: If a boolean ``True`` is passed, a silent restart will be performed.
        quick:
            - If a boolean ``True`` is passed, local IP values are stored in ``.env`` file for quick re-use.
            - Converts ``hallway_ip``, ``bedroom_ip`` and ``kitchen_ip`` into a string before storing it as env vars.
            - Doesn't convert ``tv_ip`` as a string as it is already one.
    """
    offline = os.environ.get('called_by_offline')
    if target:
        if offline:
            logger.warning(f"ERROR::Cannot restart {host_info(required='model')} via offline communicator.")
            return
        if target == 'PC':
            speaker.say(f'{choice(confirmation)} restart your {host_info("model")}?')
            speaker.runAndWait()
            converted = listener(timeout=3, phrase_limit=3)
        else:
            converted = 'yes'
        if any(word in converted.lower() for word in keywords.ok()):
            stop_terminal()
            call(['osascript', '-e', 'tell app "System Events" to restart'])
            raise KeyboardInterrupt
        else:
            speaker.say("Machine state is left intact sir!")
            return
    STOPPER['status'] = True
    logger.info('JARVIS::Restarting Now::STOPPER flag has been set.')
    logger.info(f'Called by {sys._getframe(1).f_code.co_name}')
    sys.stdout.write(f"\rMemory consumed: {size_converter(0)}\tTotal runtime: {time_converter(perf_counter())}")
    if not quiet:
        try:
            speaker.say('Restarting now sir! I will be up and running momentarily.')
            speaker.runAndWait() if not offline else None
        except RuntimeError:
            logger.error(f'Received a RuntimeError while restarting.\n{format_exc()}')
    if quick:
        set_key(dotenv_path='.env', key_to_set='hallway_ip', value_to_set=str(hallway_ip)) if hallway_ip else None
        set_key(dotenv_path='.env', key_to_set='bedroom_ip', value_to_set=str(bedroom_ip)) if bedroom_ip else None
        set_key(dotenv_path='.env', key_to_set='kitchen_ip', value_to_set=str(kitchen_ip)) if kitchen_ip else None
        set_key(dotenv_path='.env', key_to_set='tv_ip', value_to_set=tv_ip) if tv_ip else None
        set_key(dotenv_path='.env', key_to_set='tv_mac', value_to_set=tv_mac) if tv_mac else None
    os.system('python3 restart.py')
    exit(1)  # Don't call terminator() as, os._exit(1) in that func will kill the background threads running in parallel


def shutdown(proceed: bool = False) -> None:
    """Gets confirmation and turns off the machine.

    Args:
        proceed: Boolean value whether or not to get confirmation.
    """
    if not proceed:
        speaker.say(f"{choice(confirmation)} turn off the machine?")
        speaker.runAndWait()
        converted = listener(timeout=3, phrase_limit=3)
    else:
        converted = 'yes'
    if converted != 'SR_ERROR':
        if any(word in converted.lower() for word in keywords.ok()):
            stop_terminal()
            call(['osascript', '-e', 'tell app "System Events" to shut down'])
            raise KeyboardInterrupt
        else:
            speaker.say("Machine state is left intact sir!")
            return


def voice_changer(change: str = None) -> None:
    """Defaults to a particular voice module.

    Alternatively the user can choose from a variety of voices available for that particular device.

    Args:
        change: Initiates changing voices with the volume ID given in statement.
    """
    alter_msg = 0
    voices = speaker.getProperty("voices")  # gets the list of voices available
    # noinspection PyTypeChecker,PyUnresolvedReferences
    avail_voices = len(voices)

    # noinspection PyUnresolvedReferences
    def voice_default(voice_id=(7, 0)) -> None:  # default values set as tuple
        """Sets default voice module number.

        Args:
            voice_id: Default voice ID.
        """
        speaker.setProperty("voice", voices[voice_id[0]].id)  # voice module #7 for MacOS

    if change:
        if not (distribution := [int(s) for s in re.findall(r'\b\d+\b', change)]):  # walrus on if not distribution
            distribution = range(avail_voices)
        for module_id in distribution:
            if module_id < avail_voices:
                voice_default([module_id])  # passing a list as default is tuple and index values are used to reference
                sys.stdout.write(f'\rVoice module has been re-configured to {module_id}')
                if not alter_msg:
                    speaker.say('Voice module has been re-configured sir! Would you like me to retain this?')
                    alter_msg = 1
                elif alter_msg == 1:
                    speaker.say("Here's an example of one of my other voices sir!. Would you like me to use this one?")
                    alter_msg = 2
                else:
                    speaker.say('How about this one sir?')
            else:
                speaker.say(f'The voice module number {module_id} is not available for your device sir! '
                            f'You may want to try a module number between 0 and {avail_voices - 1}')
            speaker.runAndWait()
            keyword = listener(timeout=3, phrase_limit=3)
            if keyword == 'SR_ERROR':
                voice_default()
                speaker.say("Sorry sir! I had trouble understanding. I'm back to my default voice.")
                return
            elif 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                voice_default()
                speaker.say('Reverting the changes to default voice module sir!')
                return
            elif any(word in keyword.lower() for word in keywords.ok()):
                speaker.say(choice(ack))
                return
            elif custom_id := [int(id_) for id_ in re.findall(r'\b\d+\b', keyword)]:
                voice_changer(str(custom_id))
                break
    else:
        voice_default()


def clear_logs() -> None:
    """Deletes log files that were updated before 48 hours."""
    [os.remove(f"logs/{file}") for file in os.listdir('logs') if file != '.keep' and
     int(datetime.now().timestamp()) - int(os.stat(f'logs/{file}').st_mtime) > 172_800]


def starter() -> None:
    """Initiates crucial functions which needs to be called during start up.

    - Loads the ``.env`` file so that all the necessary credentials and api keys can be accessed as ``ENV vars``

    Methods:
        volume_controller(): To default the master volume 50%.
        voice_changer(): To change the voice to default value.
        clear_logs(): To purge log files older than 48 hours.
    """
    volume_controller(level=50)
    voice_changer()
    clear_logs()
    meeting_app_launcher()

    if os.path.isfile('.env'):
        logger.info('Loading .env file.')
        load_dotenv(dotenv_path='.env', verbose=True, override=True)  # loads the .env file


if __name__ == '__main__':
    if system() != 'Darwin':
        exit('Unsupported Operating System.\nWindows support was recently deprecated. '
             'Refer https://github.com/thevickypedia/Jarvis/commit/cf54b69363440d20e21ba406e4972eb058af98fc')

    logger.info('JARVIS::Starting Now')

    sys.stdout.write('\rVoice ID::Female: 1/17 Male: 0/7')  # Voice ID::reference
    speaker = init()  # initiates speaker
    recognizer = Recognizer()  # initiates recognizer that uses google's translation
    keywords = Keywords()  # stores Keywords() class from helper_functions/keywords.py
    conversation = Conversation()  # stores Conversation() class from helper_functions/conversation.py
    database = Database()  # initiates Database() for TO-DO items
    temperature = Temperature()  # initiates Temperature() for temperature conversions
    personal_cloud = PersonalCloud()  # initiates PersonalCloud() to enable or disable HDD hosting
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 10)  # increases the recursion limit by 10 times
    home = os.path.expanduser('~')  # gets the path to current user profile

    meeting_file = 'calendar.scpt'
    starter()  # initiates crucial functions which needs to be called during start up

    git_user = os.environ.get('git_user')
    git_pass = os.environ.get('git_pass')
    weather_api = os.environ.get('weather_api')
    news_api = os.environ.get('news_api')
    maps_api = os.environ.get('maps_api')
    gmail_user = os.environ.get('gmail_user')
    gmail_pass = os.environ.get('gmail_pass')
    robinhood_user = os.environ.get('robinhood_user')
    robinhood_pass = os.environ.get('robinhood_pass')
    robinhood_qr = os.environ.get('robinhood_qr')
    birthday = os.environ.get('birthday')
    offline_receive_user = os.environ.get('offline_receive_user')
    offline_receive_pass = os.environ.get('offline_receive_pass')
    offline_phrase = os.environ.get('offline_phrase')
    icloud_user = os.environ.get('icloud_user')
    icloud_pass = os.environ.get('icloud_pass')
    icloud_recovery = os.environ.get('icloud_recovery')
    phone_number = os.environ.get('phone_number')
    think_id = os.environ.get('think_id')
    router_pass = os.environ.get('router_pass')
    tv_client_key = os.environ.get('tv_client_key')
    root_password = os.environ.get('root_password')

    if st := internet_checker():
        sys.stdout.write(f'\rINTERNET::Connected to {get_ssid()}. Scanning localhost for connected devices.')
    else:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet sir! Please check your connection settings and retry.")
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                         f"\nTotal runtime: {time_converter(perf_counter())}")
        terminator()

    # Retrieves devices IP by doing a local IP range scan using Netgear API
    # Note: This can also be done my manually passing the IP addresses in a list (for lights) or string (for TV)
    # Using Netgear API will avoid the manual change required to rotate the IPs whenever the router is restarted
    # noinspection is used since, variables declared after 'and' in walrus operator are recognized as unbound variables
    if (hallway_ip := os.environ.get('hallway_ip')) and (kitchen_ip := os.environ.get('kitchen_ip')) and \
            (bedroom_ip := os.environ.get('bedroom_ip')) and (tv_ip := os.environ.get('tv_ip')):
        hallway_ip = eval(hallway_ip)
        # noinspection PyUnboundLocalVariable
        kitchen_ip = eval(kitchen_ip)
        # noinspection PyUnboundLocalVariable
        bedroom_ip = eval(bedroom_ip)
        unset_key(dotenv_path='.env', key_to_unset='hallway_ip')
        unset_key(dotenv_path='.env', key_to_unset='kitchen_ip')
        unset_key(dotenv_path='.env', key_to_unset='bedroom_ip')
        unset_key(dotenv_path='.env', key_to_unset='tv_ip')
        unset_key(dotenv_path='.env', key_to_unset='tv_mac')
    else:
        local_devices = LocalIPScan(router_pass=router_pass)
        hallway_ip = [val for val in local_devices.hallway()]
        kitchen_ip = [val for val in local_devices.kitchen()]
        bedroom_ip = [val for val in local_devices.bedroom()]
        tv_ip, tv_mac = local_devices.tv()

    if not root_password:
        sys.stdout.write('\rROOT PASSWORD is not set!')

    # warm_light is initiated with an empty dict and the key status is set to True when requested to switch to yellow
    # greet_check is used in initialize() to greet only for the first run
    # tv is set to an empty dict instead of TV() at the start to avoid turning on the TV unnecessarily
    tv_state, warm_light, greet_check, STOPPER = {}, {}, {}, {}

    # stores necessary values for geo location to receive the latitude, longitude and address
    options.default_ssl_context = create_default_context(cafile=where())
    geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)

    # checks modified time of location.yaml (if exists) and uses the data only if it was modified less than 72 hours ago
    if os.path.isfile('location.yaml') and \
            int(datetime.now().timestamp()) - int(os.stat('location.yaml').st_mtime) < 259_200:
        location_details = yaml_load(open('location.yaml'), Loader=FullLoader)
        current_lat = location_details['latitude']
        current_lon = location_details['longitude']
        location_info = location_details['address']
        current_tz = location_details['timezone']
    else:
        current_lat, current_lon, location_info = location_services(device_selector())
        current_tz = str(TimezoneFinder().timezone_at(lat=current_lat, lng=current_lon))
        location_dumper = [{'timezone': current_tz}, {'latitude': current_lat}, {'longitude': current_lon},
                           {'address': location_info}]
        with open('location.yaml', 'w') as location_writer:
            for dumper in location_dumper:
                yaml_dump(dumper, location_writer, default_flow_style=False)

    # different responses for different conditions in sentry mode
    wake_up1 = ['For you sir! Always!', 'At your service sir!']
    wake_up2 = ['Up and running sir!', "We are online and ready sir!", "I have indeed been uploaded sir!",
                'My listeners have been activated sir!']
    wake_up3 = ["I'm here sir!"]

    confirmation = ['Requesting confirmation sir! Did you mean', 'Sir, are you sure you want to']
    ack = ['Check', 'Will do sir!', 'You got it sir!', 'Roger that!', 'Done sir!', 'By all means sir!', 'Indeed sir!',
           'Gladly sir!', 'Without fail sir!', 'Sure sir!', 'Buttoned up sir!', 'Executed sir!']

    weekend = ['Friday', 'Saturday']

    # {function_name}.has_been_called is use to denote which function has triggered the other
    report.has_been_called, locate_places.has_been_called, directions.has_been_called, google_maps.has_been_called, \
        time_travel.has_been_called = False, False, False, False, False
    for functions in [delete_todo, todo, add_todo]:
        functions.has_been_called = False

    sys.stdout.write(f"\rCurrent Process ID: {Process(os.getpid()).pid}\tCurrent Volume: 50%")

    if os.path.exists(f"{home}/JarvisHelper"):
        Thread(target=offline_communicator_initiate).start()
        Thread(target=offline_communicator).start()
    else:
        logger.error(f'Unable to initiate OfflineCommunicator since, JarvisHelper is unavailable in {home}')
    Thread(target=meeting_gatherer).start()
    Thread(target=playsound, args=['indicators/initialize.mp3']).start()

    with Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        Activator.run()
