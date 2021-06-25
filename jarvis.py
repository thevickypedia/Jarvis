import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email import message_from_bytes, message_from_string
from email.header import decode_header, make_header
from imaplib import IMAP4, IMAP4_SSL
from json import load as json_load
from json import loads as json_loads
from math import ceil, floor, log, pow
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from platform import platform, system, uname
from random import choice, choices, randrange
from shutil import disk_usage, rmtree
from smtplib import SMTP
from socket import (AF_INET, SOCK_DGRAM, gaierror, gethostbyname, gethostname,
                    setdefaulttimeout, socket)
from socket import timeout as s_timeout
from ssl import create_default_context
from string import ascii_letters, digits
from subprocess import (PIPE, CalledProcessError, Popen, call, check_output,
                        getoutput)
from threading import Thread
from time import perf_counter, sleep, time
from traceback import format_exc
from unicodedata import normalize
from urllib.request import urlopen
from webbrowser import open as web_open

from appscript import app as apple_script
from boto3 import client
from certifi import where
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from googlehomepush import GoogleHome
from googlehomepush.http_server import serve_file
from holidays import CountryHoliday
from inflect import engine
from joke.jokes import chucknorris, geek, icanhazdad, icndb
from newsapi import NewsApiClient, newsapi_exception
from playsound import playsound
from psutil import Process, boot_time, cpu_count, virtual_memory
from pychromecast.error import ChromecastConnectionError
from PyDictionary import PyDictionary
from pyicloud import PyiCloudService
from pyicloud.exceptions import (PyiCloudAPIResponseException,
                                 PyiCloudFailedLoginException)
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
from yaml import Loader
from yaml import dump as yaml_dump
from yaml import load as yaml_load

from helper_functions.alarm import Alarm
from helper_functions.aws_clients import AWSClients
from helper_functions.conversation import Conversation
from helper_functions.database import Database, file_name
from helper_functions.emailer import Emailer
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


def listener(timeout: int, phrase_limit: int):
    """Function to activate listener, this function will be called by most upcoming functions to listen to user input.

    Args:
        timeout: Time in seconds for the overall listener to be active.
        phrase_limit: Time in seconds for the listener to actively listen to a sound.

    Returns:
         On success, returns recognized statement from the microphone.
         On failure, returns 'SR_ERROR' as a string which is conditioned to respond appropriately.

    """
    try:
        sys.stdout.write("\rListener activated..") and playsound('indicators/start.mp3')
        listened = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        sys.stdout.write("\r") and playsound('indicators/end.mp3')
        return_val = recognizer.recognize_google(listened)
        sys.stdout.write(f'\r{return_val}')
    except (UnknownValueError, RequestError, WaitTimeoutError):
        return_val = 'SR_ERROR'
    return return_val


def split(key: str):
    """Splits the input at 'and' or 'also' and makes it multiple commands to execute if found in statement.

    Args:
        key: Takes the voice recognized statement as argument.

    Returns:
        Return value from conditions()

    """
    exit_check = False  # this is specifically to catch the sleep command which should break the while loop in renew()
    if ' and ' in key and not any(word in key.lower() for word in keywords.avoid()):
        for each in key.split(' and '):
            exit_check = conditions(each.strip())
    elif ' also ' in key and not any(word in key.lower() for word in keywords.avoid()):
        for each in key.split(' also '):
            exit_check = conditions(each.strip())
    else:
        exit_check = conditions(key.strip())
    return exit_check


def greeting():
    """Checks the current hour to determine the part of day.

    Returns:
        Morning, Afternoon, Evening or Night based on time of day.

    """
    am_or_pm = datetime.now().strftime("%p")
    current_hour = int(datetime.now().strftime("%I"))
    if current_hour in range(4, 12) and am_or_pm == 'AM':
        greet = 'Morning'
    elif am_or_pm == 'PM' and (current_hour == 12 or current_hour in range(1, 4)):
        greet = 'Afternoon'
    elif current_hour in range(4, 8) and am_or_pm == 'PM':
        greet = 'Evening'
    else:
        greet = 'Night'
    return greet


def initialize():
    """Awakens from sleep mode. greet_check is to ensure greeting is given only for the first function call."""
    global greet_check
    if greet_check:
        speaker.say("What can I do for you?")
    else:
        speaker.say(f'Good {greeting()}.')
        greet_check = 'initialized'
    renew()


def renew():
    """Keeps listening and sends the response to conditions() function.

    This function runs only for a minute and goes to sentry_mode() if nothing is heard.
    split(converted) is a condition so that, loop breaks when if sleep in conditions() returns True.
    """
    speaker.runAndWait()
    waiter = 0
    while waiter < 12:
        waiter += 1
        try:
            sys.stdout.write("\rListener activated..") and playsound('indicators/start.mp3') if waiter == 1 else \
                sys.stdout.write("\rListener activated..")
            listen = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('indicators/end.mp3') if waiter == 0 else sys.stdout.write("\r")
            converted = recognizer.recognize_google(listen)
            remove = ['buddy', 'jarvis', 'hey', 'hello']
            converted = ' '.join([i for i in converted.split() if i.lower() not in remove])
            if not converted or 'you there' in converted:
                speaker.say(choice(wake_up3))
            else:
                if split(converted):
                    break  # split() returns what conditions function returns. Condition() returns True only for sleep.
            speaker.runAndWait()
            waiter = 0
        except (UnknownValueError, RequestError, WaitTimeoutError):
            pass


def time_converter(seconds: float):
    """Modifies seconds to appropriate days/hours/minutes/seconds.

    Args:
        seconds: Takes number of seconds as argument.

    Returns:
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


def conditions(converted: str):
    """Conditions function is used to check the message processed.

    Uses the keywords to do a regex match and trigger the appropriate function which has dedicated task.

    Args:
        converted: Takes the voice recognized statement as argument.

    Returns:
        Boolean True only when asked to sleep for conditioned sleep message.

    """
    sys.stdout.write(f'\r{converted}')
    converted_lower = converted.lower()
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
        if place:
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
                return
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
            ip_address = vpn_checker().replace('VPN::', '')
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

    elif any(word in converted_lower for word in keywords.delete_todo()):
        delete_todo()

    elif any(word in converted_lower for word in keywords.list_todo()):
        todo()

    elif any(word in converted_lower for word in keywords.add_todo()):
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
        if operating_system == 'Darwin':
            bluetooth(phrase=converted_lower)
        elif operating_system == 'Windows':
            speaker.say("Bluetooth connectivity on Windows hasn't been developed sir!")

    elif any(word in converted_lower for word in keywords.brightness()) and 'lights' not in converted_lower:
        if operating_system == 'Darwin':
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
        elif operating_system == 'Windows':
            speaker.say("Modifying screen brightness on Windows hasn't been developed sir!")

    elif any(word in converted_lower for word in keywords.lights()):
        connection_status = vpn_checker()
        if not connection_status.startswith('VPN'):
            lights(converted=converted_lower)

    elif any(word in converted_lower for word in keywords.guard_enable() or keywords.guard_disable()):
        if any(word in converted_lower for word in keywords.guard_enable()):
            logger.critical('Enabled Security Mode')
            speaker.say(f"Enabled security mode sir! I will look out for potential threats and keep you posted. "
                        f"Have a nice {greeting()}, and enjoy yourself sir!")
            speaker.runAndWait()
            guard()

    elif any(word in converted_lower for word in keywords.flip_a_coin()):
        playsound('indicators/coin.mp3')
        sleep(0.5)
        speaker.say(f"""{choice(['You got', 'It landed on', "It's"])} {choice(['heads', 'tails'])} sir""")

    elif any(word in converted_lower for word in keywords.facts()):
        speaker.say(getFact(False))

    elif any(word in converted_lower for word in keywords.meetings()):
        if not os.path.isfile('meetings'):
            meeting = ThreadPool(processes=1).apply_async(func=meetings)
            speaker.say("Please give me a moment sir! Let me check your calendar.")
            speaker.runAndWait()
            try:
                speaker.say(meeting.get(timeout=60))
            except ThreadTimeoutError:
                speaker.say("I wasn't able to read your calendar within the set time limit sir!")
            speaker.runAndWait()
        else:
            meeting_reader()

    elif any(word in converted_lower for word in keywords.voice_changer()):
        voice_changer(converted)

    elif any(word in converted_lower for word in keywords.system_vitals()):
        system_vitals()

    elif any(word in converted_lower for word in keywords.personal_cloud()):
        if operating_system == 'Windows':
            speaker.say("Personal cloud integration on Windows hasn't been developed yet sir!")
            return
        elif 'enable' in converted_lower or 'initiate' in converted_lower or 'kick off' in converted_lower or \
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
        if ('pc' in converted_lower or 'computer' in converted_lower or 'imac' in converted_lower or 'screen' in
                converted_lower) and operating_system == 'Darwin':
            pc_sleep()
        else:
            speaker.say("Activating sentry mode, enjoy yourself sir!")
        return True

    elif any(word in converted_lower for word in keywords.restart()):
        if 'pc' in converted_lower or 'computer' in converted_lower or 'imac' in converted_lower:
            restart(target='PC')
        else:
            restart()

    elif any(word in converted_lower for word in keywords.kill()) and \
            not any(word in converted_lower for word in keywords.avoid()):
        exit_process()
        terminator()

    elif any(word in converted_lower for word in keywords.shutdown()):
        shutdown()

    elif any(word in converted_lower for word in keywords.chatbot()):
        chatter_bot()

    else:
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


def unrecognized_dumper(converted: str):
    """If none of the conditions are met, converted text is written to a yaml file.

    Note that Jarvis will still try to get results from google wolfram alpha and google.

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


def location_services(device: str):
    """Initiates geo_locator and stores current location info as json so it could be used in couple of other functions.

    Args:
        device: Passed when locating a particular apple device.

    Returns:
        On success, returns current latitude, current longitude and location information as a dict.
        On failure, calls the return function or returns None.

    """
    try:
        # tries with icloud api to get your device's location for precise location services
        if not device:
            device = device_selector()
        raw_location = device.location()
        if not raw_location and place_holder == 'Apple':
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
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet. Please check your connection settings and retry.")
        speaker.runAndWait()
        return exit(1)

    try:
        # Uses the latitude and longitude information and converts to the required address.
        locator = geo_locator.reverse(f'{current_lat_}, {current_lon_}', language='en')
        location_info_ = locator.raw['address']
    except (GeocoderUnavailable, GeopyError):
        speaker.say('Received an error while retrieving your address sir! I think a restart should fix this.')
        return restart()

    return current_lat_, current_lon_, location_info_


def report():
    """Initiates a list of function that I tend to check first thing in the morning."""
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


def current_date():
    """Says today's date and adds the current time in speaker queue if report or time_travel function was called."""
    dt_string = datetime.now().strftime("%A, %B")
    date_ = engine().ordinal(datetime.now().strftime("%d"))
    year = datetime.now().strftime("%Y")
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


def current_time(place: str = None):
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


def webpage(target):
    """Opens up a webpage using your default browser to the target host.

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
        global place_holder
        speaker.say("Which website shall I open sir?")
        speaker.runAndWait()
        converted = listener(3, 4)
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
            if place_holder == 0:
                place_holder = None
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                webpage(None)
        place_holder = None
    else:
        for web in host:
            web_url = f"https://{web}"
            web_open(web_url)
        speaker.say(f"I have opened {host}")


def weather(place: str = None):
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
                     f'(which is {wind_speed} miles per hour), it feels like {temp_feel_f}°. {weather_suggest}.'
        else:
            output = f'The weather in {city} is a {feeling} {temp_f}°, and it currently feels like {temp_feel_f}°. ' \
                     f'{weather_suggest}.'
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


def weather_condition(msg: str, place: str = None):
    """Weather report when phrase has conditions like tomorrow, day after, next week and specific part of the day etc.

    weather_condition() uses conditional blocks to fetch keywords and determine the output.

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


def system_info():
    """Gets your system configuration for both mac and windows."""
    total, used, free = disk_usage("/")
    total = size_converter(total)
    used = size_converter(used)
    free = size_converter(free)
    ram = size_converter(virtual_memory().total).replace('.0', '')
    ram_used = size_converter(virtual_memory().percent).replace(' B', ' %')
    physical = cpu_count(logical=False)
    logical = cpu_count(logical=True)
    if operating_system == 'Windows':
        o_system = uname()[0] + uname()[2]
    elif operating_system == 'Darwin':
        o_system = (platform()).split('.')[0]
    else:
        o_system = None
    sys_config = f"You're running {o_system}, with {physical} physical cores and {logical} logical cores. " \
                 f"Your physical drive capacity is {total}. You have used up {used} of space. Your free space is " \
                 f"{free}. Your RAM capacity is {ram}. You are currently utilizing {ram_used} of your memory."
    sys.stdout.write(f'\r{sys_config}')
    speaker.say(sys_config)


def wikipedia_():
    """Gets any information from wikipedia using it's API."""
    global place_holder
    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
    keyword = listener(3, 5)
    if keyword == 'SR_ERROR':
        if place_holder == 0:
            place_holder = None
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            wikipedia_()
    else:
        place_holder = None
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
                keyword1 = listener(3, 5)
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
            response = listener(3, 3)
            if response != 'SR_ERROR':
                place_holder = None
                if any(word in response.lower() for word in keywords.ok()):
                    speaker.say('. '.join(result.split('. ')[3:-1]))
            else:
                sys.stdout.write("\r")
                speaker.say("I'm sorry sir, I didn't get your response.")


def news():
    """Says news around you."""
    news_source = 'fox'
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
        speaker.say("That's the end of news around you.")

    if report.has_been_called or time_travel.has_been_called:
        speaker.runAndWait()


def apps(keyword: str or None):
    """Launches an application skimmed from your statement and unable to skim asks for the app name.

    Args:
        keyword: Gets app name as an argument to launch the application.

    """
    global place_holder
    ignore = ['app', 'application']
    if not keyword or keyword in ignore:
        speaker.say("Which app shall I open sir?")
        speaker.runAndWait()
        keyword = listener(3, 4)
        if keyword != 'SR_ERROR':
            if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                return
        else:
            if place_holder == 0:
                place_holder = None
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                apps(None)
        place_holder = None

    if operating_system == 'Windows':
        status = os.system(f'start {keyword}')
        if status == 0:
            speaker.say(f'I have opened {keyword}')
        else:
            speaker.say(f"I did not find the app {keyword}. Try again.")
            apps(None)
    elif operating_system == 'Darwin':
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
            apps(None)
        else:
            app_status = os.system(f"open /Applications/'{keyword}' > /dev/null 2>&1")
            keyword = keyword.replace('.app', '')
            if app_status == 256:
                speaker.say(f"I'm sorry sir! I wasn't able to launch {keyword}. "
                            f"You might need to check its permissions.")
            else:
                speaker.say(f"I have opened {keyword}")


def robinhood():
    """Gets investment from robinhood API."""
    sys.stdout.write('\rGetting your investment details.')
    rh = Robinhood()
    rh.login(username=robin_user, password=robin_pass, qr_code=robin_qr)
    raw_result = rh.positions()
    result = raw_result['results']
    stock_value = RobinhoodGatherer().watcher(rh, result)
    sys.stdout.write(f'\r{stock_value}')
    speaker.say(stock_value)
    speaker.runAndWait()
    sys.stdout.write("\r")


def repeater():
    """Repeats what ever you say."""
    global place_holder
    speaker.say("Please tell me what to repeat.")
    speaker.runAndWait()
    keyword = listener(3, 10)
    if keyword != 'SR_ERROR':
        sys.stdout.write(f'\r{keyword}')
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            pass
        else:
            speaker.say(f"I heard {keyword}")
    else:
        if place_holder == 0:
            place_holder = None
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            repeater()


def chatter_bot():
    """Initiates chatter bot."""
    global place_holder
    file1 = 'db.sqlite3'
    if operating_system == 'Darwin':
        file2 = f"/Users/{os.environ.get('USER')}/nltk_data"
    elif operating_system == 'Windows':
        file2 = f"{os.environ.get('APPDATA')}\\nltk_data"
    else:
        file2 = None
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
    keyword = listener(3, 5)
    if keyword != 'SR_ERROR':
        place_holder = None
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
    else:
        if place_holder == 0:
            place_holder = None
            os.system('rm db* > /dev/null 2>&1')
            os.system(f'rm -rf {file2}')
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            chatter_bot()


def device_selector(converted: str = None):
    """Selects a device using the received input string.

    Args:
        converted: Takes the voice recognized statement as argument.

    Returns:
        Returns the device name from the user's input after checking the apple devices list.
        Returns your default device when not able to find it.

    """
    if converted and isinstance(converted, str):
        converted = converted.lower().replace('port', 'pods').replace('10', 'x').strip()
        target = re.search('iphone(.*)|imac(.*)', converted)  # name of the apple device to be tracked (eg: iPhone X)
        if target:
            lookup = target.group()
        elif 'macbook' in converted:
            lookup = 'MacBook Pro'
        elif 'airpods' in converted:
            lookup = 'AirPods'
        elif 'airpods pro' in converted:
            lookup = 'AirPods Pro'
        elif 'watch' in converted:
            lookup = 'Apple Watch'
        else:
            lookup = 'iPhone 11 Pro Max'  # defaults to my iPhone model
    elif isinstance(converted, dict):
        lookup = converted
    elif not converted:
        lookup = gethostname()
    else:
        lookup = 'iPhone 11 Pro Max'
    index, target_device = -1, None
    icloud_api = PyiCloudService(icloud_user, icloud_pass)
    for device in icloud_api.devices:
        index += 1
        # todo: use regex or close_matches to find the precise device and remove the abuse of converted
        if lookup.lower() in str(device).lower():
            target_device = icloud_api.devices[index]
            break
    if not target_device:
        target_device = icloud_api.iphone
    return target_device


def location():
    """Gets your current location."""
    city, state, country = location_info['city'], location_info['state'], location_info['country']
    speaker.say(f"You're at {city} {state}, in {country}")


def locate(converted: str):
    """Locates your iPhone using icloud api for python.

    Args:
        converted: Takes the voice recognized statement as argument and extracts device name from it.

    """
    global place_holder
    target_device = device_selector(converted)
    sys.stdout.write(f"\rLocating your {target_device}")
    if place_holder == 0:
        speaker.say("Would you like to get the location details?")
    else:
        target_device.play_sound()
        before_keyword, keyword, after_keyword = str(target_device).partition(':')  # partitions the hostname info
        speaker.say(f"Your {before_keyword} should be ringing now sir!")
        speaker.runAndWait()
        speaker.say("Would you like to get the location details?")
    speaker.runAndWait()
    phrase = listener(3, 3)
    if phrase == 'SR_ERROR':
        if place_holder == 0:
            place_holder = None
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            locate(converted)
    else:
        place_holder = None
        if any(word in phrase.lower() for word in keywords.ok()):
            place_holder = 'Apple'
            ignore_lat, ignore_lon, location_info_ = location_services(target_device)
            place_holder = None
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
            phrase = listener(3, 3)
            if any(word in phrase.lower() for word in keywords.ok()):
                message = 'Return my phone immediately.'
                target_device.lost_device(recovery, message)
                speaker.say("I've enabled lost mode on your phone.")
            else:
                speaker.say("No action taken sir!")


def music(device: str = None):
    """Scans music directory in your profile for .mp3 files and plays using default player.

    Args:
        device: Takes device name as argument.

    """
    sys.stdout.write("\rScanning music files...")

    if operating_system == 'Darwin':
        path = os.walk(f"{home_dir}/Music")
    elif operating_system == 'Windows':
        path = os.walk(f"{home_dir}\\Music")
    else:
        path = None

    get_all_files = (os.path.join(root, f) for root, _, files in path for f in files)
    get_music_files = (f for f in get_all_files if os.path.splitext(f)[1] == '.mp3')
    file = []
    for music_file in get_music_files:
        file.append(music_file)
    chosen = choice(file)

    if device:
        google_home(device, chosen)
    else:
        if operating_system == 'Darwin':
            call(["open", chosen])
        elif operating_system == 'Windows':
            os.system(f'start wmplayer "{chosen}"')
        sys.stdout.write("\r")
        speaker.say("Enjoy your music sir!")
        speaker.runAndWait()
        return


def gmail():
    """Reads unread emails from your gmail account for which the credentials are stored in env variables."""
    global place_holder
    sys.stdout.write("\rFetching new emails..")

    try:
        mail = IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(gmail_user, gmail_pass)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError as TimeOut:
        logger.error(TimeOut)
        speaker.say("I wasn't able to check your emails sir. You might need to check to logs.")
        speaker.runAndWait()
        return

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')  # looks for unread emails
    if return_code == 'OK':
        n = len(messages[0].split())
    else:
        speaker.say("I'm unable access your email sir.")
    if n == 0:
        speaker.say("You don't have any emails to catch up sir")
        speaker.runAndWait()
    else:
        speaker.say(f'You have {n} unread emails sir. Do you want me to check it?')  # user check before reading subject
        speaker.runAndWait()
        response = listener(3, 3)
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
                            sys.stdout.write(f'\rReceived:{receive}\tSender: {sender}\tSubject: {subject}')
                            speaker.say(f"You have an email from, {sender}, with subject, {subject}, {receive}")
                            speaker.runAndWait()
        else:
            if place_holder == 0:
                place_holder = None
            elif report.has_been_called or time_travel.has_been_called:
                pass
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                gmail()

        place_holder = None


def meaning(keyword: str or None):
    """Gets meaning for a word skimmed from your statement using PyDictionary.

    Args:
        keyword: Takes a keyword as argument for which the meaning was requested.

    """
    global place_holder
    dictionary = PyDictionary()
    if keyword == 'word':
        keyword = None
    if keyword is None:
        speaker.say("Please tell a keyword.")
        speaker.runAndWait()
        response = listener(3, 3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.exit()):
                return
            else:
                meaning(response)
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                meaning(None)
        place_holder = None
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
            speaker.say(f'Do you wanna know how {keyword} is spelled?')
            speaker.runAndWait()
            response = listener(3, 3)
            if any(word in response.lower() for word in keywords.ok()):
                for letter in list(keyword.lower()):
                    speaker.say(letter)
                speaker.runAndWait()
        else:
            speaker.say("Keyword should be a single word sir! Try again")
            meaning(None)
    return


def create_db():
    """Creates a database for to-do list by calling the create_db function in database module."""
    speaker.say(database.create_db())
    if todo.has_been_called:
        todo.has_been_called = False
        todo()
    elif add_todo.has_been_called:
        add_todo.has_been_called = False
        add_todo()
    return


def todo():
    """Says the item and category stored in your to-do list."""
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name) and (time_travel.has_been_called or report.has_been_called):
        pass
    elif not os.path.isfile(file_name):
        if place_holder == 0:
            speaker.say("Would you like to create a database for your to-do list?")
        else:
            speaker.say("You don't have a database created for your to-do list sir. Would you like to spin up one now?")
        speaker.runAndWait()
        key = listener(3, 3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok()):
                todo.has_been_called = True
                sys.stdout.write("\r")
                create_db()
            else:
                return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                todo()
        place_holder = None
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


def add_todo():
    """Adds new items to your to-do list."""
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    # if database file is not found calls create_db()
    if not os.path.isfile(file_name):
        sys.stdout.write("\r")
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
        key = listener(3, 3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok()):
                add_todo.has_been_called = True
                sys.stdout.write("\r")
                create_db()
            else:
                return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                add_todo()
        place_holder = None
    place_holder = None
    speaker.say("What's your plan sir?")
    speaker.runAndWait()
    item = listener(3, 5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            speaker.say('Your to-do list has been left intact sir.')
        else:
            sys.stdout.write(f"\rItem: {item}")
            speaker.say(f"I heard {item}. Which category you want me to add it to?")
            speaker.runAndWait()
            category = listener(3, 3)
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
                category_continue = listener(3, 3)
                if any(word in category_continue.lower() for word in keywords.ok()):
                    add_todo()
                else:
                    speaker.say('Alright')
    else:
        sys.stdout.write("\r")
        speaker.say("I didn't quite get that.")
    place_holder = None


def delete_todo():
    """Deletes items from an existing to-do list."""
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name):
        speaker.say("You don't have a database created for your to-do list sir.")
        return
    speaker.say("Which one should I remove sir?")
    speaker.runAndWait()
    item = listener(3, 5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            return
        response = database.deleter(item)
        # if the return message from database starts with 'Looks' it means that the item wasn't matched for deletion
        if response.startswith('Looks'):
            sys.stdout.write(f'\r{response}')
            speaker.say(response)
            speaker.runAndWait()
            delete_todo()
        else:
            speaker.say(response)
    else:
        if place_holder == 0:
            place_holder = None
            return
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            delete_todo()
    place_holder = None


def delete_db():
    """Deletes your database file after getting confirmation."""
    global place_holder
    if not os.path.isfile(file_name):
        speaker.say('I did not find any database sir.')
        return
    else:
        speaker.say(f'{choice(confirmation)} delete your database?')
        speaker.runAndWait()
        response = listener(3, 3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.ok()):
                os.remove(file_name)
                speaker.say("I've removed your database sir.")
            else:
                speaker.say("Your database has been left intact sir.")
            return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                speaker.runAndWait()
                place_holder = 0
                delete_db()
        place_holder = None


def distance(starting_point: str = None, destination: str = None):
    """Calculates distance between two locations.

    - If starting point is None, it gets the distance from your current location to destination.
    - If destination is None, it asks for a destination from the user.

    Args:
        starting_point: Takes the starting place name as an optional argument.
        destination: Takes the destination place name as optional argument.

    """
    global place_holder
    if not destination:
        speaker.say("Destination please?")
        speaker.runAndWait()
        destination = listener(3, 4)
        if destination != 'SR_ERROR':
            if len(destination.split()) > 2:
                speaker.say("I asked for a destination sir, not a sentence. Try again.")
                distance()
            if 'exit' in destination or 'quit' in destination or 'Xzibit' in destination:
                return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                distance()
        place_holder = None

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


def locate_places(place: str or None):
    """Gets location details of a place.

    Args:
        place: Takes a place name as argument.

    """
    global place_holder
    if not place:
        speaker.say("Tell me the name of a place!")
        speaker.runAndWait()
        converted = listener(3, 4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                place_holder = None
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
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                locate_places(place=None)
        place_holder = None
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
        locate_places.has_been_called = True
    except (TypeError, AttributeError):
        speaker.say(f"{place} is not a real place on Earth sir! Try again.")
        locate_places(place=None)
    distance(starting_point=None, destination=place)


def directions(place: str or None):
    """Opens google maps for a route between starting and destination.

    Uses reverse geocoding to calculate latitude and longitude for both start and destination.

    Args:
        place: Takes a place name as argument.

    """
    global place_holder
    if not place:
        speaker.say("You might want to give a location.")
        speaker.runAndWait()
        converted = listener(3, 4)
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
                place_holder = None
                return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                directions(place=None)
        place_holder = None
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


def alarm(msg: str):
    """Passes hour, minute and am/pm to Alarm class which initiates a thread for alarm clock in the background.

    Args:
        msg: Takes the voice recognized statement as argument and extracts time from it.

    """
    global place_holder
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', msg) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', msg)
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
        speaker.runAndWait()
        converted = listener(3, 4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                place_holder = None
                return
            else:
                alarm(converted)
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                alarm(msg='')
        place_holder = None
    return


def kill_alarm():
    """Removes lock file to stop the alarm which rings only when the certain lock file is present.

    Note: alarm_state is the list of lock files currently present.

    """
    global place_holder
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
        converted = listener(3, 4)
        if converted != 'SR_ERROR':
            place_holder = None
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
            if f'{hour}_{minute}_{am_pm}.lock' in os.listdir('alarm'):
                os.remove(f"alarm/{hour}_{minute}_{am_pm}.lock")
                speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
            else:
                speaker.say(f"I wasn't able to find an alarm at {hour}:{minute} {am_pm}. Try again.")
                kill_alarm()
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                kill_alarm()
    return


def google_home(device: str = None, file: str = None):
    """Uses socket lib to extract ip address and scans ip range for google home devices and play songs in your local.

    - Can also play music on multiple devices at once.
    - Changes made to google-home-push module:
    - 1. Modified the way local IP is received: https://github.com/deblockt/google-home-push/pull/7
    - 2. Instead of commenting/removing the final print statement on: site-packages/googlehomepush/__init__.py
    - I have used "sys.stdout = open(os.devnull, 'w')" to suppress any print statements.
    - To enable this again at a later time use "sys.stdout = sys.__stdout__"
    - Note: When music is played and immediately stopped/tasked the google home device, it is most likely to except
    - Broken Pipe error. This usually happens when you write to a socket that is fully closed.
    - This error occurs when one end of the connection tries sending data while the other end has closed the connection.
    - This can simply be ignored or handled using the below in socket module (NOT PREFERRED).

    `except IOError as error:`
        `import errno`
            `if error.errno != errno.EPIPE:`
                `sys.stdout.write(error)`

    Args:
        device: Name of the google home device on which the music has to be played.
        file: Scanned audio file to be played.

    """
    network_id = vpn_checker()
    if network_id.startswith('VPN'):
        return

    speaker.say('Scanning your IP range for Google Home devices sir!')
    sys.stdout.write('\rScanning your IP range for Google Home devices..')
    speaker.runAndWait()
    network_id = '.'.join(network_id.split('.')[0:3])

    def ip_scan(host_id: int):
        """Scans the IP range using the received args as host id in an IP address.

        Args:
            host_id: Host ID passed in a multi-threaded fashion to scan for google home devices in IP range.

        Returns:
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
    with ThreadPoolExecutor(max_workers=5000) as executor:  # max workers set to 5K (to scan 255 IPs) for less wait time
        for info in executor.map(ip_scan, range(1, 256)):  # scans host IDs 1 to 255 (eg: 192.168.1.1 to 192.168.1.255)
            devices.append(info)  # this includes all the NoneType values returned by unassigned host IDs
    devices = dict([i for i in devices if i])  # removes None values and converts list to dictionary of name and ip pair

    if not device or not file:
        sys.stdout.write("\r")

        def comma_separator(list_):
            """Separates commas using simple .join() function and analysis based on length of the list (args).

            Args:
                list_: Take a list of elements as an argument.

            Returns:
                Comma separated list of elements.

            """
            return ', and '.join([', '.join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_)

        speaker.say(f"You have {len(devices)} devices in your IP range sir! {comma_separator(list(devices.keys()))}. "
                    f"You can choose one and ask me to play some music on any of these.")
        return
    else:
        chosen = []
        [chosen.append(value) for key, value in devices.items() if key.lower() in device.lower()]
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


def jokes():
    """Uses jokes lib to say chucknorris jokes."""
    global place_holder
    speaker.say(choice([geek, icanhazdad, chucknorris, icndb])())
    speaker.runAndWait()
    speaker.say("Do you want to hear another one sir?")
    speaker.runAndWait()
    converted = listener(3, 3)
    if converted != 'SR_ERROR':
        place_holder = None
        if any(word in converted.lower() for word in keywords.ok()):
            jokes()
    return


def reminder(converted: str):
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder.

    Args:
        converted: Takes the voice recognized statement as argument and extracts the time and message from it.

    """
    global place_holder
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
        speaker.say("When do you want to be reminded sir?")
        speaker.runAndWait()
        converted = listener(3, 4)
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


def google_maps(query: str):
    """Uses google's places api to get places near by or any particular destination.

    This function is triggered when the words in user's statement doesn't match with any predefined functions.

    Args:
        query: Takes the voice recognized statement as argument.

    Returns:
        Boolean True is google's maps API is unable to fetch consumable results.

    """
    global place_holder
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
        converted = listener(3, 3)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                break
            elif any(word in converted.lower() for word in keywords.ok()):
                place_holder = None
                maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
                web_open(maps_url)
                speaker.say("Directions on your screen sir!")
                return
            elif results == 1:
                return
            elif n == results:
                speaker.say("I've run out of options sir!")
                return
            else:
                continue
        else:
            google_maps.has_been_called = True
            return


def notes():
    """Listens to the user and saves everything to a notes.txt file."""
    global place_holder
    converted = listener(5, 10)
    if converted != 'SR_ERROR':
        if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
            return
        else:
            with open(r'notes.txt', 'a') as writer:
                writer.write(f"{datetime.now().strftime('%A, %B %d, %Y')}\n{datetime.now().strftime('%I:%M %p')}\n"
                             f"{converted}\n")
    else:
        if place_holder == 0:
            place_holder = None
            return
        else:
            place_holder = 0
            notes()


def github(target: list):
    """Clones the github repository matched with existing repository in conditions function.

    Asks confirmation if the results are more than 1 but less than 3 else asks to be more specific.

    Args:
        target: Takes repository name as argument which has to be cloned.

    """
    global place_holder
    if len(target) == 1:
        os.system(f"""cd {home_dir} && git clone -q {target[0]}""")
        cloned = target[0].split('/')[-1].replace('.git', '')
        speaker.say(f"I've cloned {cloned} on your home directory sir!")
        return
    elif len(target) <= 3:
        newest = []
        [newest.append(new.split('/')[-1]) for new in target]
        sys.stdout.write(f"\r{', '.join(newest)}")
        speaker.say(f"I found {len(target)} results. On your screen sir! Which one shall I clone?")
        speaker.runAndWait()
        converted = listener(3, 5)
        if converted != 'SR_ERROR':
            if any(word in converted.lower() for word in keywords.exit()):
                place_holder = None
                return
            place_holder = None
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
            os.system(f"""cd {home_dir} && git clone -q {target[item]}""")
            cloned = target[item].split('/')[-1].replace('.git', '')
            speaker.say(f"I've cloned {cloned} on your home directory sir!")
            return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                github(target)
    else:
        speaker.say(f"I found {len(target)} repositories sir! You may want to be more specific.")
        return


def notify(user: str, password: str, number: int, body: str):
    """Send text message through SMS gateway of destination number.

    Args:
        user: Gmail username to authenticate SMTP lib.
        password: Gmail password to authenticate SMTP lib.
        number: Phone number stored as env var.
        body: Content of the message.

    """
    subject = "Message from Jarvis" if number == phone_number else "Jarvis::Message from Vignesh"
    body = body.encode('ascii', 'ignore').decode('ascii')  # ignore symbols like ° without throwing UnicodeEncodeError
    to = f"{number}@tmomail.net"
    message = (f"From: {user}\n" + f"To: {to}\n" + f"Subject: {subject}\n" + "\n\n" + body)
    server = SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user=user, password=password)
    server.sendmail(user, to, message)
    server.close()


def send_sms(number: int or None):
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        number: Phone number to which the message has to be sent.

    """
    global place_holder
    if not number:
        speaker.say("Please tell me a number sir!")
        speaker.runAndWait()
        number = listener(3, 5)
        if number != 'SR_ERROR':
            if 'exit' in number or 'quit' in number or 'Xzibit' in number:
                return
            else:
                sys.stdout.write(f'\rNumber: {number}')
                place_holder = None
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                send_sms(number=None)
    elif len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) != 10:
        sys.stdout.write(f'\r{number}')
        speaker.say("I don't think that's a right number sir! Phone numbers are 10 digits. Try again!")
        send_sms(number=None)
    if number and len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) == 10:
        speaker.say("What would you like to send sir?")
        speaker.runAndWait()
        body = listener(3, 5)
        if body == 'SR_ERROR':
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                send_sms(number)
        else:
            sys.stdout.write(f'\r{body}::to::{number}')
            speaker.say(f'{body} to {number}. Do you want me to proceed?')
            speaker.runAndWait()
            converted = listener(3, 3)
            if converted != 'SR_ERROR':
                if not any(word in converted.lower() for word in keywords.ok()):
                    speaker.say("Message will not be sent sir!")
                else:
                    notify(user=gmail_user, password=gmail_pass, number=number, body=body)
                    speaker.say("Message has been sent sir!")
                return
            else:
                if place_holder == 0:
                    place_holder = None
                    return
                else:
                    speaker.say("I didn't quite get that. Try again.")
                    place_holder = 0
                    send_sms(number)


def television(converted: str):
    """Controls all actions on a TV (LG Web OS).

    In the main() method tv is set to None. Given a command related to TV,
    Jarvis will try to ping the TV and then power it on if the host is unreachable. Then executes the said command.
    Once the tv is turned on, the TV class is also initiated and assigned to tv variable which is set global for
    other statements to use it.

    Args:
        converted: Takes the voice recognized statement as argument.

    """
    global tv
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
        try:
            arp_output = check_output(f"arp {tv_ip}", shell=True).decode('utf-8')  # arp on tv ip to get mac address
            tv_mac_address = re.search(' at (.*) on ', arp_output).group().replace(' at ', '').replace(' on ', '')
        except CalledProcessError:
            tv_mac_address = None
        if not tv_mac_address or tv_mac_address == '(INCOMPLETE)':
            tv_mac_address = os.environ.get('tv_mac') or aws.tv_mac()
        Thread(target=lambda mac_address: wake(mac_address), args=[tv_mac_address]).start()  # turns TV on in a thread
        speaker.say("Looks like your TV is powered off sir! Let me try to turn it back on!")
        speaker.runAndWait()  # speaks the message to buy some time while the TV is connecting to network

    if tv_status() != 0:  # checks if TV is reachable even before trying to launch the TV connector
        speaker.say("I wasn't able to connect to your TV sir! Please make sure you are on the "
                    "same network as your TV, and your TV is connected to a power source.")
        return

    if not tv:
        tv = TV(ip_address=tv_ip, client_key=tv_client_key)
        if 'turn on' in phrase or 'connect' in phrase:
            speaker.say("TV features have been integrated sir!")
            return

    if tv:
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
            tv = None
        else:
            speaker.say("I didn't quite get that.")
    else:
        converted = converted.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speaker.say(f"I'm sorry sir! I wasn't able to {converted}, as the TV state is unknown!")


def alpha(text: str):
    """Uses wolfram alpha API to fetch results for uncategorized phrases heard.

    Args:
        text: Takes the voice recognized statement as argument.

    Returns:
        Boolean True is wolfram alpha API is unable to fetch consumable results.

    """
    alpha_client = Think(app_id=think_id)
    res = alpha_client.query(text)
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


def google(query: str):
    """Uses Google's search engine parser and gets the first result that shows up on a google search.

    If it is unable to get the result, Jarvis sends a request to suggestqueries.google.com to rephrase
    the query and then looks up using the search engine parser once again. global suggestion_count is used
    to make sure the suggestions and parsing don't run on an infinite loop.

    Args:
        query: Takes the voice recognized statement as argument.

    Returns:
        Boolean True is google search engine is unable to fetch consumable results.

    """
    global suggestion_count
    search_engine = GoogleSearch()
    results = []
    try:
        google_results = search_engine.search(query, cache=False)
        a = {"Google": google_results}
        for k, v in a.items():
            for result in v:
                response = result['titles']
                results.append(response)
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
                suggestion_count = 0
                speaker.say(r.json()[1][0].replace('=', ''))  # picks the closest match and opens a google search
                speaker.runAndWait()
                return False
            else:
                google(suggestion)
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


def google_search(phrase: str or None):
    """Opens up a google search for the phrase received. If nothing was received, gets phrase from user.

    Args:
        phrase: Takes the voice recognized statement as argument.

    """
    global place_holder
    if not phrase:
        speaker.say("Please tell me the search phrase.")
        speaker.runAndWait()
        converted = listener(3, 5)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'xzibit' in converted or 'cancel' in converted:
                return
            else:
                phrase = converted.lower()
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                google_search(None)
    search = str(phrase).replace(' ', '+')
    unknown_url = f"https://www.google.com/search?q={search}"
    web_open(unknown_url)
    speaker.say(f"I've opened up a google search for: {phrase}.")


def volume_controller(level: int):
    """Controls volume from the numbers received. There are no chances for None.

    If you don't give a volume %
    conditions() is set to assume it as 50% Since Mac(s) run on a volume of 16 bars controlled by 8 digits, I have
    changed the level to become single digit with respect to 8 (eg: 50% becomes 4) for osX

    Args:
        level: Level of volume to which the system has to set.

    """
    sys.stdout.write("\r")
    if operating_system == 'Darwin':
        level = round((8 * level) / 100)
        os.system(f'osascript -e "set Volume {level}"')
    elif operating_system == 'Windows':
        if not os.path.isfile('SetVol.exe'):
            # Courtesy: https://rlatour.com/setvol/
            sys.stdout.write("\rPLEASE WAIT::Downloading volume controller for Windows")
            os.system("""curl https://thevickypedia.com/Jarvis/SetVol.exe --output SetVol.exe --silent""")
            sys.stdout.write("\r")
        os.system(f'SetVol.exe {level}')


def face_recognition_detection():
    """Initiates face recognition script and looks for images stored in named directories within 'train' directory."""
    if operating_system == 'Darwin':
        sys.stdout.write("\r")
        train_dir = 'train'
        os.mkdir(train_dir) if not os.path.isdir(train_dir) else None
        speaker.say('Initializing facial recognition. Please smile at the camera for me.')
        speaker.runAndWait()
        sys.stdout.write('\rLooking for faces to recognize.')
        try:
            result = Face().face_recognition()
        except BlockingIOError:
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
            phrase = listener(3, 5)
            if any(word in phrase.lower() for word in keywords.ok()):
                sys.stdout.write(f"\r{phrase}")
                phrase = phrase.replace(' ', '_')
                # creates a named directory if it is not found already else simply ignores
                os.system(f'cd {train_dir} && mkdir {phrase}') if phrase not in os.listdir(train_dir) else None
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
    elif operating_system == 'Windows':
        speaker.say("I am sorry, currently facial recognition and detection is not supported on Windows, due to the "
                    "package installation issues.")


def speed_test():
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


def bluetooth(phrase: str):
    """Find and connect to bluetooth devices near by.

    Args: Takes the voice recognized statement as argument.

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
        def connector(targets: dict):
            """Scans bluetooth devices in range and establishes connection with the matching device in phrase.

            Args:
                targets: Takes a dictionary of scanned devices as argument.

            Returns:
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

        sys.stdout.write('\rScanning paired Bluetooth devices')
        paired = getoutput("blueutil --paired --format json")
        paired = json_loads(paired)
        if not connector(targets=paired):
            sys.stdout.write('\rScanning UN-paired Bluetooth devices')
            speaker.say('No connections were established sir, looking for un-paired devices.')
            speaker.runAndWait()
            unpaired = getoutput("blueutil --inquiry --format json")
            unpaired = json_loads(unpaired)
            connector(targets=unpaired) if unpaired else speaker.say('No un-paired devices found sir! '
                                                                     'You may want to be more precise.')


def increase_brightness():
    """Increases the brightness to maximum in macOS."""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def decrease_brightness():
    """Decreases the brightness to bare minimum in macOS."""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")


def set_brightness(level: int):
    """Set brightness to a custom level.

    Since Jarvis uses in-built apple script, the only way to achieve this is to:
    set the brightness to bare minimum and increase {*}% from there or vice-versa.

    Args:
        level: Percentage of brightness to be set.

    """
    level = round((32 * int(level)) / 100)
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")
    for _ in range(level):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def lights(converted: str):
    """Controller for smart lights.

    Args:
        converted: Takes the voice recognized statement as argument.

    """
    global warm_light

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
        """Sets lights to custom brighness.

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
    plural = 'lights!' if lights_count > 1 else 'light!'
    if 'turn on' in converted or 'cool' in converted or 'white' in converted:
        tone = 'white' if 'white' in converted else 'cool'
        speaker.say(f'{choice(ack)}! Turning on {lights_count} {plural}') if 'turn on' in converted else \
            speaker.say(f'{choice(ack)}! Setting {lights_count} {plural} to {tone}!')
        with ThreadPoolExecutor(max_workers=lights_count) as executor:
            executor.map(cool, light_host_id)
    elif 'turn off' in converted:
        speaker.say(f'{choice(ack)}! Turning off {lights_count} {plural}')
        with ThreadPoolExecutor(max_workers=lights_count) as executor:
            executor.map(turn_off, light_host_id)
    elif 'warm' in converted or 'yellow' in converted:
        warm_light = True
        speaker.say(f'{choice(ack)}! Setting {lights_count} {plural} to yellow!') if 'yellow' in converted else \
            speaker.say(f'Sure sir! Setting {lights_count} {plural} to warm!')
        with ThreadPoolExecutor(max_workers=lights_count) as executor:
            executor.map(warm, light_host_id)
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
            lumen(host=light_ip, warm_lights=warm_light, rgb=level)
    else:
        speaker.say(f"I didn't quite get that sir! What do you want me to do to your {plural}?")


def vpn_checker():
    """Uses simple check on network id to see if it is connected to local host or not.

    Returns:
        Private IP address of host machine.

    """
    socket_ = socket(AF_INET, SOCK_DGRAM)
    socket_.connect(("8.8.8.8", 80))
    ip_address = socket_.getsockname()[0]
    socket_.close()
    if not (ip_address.startswith('192') | ip_address.startswith('127')):
        ip_address = 'VPN::' + ip_address
        info = json_load(urlopen('http://ipinfo.io/json'))
        sys.stdout.write(f"\rVPN connection is detected to {info.get('ip')} at {info.get('city')}, "
                         f"{info.get('region')} maintained by {info.get('org')}")
        speaker.say("You have your VPN turned on. Details on your screen sir! Please note that none of the home "
                    "integrations will work with VPN enabled.")
    return ip_address


def celebrate():
    """Function to look if the current date is a holiday or a birthday."""
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


def time_travel():
    """Triggered only from sentry_mode() to give a quick update on your day. Starts the report() in personalized way."""
    meeting = None
    if not os.path.isfile('meetings'):
        meeting = ThreadPool(processes=1).apply_async(func=meetings)
    day = greeting()
    speaker.say(f"Good {day} Vignesh.")
    current_date()
    current_time()
    weather()
    speaker.runAndWait()
    if meeting and day == 'Morning':
        try:
            speaker.say(meeting.get(timeout=60))
        except ThreadTimeoutError:
            pass
    elif day == 'Morning':
        meeting_reader()
    todo()
    gmail()
    speaker.say('Would you like to hear the latest news?')
    speaker.runAndWait()
    phrase = listener(3, 3)
    if any(word in phrase.lower() for word in keywords.ok()):
        news()
    time_travel.has_been_called = False
    return


def guard():
    """Security Mode will enable camera and microphone in the background.

    If any speech is recognized or a face is detected, there will another thread triggered to send notifications.
    Notifications will be triggered only after 5 minutes of initial notification.
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
        response = sns.publish(PhoneNumber=phone_number, Message=cam_error)
        if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
            logger.critical('SNS notification has been sent.')
        else:
            logger.error(f'Unable to send SNS notification.\n{response}')

    scale_factor = 1.1  # Parameter specifying how much the image size is reduced at each image scale.
    min_neighbors = 5  # Parameter specifying how many neighbors each candidate rectangle should have, to retain it.
    notified, date_extn, converted = None, None, None

    while True:
        # Listens for any recognizable speech and saves it to a notes file
        try:
            sys.stdout.write("\rSECURITY MODE")
            with Microphone() as source_:
                recognizer.adjust_for_ambient_noise(source_)
                listened = recognizer.listen(source_, timeout=3, phrase_time_limit=10)
                converted = recognizer.recognize_google(listened)
                converted = converted.replace('Jarvis', '').strip()
                sys.stdout.write(f"\r{converted}")
        except (UnknownValueError, RequestError, WaitTimeoutError):
            pass

        if converted and any(word.lower() in converted.lower() for word in keywords.guard_disable()):
            logger.critical('Disabled security mode')
            speaker.say(f'Welcome back sir! Good {greeting()}.')
            if f'{date_extn}.jpg' in os.listdir('threat'):
                speaker.say("We had a potential threat sir! Please check your email to confirm.")
            speaker.runAndWait()
            sys.stdout.write('\rDisabled Security Mode')
            break
        elif converted:
            logger.critical(f'Conversation::{converted}')

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
                logger.critical(f'Image of detected face stored as {date_extn}.jpg')

        if f'{date_extn}.jpg' not in os.listdir('threat'):
            date_extn = None

        # if no notification was sent yet or if a phrase or face is detected notification thread will be triggered
        if (not notified or float(time() - notified) > 300) and (converted or date_extn):
            notified = time()
            Thread(target=threat_notify, args=(converted, date_extn)).start()


def threat_notify(converted: str, date_extn: str or None):
    """Sends an SMS and email notification in case of a threat.

    Args:
        converted: Takes the voice recognized statement as argument.
        date_extn: Name of the attachment file which is the picture of the intruder.

    """
    dt_string = f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    title_ = f'Intruder Alert on {dt_string}'
    text_ = None

    if converted:
        response = sns.publish(PhoneNumber=phone_number,
                               Message=f"!!INTRUDER ALERT!!\n{dt_string}\n{converted}")
        body_ = f"""<html><head></head><body><h2>Conversation of Intruder:</h2><br>{converted}<br><br>
                                    <h2>Attached is a photo of the intruder.</h2>"""
    else:
        response = sns.publish(PhoneNumber=phone_number,
                               Message=f"!!INTRUDER ALERT!!\n{dt_string}\nCheck your email for more information.")
        body_ = """<html><head></head><body><h2>No conversation was recorded,
                                but attached is a photo of the intruder.</h2>"""
    if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
        logger.critical('SNS notification has been sent.')
    else:
        logger.error(f'Unable to send SNS notification.\n{response}')

    if date_extn:
        attachments_ = [f'threat/{date_extn}.jpg']
        response_ = Emailer(sender=gmail_user, recipient=robin_user).send_mail(title_, text_, body_, attachments_)
        if response_.get('ResponseMetadata').get('HTTPStatusCode') == 200:
            logger.critical('Email has been sent!')
        else:
            logger.error(f'Email dispatch was failed with response: {response_}\n')


def offline_communicator_initiate():
    """Initiates offline communicator in a dedicated thread."""
    logger.critical('Enabled Offline Communicator')
    Thread(target=offline_communicator).start()


def offline_communicator():
    """The following code will look for emails in a dedicated thread so Jarvis can run simultaneously.

    WARNING: Running sockets with a 30 second wait time is brutal, so I login once and keep checking for emails
    in a while STATUS loop. This may cause various exceptions when the login session expires or when google terminates
    the session. So I use exception handlers and circle back to restart the offline_communicator() after 2 minutes.

    To replicate a working model for offline communicator:
        - Set/Create a dedicated email account for offline communication (as it is less secure)
        - Send an email from a specific email address to avoid unnecessary response. - ENV VAR: offline_sender
        - The body of the email should only have the exact command you want Jarvis to do.
        - To "log" the response and send it out as notification, I made some changes to the pyttsx3 module. (below)
        - I also stop the response from being spoken.
        - voice_changer() is called, because when I stop the speaker, voice property is reset from what I set in main()

    Changes in "pyttsx3":
        - Created a global variable in say() -> pyttsx3/engine.py (before proxy) and store the response.
        - Created a new method and return the global variable which I created in say().
        - The new method (vig() in this case) is called to get the response which is then sent as an SMS notification.
        - Doing so, avoids making changes to all the functions within conditions() to notify the response from Jarvis.

    Env Vars:
        - offline_receive_user - email address which is getting checked for a command
        - offline_receive_pass - password for the above email address
        - offline_sender - email from which the command the expected, A.K.A - commander

    More cool stuff:
        - I created a REST API on AWS API Gateway and linked it to a JavaScript on my webpage.
        - When a request is made, the JavaScript makes a POST call to the API which then triggers a lambda job on AWS.
        - The lambda function is set to verify the secure key and then send the email to me.
        - As Jarvis will be watching for the UNREAD emails, he will process my request and send an SMS using AWS SNS.
        - Check it out: https://thevickypedia.com/jarvisoffline
        - NOTE::I have used a secret phrase that is validated by the lambda job to avoid spam API calls and emails.
        - You can also make Jarvis check for emails from your "number@tmomail.net" but response time will be > 5 min.
    """
    try:
        setdefaulttimeout(30)  # set default timeout for new socket connections to 30 seconds
        mail = IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(offline_receive_user, offline_receive_pass)
        mail.list()
        response = None
        while STATUS:
            mail.select('inbox')  # choose inbox
            return_code, messages = mail.search(None, 'UNSEEN')
            if return_code == 'OK':
                n = len(messages[0].split())
            else:
                logger.error(f"Offline Communicator::Search Error.\n{return_code}")
                raise RuntimeError
            if not n:
                pass
            else:
                for bytecode in messages[0].split():
                    ignore, mail_data = mail.fetch(bytecode, '(RFC822)')
                    for response_part in mail_data:
                        if isinstance(response_part, tuple):
                            original_email = message_from_bytes(response_part[1])
                            sender = (original_email['From']).split('<')[-1].split('>')[0].strip()
                            if sender == offline_sender:
                                # noinspection PyUnresolvedReferences
                                email_message = message_from_string(mail_data[0][1].decode('utf-8'))
                                for part in email_message.walk():
                                    required_type = ["text/html", "text/plain"]
                                    if part.get_content_type() in required_type:
                                        body = part.get_payload(decode=True).decode('utf-8').strip()
                                        logger.critical(f'Received offline input::{body}')
                                        mail.store(bytecode, "+FLAGS", "\\Deleted")  # marks email as deleted
                                        mail.expunge()  # DELETES (not send to Trash) the email permanently
                                        if body:
                                            split(body)
                                            response = f'Request:\n{body}\n\nResponse:\n{speaker.vig()}'
                                            speaker.stop()
                                            voice_changer()
                                            break
                            else:
                                mail.store(bytecode, "-FLAGS", "\\Seen")  # set "-FLAGS" to un-see/mark as unread
            if response:
                notify(user=offline_receive_user, password=offline_receive_pass, number=phone_number, body=response)
                logger.critical('Response from Jarvis has been sent!')
                response = None  # reset response to None to avoid receiving same message endlessly
            sleep(30)  # waits for 30 seconds before attempting next search
        logger.critical('Disabled Offline Communicator')
        mail.close()  # closes imap lib
        mail.logout()
    except (IMAP4.abort, IMAP4.error, s_timeout, gaierror, RuntimeError, ConnectionResetError, TimeoutError):
        setdefaulttimeout(None)  # revert default timeout for new socket connections to None
        imap_error = sys.exc_info()[0]
        logger.error(f'Offline Communicator::{imap_error.__name__}\n{format_exc()}')  # include traceback
        logger.error('Restarting Offline Communicator')
        sleep(120)  # restart the session after 2 minutes in case of any of the above exceptions
        offline_communicator_initiate()  # return used here will terminate the current function


def meeting_reader():
    """Speaks meeting information that meeting_gatherer() stored in a file named 'meetings'.

    If the file is not available, meeting information is directly fetched from the meetings() function.
    """
    with open('meetings', 'r') as meeting:
        meeting_info = meeting.read()
        sys.stdout.write(f'\r{meeting_info}')
        speaker.say(meeting_info)
        meeting.close()
    speaker.runAndWait()


def meeting_gatherer():
    """Gets return value from meetings() and writes it to file named 'meetings'.

    This function runs in a dedicated thread every 15 minutes to avoid wait time when meetings information is requested.
    """
    while STATUS:
        if os.path.isfile('meetings') and int(datetime.now().timestamp()) - int(os.stat('meetings').st_mtime) < 1_800:
            os.remove('meetings')  # removes the file if it is older than 30 minutes
        data = meetings()
        if data.startswith('You'):
            with open('meetings', 'w') as gatherer:
                gatherer.write(data)
            gatherer.close()
        sleep(900)


def meetings(meeting_file: str = 'calendar.scpt'):
    """Uses applescript to fetch events/meetings from local Calendar (including subscriptions) or Microsoft Outlook.

    Args:
        meeting_file: Takes applescript filename as argument. Defaults to calendar.scpt unless an alternate is passed.

    Returns:
        On success, returns a message saying which meeting is scheduled at what time.
        If no events, returns a message saying there are no events in the next 12 hours.
        On failure, returns a message saying Jarvis was unable to read calendar/outlook.

    """
    if operating_system == 'Windows':
        return "Meetings feature on Windows hasn't been developed yet sir!"

    args = [1, 3]
    process = Popen(['/usr/bin/osascript', meeting_file] + [str(arg) for arg in args], stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    if error := process.returncode:  # stores process.returncode in error if process.returncode is not 0
        logger.error(f"Failed to read {meeting_file.replace('.scpt', '')} with exit code: "
                     f"{error}\n{err.decode('UTF-8')}")
        failure = f"Unable to read {meeting_file.replace('.scpt', '')}\n{err.decode('UTF-8')}"
        os.system(f"""osascript -e 'display notification "{failure}" with title "Jarvis"'""")
        return f"I was unable to read your {meeting_file.replace('.scpt', '')} sir! Please make sure it is in sync."

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


def system_vitals():
    """Reads system vitals on MacOS."""
    if operating_system == 'Windows':
        speaker.say("Reading vitals on Windows hasn't been developed yet sir")
        return

    if not root_password:
        speaker.say("You haven't provided a root password for me to read system vitals sir! "
                    "Add the root password as an environment variable for me to read.")
        return

    version = host_info('version')
    model = host_info('model')

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
    sys.stdout.write(f'\r{output}')
    speaker.say(f'Your {model} was last booted on {restart_time}. '
                f'Current boot time is: {restart_duration}.')
    if second >= 172_800:
        if boot_extreme := re.search('(.*) days', restart_duration):
            warn = int(boot_extreme.group().replace(' days', '').strip())
            speaker.say(f'Sir! your {model} has been running continuously for more than {warn} days. You must '
                        f'consider a reboot for better performance. Would you like me to restart it for you sir?')
            speaker.runAndWait()
            response = listener(3, 3)
            if any(word in response.lower() for word in keywords.ok()):
                restart(target='PC_Proceed')


def get_ssid():
    """Gets SSID of the network connected.

    Returns:
        WiFi or Ethernet SSID.

    """
    if operating_system == 'Darwin':
        process = Popen(
            ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
            stdout=PIPE)
        out, err = process.communicate()
        if error := process.returncode:
            logger.error(f"Failed to fetch SSID with exit code: {error}\n{err}")
        # noinspection PyTypeChecker
        return dict(map(str.strip, info.split(': ')) for info in out.decode('utf-8').split('\n')[:-1]).get('SSID')
    elif operating_system == 'Windows':
        netsh = check_output("netsh wlan show interfaces", shell=True)
        for info in netsh.decode('utf-8').split('\n')[:-1]:
            if 'SSID' in info:
                return info.strip('SSID').replace('SSID', '').replace(':', '').strip()


class PersonalCloud:
    """Controller for Personal Cloud.

    Reference: https://github.com/thevickypedia/personal_cloud/blob/main/README.md#run-book

    Make sure to enable file access for Terminal sessions. Steps:
        Step 1:
            - Mac OS 10.14.* and higher - System Preferences -> Security & Privacy -> Privacy -> Full Disk Access
            - Mac OS 10.13.* and lower - System Preferences -> Security & Privacy -> Privacy -> Accessibility
        Step 2:
            Unlock for admin privileges. Click on the "+" icon. Select Applications -> Utilities -> Terminal
    """

    @staticmethod
    def get_port():
        """
        - Chooses a TCP PORT number dynamically that is not being used to ensure we don't rely on a single port.
        - Well-Known ports: 0 to 1023
        - Registered ports: 1024 to 49151
        - Dynamically available: 49152 to 65535
        - Alternate to active_sessions ->
        - check_output(f"echo {root_password} | sudo -S lsof -PiTCP -sTCP:LISTEN 2>&1;", shell=True).decode('utf-8')
        - 'remove' should be an actual function as per pep-8 standards, bypassing it using  # noqa
        """

        active_sessions = check_output("netstat -anvp tcp | awk 'NR<3 || /LISTEN/' 2>&1;", shell=True).decode('utf-8')
        if not (localhost := gethostbyname('localhost')):  # 'if not' in walrus operator to assign localhost manually
            localhost = '127.0.0.1'
        remove = lambda item: item.replace(localhost, '').replace(':', '').replace('.', '').replace('*', '')  # noqa
        active_ports = []
        for index, row in enumerate(active_sessions.split('\n')):
            if row and index > 1:  # First row - Description of the netstat command, Second row - Headers for columns
                active_ports.append(remove(row.split()[3]))
        while True:
            port = randrange(49152, 65535)
            if port not in active_ports:
                return port

    @staticmethod
    def delete_repo():
        """Called during enable and disable to delete any existing bits for a clean start next time."""
        if 'personal_cloud' in os.listdir(home_dir):
            rmtree(f'{home_dir}/personal_cloud')  # delete repo for a fresh start

    @staticmethod
    def enable():
        """Enables personal cloud.

        - Clones personal_cloud repo in a dedicated Terminal,
        - Creates a dedicated virtual env and installs the requirements within it (ETA: ~20 seconds),
        - If personal_cloud_volume env var is provided, Jarvis will mount the drive if it is is connected to the device
        - Gets and sets env vars required for the personal cloud,
        - Generates random username and passphrase for login info,
        - Triggers personal cloud using a dedicated Terminal,
        - Sends an SMS with endpoint, username and password to your mobile phone.
        """
        personal_cloud.delete_repo()
        initial_script = f"cd {home_dir} && git clone -q https://github.com/thevickypedia/personal_cloud.git && " \
                         f"cd personal_cloud && python3 -m venv venv && source venv/bin/activate && " \
                         f"pip3 install -r requirements.txt"

        apple_script('Terminal').do_script(initial_script)

        personal_cloud_port = personal_cloud.get_port()
        personal_cloud_username = ''.join(choices(ascii_letters, k=10))
        personal_cloud_passphrase = ''.join(choices(ascii_letters + digits, k=10))
        personal_cloud_volume = os.environ.get('personal_cloud_volume')

        if not personal_cloud.volume_checker(volume_name=personal_cloud_volume) if personal_cloud_volume else None:
            logger.critical(f"Volume: {personal_cloud_volume} was not connected to your {host_info('model')}")
            personal_cloud_volume = None

        # export PORT for both ngrok and exec scripts as they will be running in different Terminal sessions
        ngrok_script = f"cd {home_dir}/personal_cloud && export PORT={personal_cloud_port} && " \
                       f"source venv/bin/activate && python3 ngrok.py"

        exec_script = f"export PORT={personal_cloud_port} && " \
                      f"export USERNAME={personal_cloud_username} && " \
                      f"export PASSWORD={personal_cloud_passphrase} && " \
                      f"export volume_name='{personal_cloud_volume}' && " \
                      f"cd {home_dir}/personal_cloud && source venv/bin/activate && python3 server.py"

        cloned_path = f'{home_dir}/personal_cloud'
        while True:  # wait for the requirements to be installed after the repo was cloned
            if 'personal_cloud' in os.listdir(home_dir) and 'venv' in os.listdir(cloned_path) and \
                    'bin' in os.listdir(f'{cloned_path}/venv') and 'pyngrok' in os.listdir(f'{cloned_path}/venv/bin'):
                apple_script('Terminal').do_script(exec_script)
                apple_script('Terminal').do_script(ngrok_script)
                break

        while True:  # wait for the endpoint url (as file) to get generated within personal_cloud
            if 'url' in os.listdir(cloned_path):
                url = open(f'{cloned_path}/url', 'r').read()  # commit #d564dfa... on personal_cloud
                break

        notify(user=offline_receive_user, password=offline_receive_pass, number=phone_number,
               body=f"URL: {url}\nUsername: {personal_cloud_username}\nPassword: {personal_cloud_passphrase}")

    @staticmethod
    def volume_checker(volume_name: str, mount: bool = True, unmount: bool = False):
        """By default, Mounts volume in a thread if it is connected to the device and volume name is set as env var.

        If unmount is set to True, only then the drive is stopped of its usage and Jarvis unmounts it.

        Args:
            volume_name: Name of the volume stored as env var.
            mount: Boolean value set to True to mount the volume by default.
            unmount: Boolean value set to False to unmount the volume only when requested.

        Returns:
            Boolean value indicating whether the volume is connected or not.

        """
        connected = False
        disk_check = check_output("diskutil list 2>&1;", shell=True)
        disk_list = disk_check.decode('utf-8').split('\n\n')
        if mount:
            for disk in disk_list:
                if disk and '(external, physical):' in disk and volume_name in disk.split('\n')[-1]:
                    connected = True
                    break
            if connected:
                Thread(target=lambda: os.system(f'diskutil mount "{volume_name}" > /dev/null 2>&1;')).start()
                logger.critical(f'Volume: {volume_name} has been mounted.')
                return True
            else:
                return False
        elif unmount:
            pid_check = check_output(f"echo {root_password} | sudo -S lsof '/Volumes/{volume_name}' 2>&1;", shell=True)
            pid_list = pid_check.decode('utf-8').split('\n')
            for id_ in pid_list:
                os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1') if id_ else None
            logger.critical(f'{len(pid_list) - 1} active processes have been terminated.')
            for disk in disk_list:
                if disk and '(external, physical):' in disk:
                    unmount_uuid = disk.split('\n')[0].strip('(external, physical):')
                    disk_info = disk.split('\n')[-1]
                    if volume_name in disk_info:
                        os.system(f'diskutil unmountDisk {unmount_uuid} > /dev/null 2>&1;')
                        logger.critical(f"Disk {unmount_uuid} with Name {volume_name} has been unmounted from your "
                                        f"{host_info('model')}")

    @staticmethod
    def disable():
        """Shuts off the server.py to stop the personal cloud.

        This eliminates the hassle of passing args and handling threads.
        """
        pid_check = check_output("ps -ef | grep 'Python server.py\\|Python ngrok.py'", shell=True)
        pid_list = pid_check.decode('utf-8').split('\n')
        for pid_info in pid_list:
            if pid_info and 'Library' in pid_info and ('/bin/sh' not in pid_info or 'grep' not in pid_info):
                os.system(f'kill -9 {pid_info.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout
        personal_cloud.delete_repo()
        personal_cloud.volume_checker(volume_name=os.environ.get('personal_cloud_volume'), mount=False, unmount=True)


def internet_checker():
    """Uses speed test api to check for internet connection.

    >>> Speedtest

    Returns:
        On success, returns Speedtest module.
        On failure, returns boolean False.

    """
    try:
        return Speedtest()
    except ConfigRetrievalError:
        return False


def sentry_mode():
    """Sentry mode, all it does is to wait for the right keyword to wake up and get into action.

    Threshold is used to sanity check sentry_mode() so that:
        - Jarvis doesn't run into Fatal Python error.
        - Jarvis restarts at least twice a day and gets a new pid.
    """
    time_of_day = ['morning', 'night', 'afternoon', 'after noon', 'evening', 'goodnight']
    wake_up_words = ['look alive', 'wake up', 'wakeup', 'show time', 'showtime', 'time to work', 'spin up']
    threshold = 0
    while threshold < 10_000:
        threshold += 1
        try:
            sys.stdout.write("\rSentry Mode")
            listen = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            sys.stdout.write("\r")
            key_original = recognizer.recognize_google(listen).strip()
            sys.stdout.write(f"\r{key_original}")
            key = key_original.lower()
            key_split = key.split()
            if [word for word in key_split if word in time_of_day] and 'jarvis' in key:
                time_travel.has_been_called = True
                if event:
                    speaker.say(f'Happy {event}!')
                if 'night' in key_split or 'goodnight' in key_split:
                    Thread(target=pc_sleep).start()
                time_travel()
            elif key == 'jarvis':
                speaker.say(f'{choice(wake_up3)}')
                initialize()
            elif any(word in key for word in wake_up_words) and 'jarvis' in key:
                speaker.say(f'{choice(wake_up1)}')
                initialize()
            elif 'jarvis' in key:
                remove = ['buddy', 'jarvis']
                converted = ' '.join([i for i in key_original.split() if i.lower() not in remove])
                if converted:
                    split(converted.strip())
                else:
                    speaker.say(f'{choice(wake_up3)}')
                    initialize()
            speaker.runAndWait()
        except (UnknownValueError, RequestError, WaitTimeoutError):
            continue
        except KeyboardInterrupt:
            exit_process()
            terminator()
        except (RecursionError, TimeoutError, RuntimeError, ConnectionResetError):
            unknown_error = sys.exc_info()[0]
            logger.error(f'Unknown exception::{unknown_error.__name__}\n{format_exc()}')  # include traceback
            speaker.say('I faced an unknown exception.')
            restart()
    speaker.stop()  # stops before starting a new speaker loop to avoid conflict with offline communicator
    speaker.say("My run time has reached the threshold!")
    volume_controller(5)
    restart()


def size_converter(byte_size: int):
    """Gets the current memory consumed and converts it to human friendly format.

    Args:
        byte_size: Receives byte size as argument.

    Returns:
        Converted understandable size.

    """
    if not byte_size:
        if operating_system == 'Darwin':
            from resource import RUSAGE_SELF, getrusage
            byte_size = getrusage(RUSAGE_SELF).ru_maxrss
        elif operating_system == 'Windows':
            byte_size = Process(os.getpid()).memory_info().peak_wset
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    integer = int(floor(log(byte_size, 1024)))
    power = pow(1024, integer)
    size = round(byte_size / power, 2)
    response = str(size) + ' ' + size_name[integer]
    return response


def exit_message():
    """Variety of exit messages based on day of week and time of day."""
    current = datetime.now().strftime("%p")  # current part of day (AM/PM)
    clock = datetime.now().strftime("%I")  # current hour
    today = datetime.now().strftime("%A")  # current day

    if current == 'AM' and int(clock) < 10:
        exit_msg = f"Have a nice day, and happy {today}."
    elif current == 'AM' and int(clock) >= 10:
        exit_msg = f"Enjoy your {today}."
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 3) and today in weekend:
        exit_msg = "Have a nice afternoon, and enjoy your weekend."
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 3):
        exit_msg = "Have a nice afternoon."
    elif current == 'PM' and int(clock) < 6 and today in weekend:
        exit_msg = "Have a nice evening, and enjoy your weekend."
    elif current == 'PM' and int(clock) < 6:
        exit_msg = "Have a nice evening."
    elif today in weekend:
        exit_msg = "Have a nice night, and enjoy your weekend."
    else:
        exit_msg = "Have a nice night."

    if event:
        exit_msg += f'\nAnd by the way, happy {event}'

    return exit_msg


def terminator():
    """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc.

    Using this, eliminates the hassle of forcing multiple threads to stop.
    """
    # noinspection PyUnresolvedReferences,PyProtectedMember
    os._exit(0)


def remove_files():
    """Function that deletes multiple files when called during exit operation.

    Deletes:
        - all .lock files created for alarms and reminders.
        - location data in yaml format, to recreate a new one next time around.
        - meetings, file to recreate a new one next time around.
    """
    [os.remove(f"alarm/{file}") for file in os.listdir('alarm') if file != '.keep']
    [os.remove(f"reminder/{file}") for file in os.listdir('reminder') if file != '.keep']
    os.remove('location.yaml') if os.path.isfile('location.yaml') else None
    os.remove('meetings') if os.path.isfile('meetings') else None


def exit_process():
    """Function that holds the list of operations done upon exit."""
    global STATUS
    STATUS = False
    logger.critical('JARVIS::Stopping Now::Run STATUS has been unset')
    alarms, reminders = [], {}
    for file in os.listdir('alarm'):
        if file != '.keep' and file != '.DS_Store':
            alarms.append(file)
    for file in os.listdir('reminder'):
        if file != '.keep' and file != '.DS_Store':
            split_val = file.replace('.lock', '').split('|')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        logger.critical(f'JARVIS::Deleting Reminders - {reminders}')
        if len(reminders) == 1:
            speaker.say('You have a pending reminder sir!')
        else:
            speaker.say(f'You have {len(reminders)} pending reminders sir!')
        for key, value in reminders.items():
            speaker.say(f"{value.replace('_', ' ')} at "
                        f"{key.replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')}")
    if alarms:
        logger.critical(f'JARVIS::Deleting Alarms - {alarms}')
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
        pass
    remove_files()
    sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                     f"\nTotal runtime: {time_converter(perf_counter())}")


def extract_nos(input_: str):
    """Extracts number part from a string.

    Args:
        input_: Takes string as an argument.

    Returns:
        Float values.

    """
    return float('.'.join(re.findall(r"\d+", input_)))


def format_nos(input_: float):
    """Removes .0 float values.

    Args:
        input_: Int if found, else returns the received float value.

    Returns:
        Formatted integer.

    """
    return int(input_) if isinstance(input_, float) and input_.is_integer() else input_


def extract_str(input_: str):
    """Extracts strings from the received input.

    Args:
        input_: Takes a string as argument.

    Returns:
        A string after removing special characters.

    """
    return ''.join([i for i in input_ if not i.isdigit() and i not in [',', '.', '?', '-', ';', '!', ':']])


def host_info(required: str):
    """Gets both the model and version of the hosted device.

    Args:
        required: model or version

    Returns:
        Model or version of the machine based on the arg received.

    """
    device = (check_output("sysctl hw.model", shell=True)).decode('utf-8').split('\n')  # gets model info
    result = list(filter(None, device))[0]  # removes empty string ('\n')
    model = extract_str(result).replace('hwmodel', '').strip()
    version = extract_nos(''.join(device))
    if required == 'model':
        return model
    elif required == 'version':
        return version


def pc_sleep():
    """Locks the host device using osascript and reduces brightness to bare minimum."""
    Thread(target=decrease_brightness).start()
    # os.system("""osascript -e 'tell app "System Events" to sleep'""")  # requires restarting Jarvis manually
    os.system("""osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'""")
    if not (report.has_been_called or time_travel.has_been_called):
        speaker.say(choice(ack))


def stop_terminal():
    """Uses pid to kill terminals as terminals await user confirmation interrupting shutdown/restart."""
    pid_check = check_output("ps -ef | grep 'iTerm\\|Terminal'", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for id_ in pid_list:
        if id_ and 'Applications' in id_ and '/usr/bin/login' not in id_:
            os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout


def restart(target: str = None):
    """Restart triggers restart.py which in turn starts Jarvis after 5 seconds.

    Doing this changes the PID to avoid any Fatal Errors occurred by long running threads.
    restart(PC) will restart the machine after getting confirmation.
    restart(anything_else) will restart the machine without getting any confirmation.

    Args:
        target:
        None - Restarts Jarvis to reset PID
        PC - Restarts the machine after getting confirmation.

    """
    if target:
        if target == 'PC':
            speaker.say(f'{choice(confirmation)} restart your {host_info("model")}?')
            speaker.runAndWait()
            converted = listener(3, 3)
        else:
            converted = 'yes'
        if any(word in converted.lower() for word in keywords.ok()):
            exit_process()
            if operating_system == 'Darwin':
                stop_terminal()
                call(['osascript', '-e', 'tell app "System Events" to restart'])
            elif operating_system == 'Windows':
                os.system("shutdown /r /t 1")
            terminator()
        else:
            speaker.say("Machine state is left intact sir!")
            return
    global STATUS
    STATUS = False
    logger.critical('JARVIS::Restarting Now::Run STATUS has been unset')
    sys.stdout.write(f"\rMemory consumed: {size_converter(0)}\tTotal runtime: {time_converter(perf_counter())}")
    speaker.say('Restarting now sir! I will be up and running momentarily.')
    try:
        speaker.runAndWait()
    except RuntimeError:
        pass
    os.system('python3 restart.py')
    exit(1)  # Don't call terminator() as, os._exit(1) in that func will kill the background threads running in parallel


def shutdown(proceed: bool = False):
    """Gets confirmation and turns off the machine.

    Args: Boolean value whether or not to get confirmation.

    """
    global place_holder
    if not proceed:
        speaker.say(f"{choice(confirmation)} turn off the machine?")
        speaker.runAndWait()
        converted = listener(3, 3)
    else:
        converted = 'yes'
    if converted != 'SR_ERROR':
        place_holder = None
        if any(word in converted.lower() for word in keywords.ok()):
            exit_process()
            if operating_system == 'Darwin':
                stop_terminal()
                call(['osascript', '-e', 'tell app "System Events" to shut down'])
            elif operating_system == 'Windows':
                os.system("shutdown /s /t 1")
            terminator()
        else:
            speaker.say("Machine state is left intact sir!")
            return
    else:
        if place_holder == 0:
            place_holder = None
            return
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            shutdown()


def voice_changer(change: str = None):
    """Alters voice and rate of speech according to the Operating System.

    Alternatively you can choose from a variety of voices available for your device.

    Args:
        change: Initiates changing voices with the volume ID given in statement.

    """
    global place_holder
    voices = speaker.getProperty("voices")  # gets the list of voices available
    # noinspection PyTypeChecker,PyUnresolvedReferences
    avail_voices = len(voices)

    # noinspection PyUnresolvedReferences
    def voice_default(voice_id=(7, 0)):  # default values set as tuple
        """Sets default voice module number.

        Args:
            voice_id: Default voice ID for MacOS and Windows.

        """
        if operating_system == 'Darwin':
            speaker.setProperty("voice", voices[voice_id[0]].id)  # voice module #7 for MacOS
        elif operating_system == 'Windows':
            speaker.setProperty("voice", voices[voice_id[-1]].id)  # voice module #0 for Windows
            speaker.setProperty('rate', 190)  # speech rate is slowed down in Windows for optimal experience
        else:
            logger.error(f'Unsupported Operating System::{operating_system}.')
            terminator()

    if change:
        if not (distribution := [int(s) for s in re.findall(r'\b\d+\b', change)]):  # walrus on if not distribution
            distribution = range(avail_voices)
        for module_id in distribution:
            if module_id < avail_voices:
                voice_default([module_id])  # passing a list as default is tuple and index values are used to reference
                sys.stdout.write(f'\rVoice module has been re-configured to {module_id}')
                if not place_holder:
                    speaker.say('Voice module has been re-configured sir! Would you like me to retain this?')
                    place_holder = 1
                elif place_holder == 1:
                    speaker.say("Here's an example of one of my other voices sir!. Would you like me to use this one?")
                    place_holder = 2
                else:
                    speaker.say('How about this one sir?')
            else:
                speaker.say(f'The voice module number {module_id} is not available for your device sir! '
                            f'You may want to try a module number between 0 and {avail_voices - 1}')
            speaker.runAndWait()
            keyword = listener(3, 3)
            if keyword == 'SR_ERROR':
                voice_default()
                speaker.say("Sorry sir! I had trouble understanding. I'm back to my default voice.")
                place_holder = 0
                return
            elif 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                voice_default()
                speaker.say('Reverting the changes to default voice module sir!')
                place_holder = 0
                return
            elif any(word in keyword.lower() for word in keywords.ok()):
                speaker.say(choice(ack))
                place_holder = 0
                return
            elif custom_id := [int(id_) for id_ in re.findall(r'\b\d+\b', keyword)]:
                voice_changer(str(custom_id))
                break
    else:
        voice_default()


if __name__ == '__main__':
    STATUS = True
    logger.critical('JARVIS::Starting Now::Run STATUS has been set')

    sys.stdout.write('\rVoice ID::Female: 1/17 Male: 0/7')  # Voice ID::reference
    speaker = init()  # initiates speaker
    recognizer = Recognizer()  # initiates recognizer that uses google's translation
    keywords = Keywords()  # stores Keywords() class from helper_functions/keywords.py
    conversation = Conversation()  # stores Conversation() class from helper_functions/conversation.py
    operating_system = system()  # detects current operating system
    aws = AWSClients()  # initiates AWSClients object to fetch credentials from AWS secrets
    database = Database()  # initiates Database() for TO-DO items
    temperature = Temperature()  # initiates Temperature() for temperature conversions
    personal_cloud = PersonalCloud()  # initiates PersonalCloud() to enable or disable HDD hosting
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 10)  # increases the recursion limit by 10 times
    sns = client('sns')  # initiates sns for notification service
    home_dir = os.path.expanduser('~')  # gets the path to current user profile

    volume_controller(50)  # defaults to volume 50%
    voice_changer()  # changes voice to default values given

    # Get all necessary credentials and api keys from env vars or aws client
    sys.stdout.write("\rFetching credentials and API keys.")
    git_user = os.environ.get('git_user') or aws.git_user()
    git_pass = os.environ.get('git_pass') or aws.git_pass()
    weather_api = os.environ.get('weather_api') or aws.weather_api()
    news_api = os.environ.get('news_api') or aws.news_api()
    maps_api = os.environ.get('maps_api') or aws.maps_api()
    gmail_user = os.environ.get('gmail_user') or aws.gmail_user()
    gmail_pass = os.environ.get('gmail_pass') or aws.gmail_pass()
    robin_user = os.environ.get('robinhood_user') or aws.robinhood_user()
    robin_pass = os.environ.get('robinhood_pass') or aws.robinhood_pass()
    robin_qr = os.environ.get('robinhood_qr') or aws.robinhood_qr()
    tv_client_key = os.environ.get('tv_client_key') or aws.tv_client_key()
    birthday = os.environ.get('birthday') or aws.birthday()
    offline_receive_user = os.environ.get('offline_receive_user') or aws.offline_receive_user()
    offline_receive_pass = os.environ.get('offline_receive_pass') or aws.offline_receive_pass()
    offline_sender = os.environ.get('offline_sender') or aws.offline_sender()
    icloud_user = os.environ.get('icloud_user') or aws.icloud_user()
    icloud_pass = os.environ.get('icloud_pass') or aws.icloud_pass()
    recovery = os.environ.get('icloud_recovery') or aws.icloud_recovery()
    phone_number = os.environ.get('phone') or aws.phone()
    think_id = os.environ.get('think_id') or aws.think_id()
    router_pass = os.environ.get('router_pass') or aws.router_pass()

    if st := internet_checker():
        sys.stdout.write(f'\rINTERNET::Connected to {get_ssid()}. Scanning localhost for connected devices.')
    else:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet sir! Please check your connection settings and retry.")
        speaker.runAndWait()
        terminator()

    # Retrieves devices IP by doing a local IP range scan using Netgear API
    # Note: This can also be done my manually passing the IP addresses in a list (for lights) or string (for TV)
    # Using Netgear API will avoid the manual change required to rotate the IPs whenever the router is restarted
    local_devices = LocalIPScan(router_pass=router_pass)
    hallway_ip = [val for val in local_devices.hallway()]
    kitchen_ip = [val for val in local_devices.kitchen()]
    bedroom_ip = [val for val in local_devices.bedroom()]
    tv_ip = ''.join([val for val in local_devices.tv()])

    if not (root_password := os.environ.get('PASSWORD')):
        sys.stdout.write('\rROOT PASSWORD is not set!')

    # place_holder is used in all the functions so that the "I didn't quite get that..." part runs only once
    # greet_check is used in initialize() to greet only for the first run
    # tv is set to None instead of TV() at the start to avoid turning on the TV unnecessarily
    # suggestion_count is used in google_searchparser to limit the number of times suggestions are used.
    # This is just a safety check so that Jarvis doesn't run into infinite loops while looking for suggestions.
    warm_light, place_holder, greet_check, tv, suggestion_count = False, None, None, None, 0

    # stores necessary values for geo location to receive the latitude, longitude and address
    options.default_ssl_context = create_default_context(cafile=where())
    geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)

    # checks the modified time of location.yaml (if exists) and uses the data only if it was modified 72 hours ago
    if os.path.isfile('location.yaml') and \
            int(datetime.now().timestamp()) - int(os.stat('location.yaml').st_mtime) < 259_200:
        location_details = yaml_load(open('location.yaml'), Loader)
        current_lat = location_details['latitude']
        current_lon = location_details['longitude']
        location_info = location_details['address']
    else:
        current_lat, current_lon, location_info = location_services(device_selector())
        location_dumper = [{'latitude': current_lat}, {'longitude': current_lon}, {'address': location_info}]
        with open('location.yaml', 'w') as location_writer:
            for dumper in location_dumper:
                yaml_dump(dumper, location_writer, default_flow_style=False)

    # different responses for different conditions in sentry mode
    wake_up1 = ['Up and running sir!', "We are online and ready sir!", "I have indeed been uploaded sir!",
                'My listeners have been activated sir!']
    wake_up2 = ['For you sir - Always!', 'At your service sir!']
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

    event = celebrate()  # triggers celebrate function and wishes for a event if found.

    sys.stdout.write(f"\rCurrent Process ID: {Process(os.getpid()).pid}\tCurrent Volume: 50%")

    offline_communicator_initiate()  # dedicated function to initiate offline communicator to ease restart

    logger.critical('Meeting gather has been initiated.')
    Thread(target=meeting_gatherer).start()  # triggers meeting_gathere to run in the background

    # starts sentry mode
    Thread(target=playsound, args=['indicators/initialize.mp3']).start()
    with Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        sentry_mode()
