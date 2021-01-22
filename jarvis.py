import json
import logging
import math
import os
import platform
import random
import re
import ssl
import subprocess
import sys
import time
import unicodedata
import webbrowser
from datetime import datetime, timedelta
from threading import Thread
from urllib.request import urlopen

import boto3
import certifi
import holidays
import pytemperature
import pyttsx3 as audio
import requests
import speech_recognition as sr
import yaml
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from inflect import engine
from playsound import playsound
from psutil import Process, virtual_memory
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudAPIResponseException, PyiCloudFailedLoginException
from requests.auth import HTTPBasicAuth
from socket import socket, AF_INET, SOCK_DGRAM, gethostname
from speedtest import Speedtest, ConfigRetrievalError
from wordninja import split as splitter

from helper_functions.alarm import Alarm
from helper_functions.aws_clients import AWSClients
from helper_functions.conversation import Conversation
from helper_functions.database import Database, file_name
from helper_functions.emailer import send_mail
from helper_functions.keywords import Keywords
from helper_functions.reminder import Reminder
from tv_controls import TV


def listener(timeout, phrase_limit):
    """Function to activate listener, this function will be called by most upcoming functions to listen to user input.
    Returns 'SR_ERROR' as a string which is conditioned to respond appropriately."""
    try:
        sys.stdout.write("\rListener activated..") and playsound('indicators/start.mp3')
        listened = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        sys.stdout.write("\r") and playsound('indicators/end.mp3')
        return_val = recognizer.recognize_google(listened)
        sys.stdout.write(f'\r{return_val}')
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
        return_val = 'SR_ERROR'
    return return_val


def split(key):
    if 'and' in key:
        for each in key.split('and'):
            conditions(each.strip())
    elif 'also' in key:
        for each in key.split('also'):
            conditions(each.strip())
    else:
        conditions(key.strip())


def greeting():
    """Function that returns a greeting based on the current time of the day."""
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
    """Function to initialize when woke up from sleep mode. greet_check and dummy are to ensure greeting is given only
    for the first time, the script is run place_holder is set for all the functions so that the function runs only ONCE
    again in case of an exception"""
    global greet_check
    greet_check = 'initialized'
    if dummy.has_been_called:
        speaker.say("What can I do for you?")
        dummy.has_been_called = False
    else:
        speaker.say(f'Good {greeting()}.')
    renew()


def renew():
    """renew() function will keep listening and send the response to conditions() This function runs only for a minute
    and goes to sentry_mode() if nothing is heard"""
    speaker.runAndWait()
    waiter = 0
    while waiter < 12:
        waiter += 1
        try:
            sys.stdout.write(f"\rListener activated..") and playsound('indicators/start.mp3') if waiter == 1 else \
                sys.stdout.write(f"\rListener activated..")
            listen = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('indicators/end.mp3') if waiter == 0 else sys.stdout.write("\r")
            converted = recognizer.recognize_google(listen)
            if any(word in converted.lower() for word in keywords.sleep()):
                speaker.say(f"Activating sentry mode, enjoy yourself sir!")
                speaker.runAndWait()
                return
            else:
                split(converted)
                speaker.runAndWait()
                waiter = 0
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            pass


def time_converter(seconds):
    """Run time calculator"""
    seconds = round(seconds % (24 * 3600))
    hour = round(seconds // 3600)
    seconds %= 3600
    minutes = round(seconds // 60)
    seconds %= 60
    if hour:
        return f'{hour} hours, {minutes} minutes, {seconds} seconds'
    elif minutes == 1:
        return f'{minutes} minute, {seconds} seconds'
    elif minutes:
        return f'{minutes} minutes, {seconds} seconds'
    elif seconds:
        return f'{seconds} seconds'


def conditions(converted):
    """Conditions function is used to check the message processed, and use the keywords to do a regex match and trigger
    the appropriate function which has dedicated task"""
    sys.stdout.write(f'\r{converted}')

    if 'are you there' in converted.lower() or converted.strip() == 'Jarvis' or 'you there' in \
            converted.lower():
        speaker.say("I'm here sir!")

    elif any(word in converted.lower() for word in keywords.date()) and \
            not any(word in converted.lower() for word in keywords.avoid()):
        current_date()

    elif any(word in converted.lower() for word in keywords.time()):
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        if place:
            current_time(place)
        else:
            current_time(None)

    elif any(word in converted.lower() for word in keywords.weather()):
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        checker = converted.lower()
        weather_cond = ['tomorrow', 'day after', 'next week', 'tonight', 'afternoon', 'evening']
        if any(match in checker for match in weather_cond):
            if place:
                weather_condition(place, converted)
            else:
                weather_condition(None, converted)
        elif place:
            weather(place)
        else:
            weather(None)

    elif any(word in converted.lower() for word in keywords.system_info()):
        system_info()

    elif any(word in converted.lower() for word in keywords.wikipedia()):
        wikipedia_()

    elif any(word in converted.lower() for word in keywords.news()):
        news()

    elif any(word in converted.lower() for word in keywords.report()):
        report()

    elif any(word in converted.lower() for word in keywords.robinhood()):
        robinhood()

    elif any(word in converted.lower() for word in keywords.repeat()):
        repeater()

    elif any(word in converted.lower() for word in keywords.location()):
        location()

    elif any(word in converted.lower() for word in keywords.locate()):
        locate(converted)

    elif any(word in converted.lower() for word in keywords.gmail()):
        gmail()

    elif any(word in converted.lower() for word in keywords.meaning()):
        meaning(converted.split()[-1])

    elif any(word in converted.lower() for word in keywords.delete_todo()):
        delete_todo()

    elif any(word in converted.lower() for word in keywords.list_todo()):
        todo()

    elif any(word in converted.lower() for word in keywords.add_todo()):
        add_todo()

    elif any(word in converted.lower() for word in keywords.delete_db()):
        delete_db()

    elif any(word in converted.lower() for word in keywords.create_db()):
        create_db()

    elif any(word in converted.lower() for word in keywords.distance()) and \
            not any(word in converted.lower() for word in keywords.avoid()):
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

    elif any(word in converted.lower() for word in conversation.form()):
        speaker.say("I am a program, I'm without form.")

    elif any(word in converted.lower() for word in keywords.geopy()):
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

    elif any(word in converted.lower() for word in keywords.directions()):
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

    elif any(word in converted.lower() for word in keywords.webpage()) and \
            not any(word in converted.lower() for word in keywords.avoid()):
        converted = converted.replace(' In', 'in').replace(' Co. Uk', 'co.uk')
        host = (word for word in converted.split() if '.' in word)
        webpage(host)

    elif any(word in converted.lower() for word in keywords.kill_alarm()):
        kill_alarm()

    elif any(word in converted.lower() for word in keywords.alarm()):
        alarm(converted.lower())

    elif any(word in converted.lower() for word in keywords.google_home()):
        google_home(device=None, file=None)

    elif any(word in converted.lower() for word in keywords.jokes()):
        jokes()

    elif any(word in converted.lower() for word in keywords.reminder()):
        reminder(converted.lower())

    elif any(word in converted.lower() for word in keywords.notes()):
        notes()

    elif any(word in converted.lower() for word in keywords.github()):
        git_user = os.getenv('git_user') or aws.git_user()
        git_pass = os.getenv('git_pass') or aws.git_pass()
        auth = HTTPBasicAuth(git_user, git_pass)
        request = requests.get(f'https://api.github.com/user/repos?type=all&per_page=100', auth=auth)
        response = request.json()
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
             for word in converted.lower().split() for item in repos for repo, clone_url in item.items()]
            if result:
                github(target=result)
            else:
                speaker.say("Sorry sir! I did not find that repo.")

    elif any(word in converted.lower() for word in keywords.txt_message()):
        number = '-'.join([str(s) for s in re.findall(r'\b\d+\b', converted)])
        send_sms(number)

    elif any(word in converted.lower() for word in keywords.google_search()):
        phrase = converted.split('for')[-1] if 'for' in converted else None
        google_search(phrase)

    elif any(word in converted.lower() for word in keywords.tv()):
        television(converted)

    elif any(word in converted.lower() for word in keywords.apps()):
        apps(converted.split()[-1])

    elif any(word in converted.lower() for word in keywords.music()):
        if 'speaker' in converted.lower():
            music(converted)
        else:
            music(None)

    elif any(word in converted.lower() for word in keywords.volume()):
        if 'mute' in converted.lower():
            level = 0
        elif 'max' in converted.lower() or 'full' in converted.lower():
            level = 100
        else:
            level = re.findall(r'\b\d+\b', converted)  # gets integers from string as a list
            level = int(level[0]) if level else 50  # converted to int for volume
        volume_controller(level)
        speaker.say(f"{random.choice(ack)}")

    elif any(word in converted.lower() for word in keywords.face_detection()):
        face_recognition_detection()

    elif any(word in converted.lower() for word in keywords.speed_test()):
        speed_test()

    elif any(word in converted.lower() for word in keywords.bluetooth()):
        if operating_system == 'Darwin':
            bluetooth(phrase=converted.lower())
        elif operating_system == 'Windows':
            speaker.say("Bluetooth connectivity on Windows hasn't been developed sir!")

    elif any(word in converted.lower() for word in keywords.brightness()):
        checker = converted.lower()
        if operating_system == 'Darwin':
            speaker.say(random.choice(ack))
            if 'set' in checker or re.findall(r'\b\d+\b', checker):
                level = re.findall(r'\b\d+\b', checker)  # gets integers from string as a list
                level = level if level else ['50']  # pass as list for brightness, as args must be iterable
                Thread(target=set_brightness, args=level).start()
            elif 'decrease' in checker or 'reduce' in checker or 'lower' in checker or 'dark' in checker or \
                    'dim' in checker:
                Thread(target=decrease_brightness).start()
            elif 'increase' in checker or 'bright' in checker or 'max' in checker or 'brighten' in checker or \
                    'light up' in checker:
                Thread(target=increase_brightness).start()
        elif operating_system == 'Windows':
            speaker.say("Modifying screen brightness on Windows hasn't been developed sir!")

    elif any(word in converted.lower() for word in keywords.lights()):
        converted = [converted.lower()]
        speaker.say(random.choice(ack))
        Thread(target=lights, args=converted).start()

    elif any(word in converted.lower() for word in keywords.guard_enable() or keywords.guard_disable()):
        stop_flag = 'False'
        guard_start = Thread(target=guard, args=[stop_flag])
        if any(word in converted.lower() for word in keywords.guard_enable()):
            logger.fatal('\nEnabled Security Mode\n')
            speaker.say(f"Enabled security mode sir! I will look out for potential threats and keep you posted. "
                        f"Have a nice {greeting()}, and enjoy yourself sir!")
            speaker.runAndWait()
            guard_start.start()
            return
        else:
            # noinspection PyUnusedLocal
            stop_flag = 'True'
            guard_start.join()
            logger.fatal('\nDisabled Security Mode\n')
            speaker.say(f'Welcome back sir! Good {greeting()}.')

    elif any(word in converted.lower() for word in conversation.greeting()):
        speaker.say('I am spectacular. I hope you are doing fine too.')

    elif any(word in converted.lower() for word in conversation.capabilities()):
        speaker.say('There is a lot I can do. For example: I can get you the weather at any location, news around '
                    'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                    'system configuration, tell your investment details, locate your phone, find distance between '
                    'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
                    ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')

    elif any(word in converted.lower() for word in conversation.languages()):
        speaker.say("Tricky question!. I'm configured in python, and I can speak English.")

    elif any(word in converted.lower() for word in conversation.whats_up()):
        speaker.say("My listeners are up. There is nothing I cannot process. So ask me anything..")

    elif any(word in converted.lower() for word in conversation.what()):
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")

    elif any(word in converted.lower() for word in conversation.who()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")

    elif any(word in converted.lower() for word in conversation.about_me()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")
        speaker.say("I can seamlessly take care of your daily tasks, and also help with most of your work!")

    elif any(word in converted.lower() for word in keywords.restart()):
        restart()

    elif any(word in converted.lower() for word in keywords.kill()):
        exit_process()
        Alarm(None, None, None)
        Reminder(None, None, None, None)

    elif any(word in converted.lower() for word in keywords.shutdown()):
        shutdown()

    elif any(word in converted.lower() for word in keywords.chatbot()):
        chatter_bot()

    else:
        if maps_api(converted):
            if google(converted):
                # if none of the conditions above are met, it writes your statement to an yaml file for future training
                train_file = {'Uncategorized': converted}
                if os.path.isfile('training_data.yaml'):
                    with open(r'training_data.yaml', 'r') as reader:
                        content = reader.read()
                        for key, value in train_file.items():
                            if str(value) not in content:  # avoids duplication in yaml file
                                dict_file = [{key: [value]}]
                                with open(r'training_data.yaml', 'a') as writer:
                                    yaml.dump(dict_file, writer)
                else:
                    for key, value in train_file.items():
                        train_file = [{key: [value]}]
                    with open(r'training_data.yaml', 'a') as writer:
                        yaml.dump(train_file, writer)

                # if none of the conditions above are met, opens a google search on default browser
                sys.stdout.write(f"\r{converted}")
                if maps_api.has_been_called:
                    maps_api.has_been_called = False
                    speaker.say("I have also opened a google search for your request.")
                else:
                    speaker.say(f"I heard {converted}. Let me look that up.")
                    speaker.runAndWait()
                    speaker.say("I have opened a google search for your request.")
                search = str(converted).replace(' ', '+')
                unknown_url = f"https://www.google.com/search?q={search}"
                webbrowser.open(unknown_url)


def location_services(device):
    """Initiates geo_locator and stores current location info as json so it could be used in couple of other functions
    device is the argument passed when locating a particular apple device"""
    try:
        # tries with icloud api to get your device's location for precise location services
        if not device:
            device = device_selector(None)
        raw_location = device.location()
        if not raw_location and place_holder == 'Apple':
            return 'None', 'None', 'None'
        elif not raw_location:
            raise PyiCloudAPIResponseException
        else:
            current_lat_ = raw_location['latitude']
            current_lon_ = raw_location['longitude']
    except (PyiCloudAPIResponseException, PyiCloudFailedLoginException):
        # uses latitude and longitude information from your IP's client when unable to connect to icloud
        current_lat_ = st.results.client['lat']
        current_lon_ = st.results.client['lon']
        speaker.say("I have trouble accessing the i-cloud API, so I'll be using your I.P address to get your location. "
                    "Please note that - this may not be accurate enough for location services.")
        speaker.runAndWait()
    except requests.exceptions.ConnectionError:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet. Please check your connection settings and retry.")
        speaker.runAndWait()
        return exit(1)

    try:
        # Uses the latitude and longitude information and converts to the required address.
        locator = geo_locator.reverse(f'{current_lat_}, {current_lon_}')
        location_info_ = locator.raw['address']
    except (GeocoderUnavailable, GeopyError):
        speaker.say('Received an error while retrieving your address sir! I think a restart should fix this.')
        return restart()

    return current_lat_, current_lon_, location_info_


def report():
    """Initiates a list of function that I tend to check first thing in the morning"""
    sys.stdout.write("\rStarting today's report")
    report.has_been_called = True
    current_date()
    current_time(None)
    weather(None)
    todo()
    gmail()
    robinhood()
    news()
    report.has_been_called = False


def current_date():
    """Says today's date and adds the current time in speaker queue if report or time_travel function was called"""
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
        speaker.say(f'The current time is, ')


def current_time(place):
    """Says current time at the requested location if any else with respect to the current timezone"""
    if place:
        from timezonefinder import TimezoneFinder
        import pytz
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
        datetime_zone = datetime.now(pytz.timezone(zone))
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
    """opens up a webpage using your default browser to the target host. If no target received, will ask for
    user confirmation. If no '.' in the phrase heard, phrase will default to .com"""
    host = []
    try:
        [host.append(i) for i in target]
    except TypeError:
        host = None
    if not host:
        global place_holder
        speaker.say("Which website shall I open sir?")
        speaker.runAndWait()
        converted = listener(3, 5)
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
            webbrowser.open(web_url)
        speaker.say(f"I have opened {host}")


def weather(place):
    """Says weather at any location if a specific location is mentioned
    Says weather at current location by getting IP using reverse geocoding if no place is received"""
    sys.stdout.write('\rGetting your weather info')
    api_key = os.getenv('weather_api') or aws.weather_api()
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
    weather_url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}'
    r = urlopen(weather_url)  # sends request to the url created
    response = json.loads(r.read())  # loads the response in a json

    weather_location = f'{city} {state}'.replace('None', '') if city != state else city or state
    temperature = response['current']['temp']
    condition = response['current']['weather'][0]['description']
    feels_like = response['current']['feels_like']
    maxi = response['daily'][0]['temp']['max']
    high = int(round(pytemperature.k2f(maxi), 2))
    mini = response['daily'][0]['temp']['min']
    low = int(round(pytemperature.k2f(mini), 2))
    temp_f = int(round(pytemperature.k2f(temperature), 2))
    temp_feel_f = int(round(pytemperature.k2f(feels_like), 2))
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
            weather_suggest = "I would not consider thick clothes today."
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


def weather_condition(place, msg):
    """Weather report when your phrase has conditions in it like tomorrow, day after, next week and specific part
    of the day etc. weather_condition() uses conditional blocks to fetch keywords and determine the output"""
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
    api_key = os.getenv('weather_api') or aws.weather_api()
    api_endpoint = "http://api.openweathermap.org/data/2.5/"
    weather_url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}'
    r = urlopen(weather_url)  # sends request to the url created
    response = json.loads(r.read())  # loads the response in a json
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
    temperature = response['daily'][key]['temp'][when]
    feels_like = response['daily'][key]['feels_like'][when]
    condition = response['daily'][key]['weather'][0]['description']
    sunrise = response['daily'][key]['sunrise']
    sunset = response['daily'][key]['sunset']
    maxi = response['daily'][key]['temp']['max']
    mini = response['daily'][1]['temp']['min']
    high = int(round(pytemperature.k2f(maxi), 2))
    low = int(round(pytemperature.k2f(mini), 2))
    temp_f = int(round(pytemperature.k2f(temperature), 2))
    temp_feel_f = int(round(pytemperature.k2f(feels_like), 2))
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
    """gets your system configuration for both mac and windows"""
    import shutil
    total, used, free = shutil.disk_usage("/")
    total = size_converter(total)
    used = size_converter(used)
    free = size_converter(free)
    ram = size_converter(virtual_memory().total).replace('.0', '')
    ram_used = size_converter(virtual_memory().percent).replace(' B', ' %')
    cpu = str(os.cpu_count())
    if operating_system == 'Windows':
        o_system = platform.uname()[0] + platform.uname()[2]
    elif operating_system == 'Darwin':
        o_system = (platform.platform()).split('.')[0]
    else:
        o_system = None
    speaker.say(f"You're running {o_system}, with {cpu} cores. Your physical drive capacity is {total}. "
                f"You have used up {used} of space. Your free space is {free}. Your RAM capacity is {ram}. "
                f"You are currently utilizing {ram_used} of your memory.")


def wikipedia_():
    """gets any information from wikipedia using it's API"""
    global place_holder
    import wikipedia
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
                summary = wikipedia.summary(keyword)
            except wikipedia.exceptions.DisambiguationError as e:  # checks for the right keyword in case of 1+ matches
                sys.stdout.write(f'\r{e}')
                speaker.say('Your keyword has multiple results sir. Please pick any one displayed on your screen.')
                speaker.runAndWait()
                keyword1 = listener(3, 5)
                if keyword1 != 'SR_ERROR':
                    summary = wikipedia.summary(keyword1)
                else:
                    summary = None
            except wikipedia.exceptions.PageError:
                speaker.say(f"I'm sorry sir! I didn't get a response for the phrase: {keyword}. Try again!")
                summary = None
                wikipedia_()
            # stops with two sentences before reading whole passage
            formatted = '. '.join(summary.split('. ')[0:2]) + '.'
            speaker.say(formatted)
            speaker.say("Do you want me to continue sir?")  # gets confirmation to read the whole passage
            speaker.runAndWait()
            response = listener(3, 5)
            if response != 'SR_ERROR':
                place_holder = None
                if any(word in response.lower() for word in keywords.ok()):
                    speaker.say('. '.join(summary.split('. ')[3:-1]))
            else:
                sys.stdout.write("\r")
                speaker.say("I'm sorry sir, I didn't get your response.")


def news():
    """Says news around you"""
    news_source = 'fox'
    sys.stdout.write(f'\rGetting news from {news_source} news.')
    from newsapi import NewsApiClient, newsapi_exception
    news_api = NewsApiClient(api_key=os.getenv('news_api') or aws.news_api())
    try:
        all_articles = news_api.get_top_headlines(sources=f'{news_source}-news')
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


def apps(keyword):
    """Launches an application skimmed from your statement and unable to skim asks for the app name"""
    global place_holder
    ignore = ['app', 'application']
    if not keyword or keyword in ignore:
        speaker.say("Which app shall I open sir?")
        speaker.runAndWait()
        keyword = listener(3, 5)
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
        v = (subprocess.check_output("ls /Applications/", shell=True))
        apps_ = (v.decode('utf-8').split('\n'))

        for app in apps_:
            if re.search(keyword, app, flags=re.IGNORECASE) is not None:
                keyword = app

        app_status = os.system(f"open /Applications/'{keyword}'")
        if app_status == 256:
            speaker.say(f"I did not find the app {keyword}. Try again.")
            apps(None)
        else:
            speaker.say(f"I have opened {keyword}")


def robinhood():
    """Gets investment from robinhood api"""
    sys.stdout.write('\rGetting your investment details.')
    from pyrh import Robinhood
    u = os.getenv('robinhood_user') or aws.robinhood_user()
    p = os.getenv('robinhood_pass') or aws.robinhood_pass()
    q = os.getenv('robinhood_qr') or aws.robinhood_qr()
    rh = Robinhood()
    rh.login(username=u, password=p, qr_code=q)
    raw_result = rh.positions()
    result = raw_result['results']
    from helper_functions.robinhood import watcher
    stock_value = watcher(rh, result)
    sys.stdout.write(f'\r{stock_value}')
    speaker.say(stock_value)
    speaker.runAndWait()
    sys.stdout.write("\r")


def repeater():
    """Repeats what ever you say"""
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
    """Initiates chat bot, currently not supported for Windows"""
    global place_holder
    file1 = 'db.sqlite3'
    if operating_system == 'Darwin':
        file2 = f"/Users/{os.environ.get('USER')}/nltk_data"
    elif operating_system == 'Windows':
        file2 = f"{os.getenv('APPDATA')}\\nltk_data"
    else:
        file2 = None
    if os.path.isfile(file1) and os.path.isdir(file2):
        from chatterbot import ChatBot
        from chatterbot.trainers import ChatterBotCorpusTrainer
        bot = ChatBot("Chatterbot", storage_adapter="chatterbot.storage.SQLStorageAdapter")
    else:
        speaker.say('Give me a moment while I train the module.')
        speaker.runAndWait()
        from chatterbot import ChatBot
        from chatterbot.trainers import ChatterBotCorpusTrainer
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
            os.system('rm db*')
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
            os.system('rm db*')
            os.system(f'rm -rf {file2}')
        else:
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            chatter_bot()


def device_selector(converted):
    """Returns the device name from the user's input after checking the apple devices list.
    Returns your default device when not able to find it."""
    if converted and isinstance(converted, str):
        converted = converted.lower().replace('port', 'pods')
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
        if lookup.lower() in str(device).lower():
            target_device = icloud_api.devices[index]
            break
    if not target_device:
        target_device = icloud_api.iphone
    return target_device


def location():
    """Gets your current location"""
    city, state, country = location_info['city'], location_info['state'], location_info['country']
    speaker.say(f"You're at {city} {state}, in {country}")


def locate(converted):
    """Locates your iPhone using icloud api for python"""
    global place_holder
    target_device = device_selector(converted)
    sys.stdout.write(f"\rLocating your {target_device}")
    if dummy.has_been_called:
        dummy.has_been_called = False
        speaker.say("Would you like to ring it?")
    else:
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
            speaker.say("Would you like to ring it?")
    speaker.runAndWait()
    phrase = listener(3, 5)
    if phrase == 'SR_ERROR':
        if place_holder == 0:
            place_holder = None
        else:
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            place_holder = 0
            locate(converted)
    else:
        place_holder = None
        if any(word in phrase.lower() for word in keywords.ok()):
            speaker.say("Ringing your device now.")
            target_device.play_sound()
            speaker.say("I can also enable lost mode. Would you like to do it?")
            speaker.runAndWait()
            phrase = listener(3, 5)
            if any(word in phrase.lower() for word in keywords.ok()):
                recovery = os.getenv('icloud_recovery') or aws.icloud_recovery()
                message = 'Return my phone immediately.'
                target_device.lost_device(recovery, message)
                speaker.say("I've enabled lost mode on your phone.")
            else:
                speaker.say("No action taken sir!")


def music(device):
    """Scans music directory in your profile for .mp3 files and plays using default player"""
    sys.stdout.write("\rScanning music files...")
    user_profile = os.path.expanduser('~')

    if operating_system == 'Darwin':
        path = os.walk(f"{user_profile}/Music")
    elif operating_system == 'Windows':
        path = os.walk(f"{user_profile}\\Music")
    else:
        path = None

    get_all_files = (os.path.join(root, f) for root, _, files in path for f in files)
    get_music_files = (f for f in get_all_files if os.path.splitext(f)[1] == '.mp3')
    file = []
    for music_file in get_music_files:
        file.append(music_file)
    chosen = random.choice(file)

    if device:
        google_home(device, chosen)
    else:
        if operating_system == 'Darwin':
            subprocess.call(["open", chosen])
        elif operating_system == 'Windows':
            os.system(f'start wmplayer "{chosen}"')
        sys.stdout.write("\r")
        speaker.say("Enjoy your music sir!")
        speaker.runAndWait()
        return


def gmail():
    """Reads unread emails from your gmail account for which the creds are stored in env variables"""
    global place_holder
    sys.stdout.write("\rFetching new emails..")
    import email
    import imaplib
    from email.header import decode_header, make_header

    u = os.getenv('gmail_user') or aws.gmail_user()
    p = os.getenv('gmail_pass') or aws.gmail_pass()

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(u, p)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError as TimeOut:
        logger.info(TimeOut)
        speaker.say("I wasn't able to check your emails sir. You might need to check to logs.")
        speaker.runAndWait()
        return

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')  # looks for unread emails
    if return_code == 'OK':
        for _ in messages[0].split():
            n = n + 1
    else:
        speaker.say("I'm unable access your email sir.")
    if n == 0:
        speaker.say("You don't have any emails to catch up sir")
        speaker.runAndWait()
    else:
        speaker.say(f'You have {n} unread emails sir. Do you want me to check it?')  # user check before reading subject
        speaker.runAndWait()
        response = listener(3, 5)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.ok()):
                for nm in messages[0].split():
                    ignore, mail_data = mail.fetch(nm, '(RFC822)')
                    for response_part in mail_data:
                        if isinstance(response_part, tuple):  # checks for type(response_part)
                            original_email = email.message_from_bytes(response_part[1])
                            sender = (original_email['From']).split(' <')[0]
                            sub = make_header(decode_header(original_email['Subject'])) \
                                if original_email['Subject'] else None
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
                            sys.stdout.write(f'\rReceived:{receive}::{received_date}\tSender: {sender}\tSubject: {sub}')
                            speaker.say(f"You have an email from, {sender}, with subject, {sub}, {receive}")
                            speaker.runAndWait()
        else:
            if place_holder == 0:
                place_holder = None
            else:
                speaker.say("I didn't quite get that. Try again.")
                speaker.runAndWait()
                place_holder = 0
                gmail()

        place_holder = None
    if report.has_been_called or time_travel.has_been_called:
        speaker.runAndWait()


def meaning(keyword):
    """Gets meaning for a word skimmed from your statement using PyDictionary"""
    global place_holder
    from PyDictionary import PyDictionary
    dictionary = PyDictionary()
    if keyword == 'word':
        keyword = None
    if keyword is None:
        speaker.say("Please tell a keyword.")
        speaker.runAndWait()
        response = listener(3, 5)
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
            response = listener(3, 5)
            if any(word in response.lower() for word in keywords.ok()):
                for letter in list(keyword.lower()):
                    speaker.say(letter)
                speaker.runAndWait()
        else:
            speaker.say("Keyword should be a single word sir! Try again")
            meaning(None)
    return


def create_db():
    """Creates a database for to-do list by calling the create_db() function in helper_functions/database.py"""
    speaker.say(database.create_db())
    if todo.has_been_called:
        todo.has_been_called = False
        todo()
    elif add_todo.has_been_called:
        add_todo.has_been_called = False
        add_todo()
    return


def todo():
    """Says the item and category stored in your to-do list"""
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
        key = listener(3, 5)
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
    """Adds new items to your to-do list"""
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    # if database file is not found calls create_db()
    if not os.path.isfile(file_name):
        sys.stdout.write("\r")
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
        key = listener(3, 5)
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
    item = listener(3, 6)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            speaker.say('Your to-do list has been left intact sir.')
        else:
            sys.stdout.write(f"\rItem: {item}")
            speaker.say(f"I heard {item}. Which category you want me to add it to?")
            speaker.runAndWait()
            category = listener(3, 5)
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
                category_continue = listener(3, 5)
                if any(word in category_continue.lower() for word in keywords.ok()):
                    add_todo()
                else:
                    speaker.say('Alright')
    else:
        sys.stdout.write("\r")
        speaker.say("I didn't quite get that.")
    place_holder = None


def delete_todo():
    """Deletes items from an existing to-do list"""
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
    """Deletes your database file after getting confirmation"""
    global place_holder
    if not os.path.isfile(file_name):
        speaker.say(f'I did not find any database sir.')
        return
    else:
        speaker.say(f'{random.choice(confirmation)} delete your database?')
        speaker.runAndWait()
        response = listener(3, 5)
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


def distance(starting_point, destination):
    """Calibrates distance between starting point and destination. This function doesn't care about the starting point
    If starting point is None, it gets the distance from your current location to destination. If destination is None,
    it asks for a destination from user"""
    global place_holder
    if not destination:
        speaker.say("Destination please?")
        speaker.runAndWait()
        destination = listener(3, 5)
        if destination != 'SR_ERROR':
            if len(destination.split()) > 2:
                speaker.say("I asked for a destination sir, not a sentence. Try again.")
                distance(starting_point=None, destination=None)
            if 'exit' in destination or 'quit' in destination or 'Xzibit' in destination:
                return
        else:
            if place_holder == 0:
                place_holder = None
                return
            else:
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                distance(starting_point=None, destination=None)
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
            drive_time = math.ceil(t_taken)
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


def locate_places(place):
    """Gets location details of a place"""
    global place_holder
    if not place:
        speaker.say("Tell me the name of a place!")
        speaker.runAndWait()
        converted = listener(3, 5)
        if converted != 'SR_ERROR':
            if 'exit' in place or 'quit' in place or 'Xzibit' in place:
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


def directions(place):
    """Opens google maps for a route between starting and destination.
    Uses reverse geocoding to calculate latitude and longitude for both start and destination."""
    global place_holder
    if not place:
        speaker.say("You might want to give a location.")
        speaker.runAndWait()
        converted = listener(3, 5)
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
    webbrowser.open(maps_url)
    speaker.say("Directions on your screen sir!")
    if start_country and end_country:
        if re.match(start_country, end_country, flags=re.IGNORECASE):
            directions.has_been_called = True
            distance(starting_point=None, destination=place)
        else:
            speaker.say("You might need a flight to get there!")
    return


def alarm(msg):
    """Passes hour, minute and am/pm to Alarm class which initiates a thread for alarm clock in the background"""
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
                speaker.say(f"{random.choice(ack)} I will wake you up at {hour}:{minute} {am_pm}.")
            else:
                speaker.say(f"{random.choice(ack)} Alarm has been set for {hour}:{minute} {am_pm}.")
            sys.stdout.write(f"\rAlarm has been set for {hour}:{minute} {am_pm} sir!")
        else:
            speaker.say(f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                        f"I don't think a time like that exists on Earth.")
    else:
        speaker.say('Please tell me a time sir!')
        speaker.runAndWait()
        converted = listener(3, 5)
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
    """Removes lock file to stop the alarm which rings only when the certain lock file is present
    alarm_state is the list of lock files currently present"""
    global place_holder
    alarm_state = []
    [alarm_state.append(file) if file != '.keep' else None for file in os.listdir('alarm')]
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
        converted = listener(3, 5)
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


def google_home(device, file):
    """Uses socket lib to extract ip address and scans ip range for google home devices and play songs in your local.
    Can also play music on multiple devices at once.
    Changes made to google-home-push module:
        * Modified the way local IP is received: https://github.com/deblockt/google-home-push/pull/7
        * Instead of commenting/removing the final print statement on: site-packages/googlehomepush/__init__.py
        I have used "sys.stdout = open(os.devnull, 'w')" to suppress any print statements. To enable this again at a
        later time use "sys.stdout = sys.__stdout__"
    Note: When music is played and immediately stopped/tasked the google home device, it is most likely to except
     Broken Pipe error. This usually happens when you write to a socket that is fully closed.
     Broken Pipe occurs when one end of the connection tries sending data while the other end has closed the connection.
    This can simply be ignored or handled using the below in socket module (NOT PREFERRED).
    ''' except IOError as error:
            import errno
            if error.errno != errno.EPIPE:
                sys.stdout.write(error)
                pass'''
    """
    speaker.say('Scanning your IP range for Google Home devices sir!')
    speaker.runAndWait()
    sys.stdout.write('\rScanning your IP range for Google Home devices..')
    from googlehomepush import GoogleHome
    from pychromecast.error import ChromecastConnectionError
    network_id = vpn_checker()
    if not network_id:
        return

    def ip_scan(host_id):
        """Scans the IP range using the received args as host id in an IP address"""
        try:
            device_info = GoogleHome(host=f"{network_id}.{host_id}").cc
            device_info = str(device_info)
            device_name = device_info.split("'")[3]
            device_ip = device_info.split("'")[1]
            # port = sample.split("'")[2].split()[1].replace(',', '')
            return device_name, device_ip
        except ChromecastConnectionError:
            pass

    from concurrent.futures import ThreadPoolExecutor  # scan time after MultiThread: < 10 seconds (usual bs: 3 minutes)
    devices = []
    with ThreadPoolExecutor(max_workers=5000) as executor:  # max workers set to 5K (to scan 255 IPs) for less wait time
        for info in executor.map(ip_scan, range(1, 256)):  # scans host IDs 1 to 255 (eg: 192.168.1.1 to 192.168.1.255)
            devices.append(info)  # this includes all the NoneType values returned by unassigned host IDs
    devices = dict([i for i in devices if i])  # removes None values and converts list to dictionary of name and ip pair

    if not device or not file:
        sys.stdout.write("\r")

        def comma_separator(list_):
            """Seperates commas using simple .join() function and analysis based on length of the list (args)"""
            return ', and '.join([', '.join(list_[:-1]), list_[-1]] if len(list_) > 2 else list_)

        speaker.say(f"You have {len(devices)} devices in your IP range sir! {comma_separator(list(devices.keys()))}. "
                    f"You can choose one and ask me to play some music on any of these.")
        return
    else:
        from googlehomepush.http_server import serve_file
        chosen = []
        [chosen.append(value) if key.lower() in device.lower() else None for key, value in devices.items()]
        if not chosen:
            speaker.say("I don't see any matching devices sir!. Let me help you.")
            google_home(None, None)
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
    """Uses jokes lib to say chucknorris jokes"""
    global place_holder
    from joke.jokes import geek, icanhazdad, chucknorris, icndb
    speaker.say(random.choice([geek, icanhazdad, chucknorris, icndb])())
    speaker.runAndWait()
    speaker.say("Do you want to hear another one sir?")
    speaker.runAndWait()
    converted = listener(3, 5)
    if converted != 'SR_ERROR':
        place_holder = None
        if any(word in converted.lower() for word in keywords.ok()):
            jokes()
    return


def reminder(converted):
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder"""
    global place_holder
    message = re.search(' to (.*) at ', converted) or re.search(' about (.*) at ', converted)
    if not message:
        message = re.search(' to (.*)', converted) or re.search(' about (.*)', converted)
        if not message:
            speaker.say('Reminder format should be::Remind me to do something, at some time.')
            sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
            return
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
        r'([0-9]+\s?(?:a.m.|p.m.:?))', converted)
    if not extracted_time:
        speaker.say("When do you want to be reminded sir?")
        speaker.runAndWait()
        converted = listener(3, 5)
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
            speaker.say(f"{random.choice(ack)} I will remind you {to_about} {message}, at {hour}:{minute} {am_pm}.")
            sys.stdout.write(f"\r{message} at {hour}:{minute} {am_pm}")
        else:
            speaker.say(f"A reminder at {hour}:{minute} {am_pm}? Are you an alien? "
                        f"I don't think a time like that exists on Earth.")
    else:
        speaker.say('Reminder format should be::Remind me to do something, at some time.')
        sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
    return


def maps_api(query):
    """Uses google's places api to get places near by or any particular destination.
    This function is triggered when the words in user's statement doesn't match with any predefined functions."""
    global place_holder
    api_key = os.getenv('maps_api') or aws.maps_api()
    maps_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    response = requests.get(maps_url + 'query=' + query + '&key=' + api_key)
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
        converted = listener(3, 5)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                break
            elif any(word in converted.lower() for word in keywords.ok()):
                place_holder = None
                maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
                webbrowser.open(maps_url)
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
            maps_api.has_been_called = True
            return True


def notes():
    """Listens to the user and saves everything to a notes.txt file"""
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


def github(target):
    """Clones the github repository matched with existing repository in conditions()
    Asks confirmation if the results are more than 1 but less than 3 else asks to be more specific"""
    global place_holder
    home = os.path.expanduser('~')
    if len(target) == 1:
        os.system(f"""cd {home} && git clone -q {target[0]}""")
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
            os.system(f"""cd {home} && git clone {target[item]}""")
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


def send_sms(number):
    """Sends a message to the number received. If no number was received, it will ask for a number, looks if it is
    10 digits and then sends a message."""
    global place_holder
    import smtplib
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
            converted = listener(3, 5)
            if converted != 'SR_ERROR':
                if not any(word in converted.lower() for word in keywords.ok()):
                    speaker.say("Message will not be sent sir!")
                else:
                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    gmail_user = os.getenv('gmail_user') or aws.gmail_user()
                    gmail_pass = os.getenv('gmail_pass') or aws.gmail_pass()
                    server.login(user=gmail_user, password=gmail_pass)
                    to = f"+1{number}@tmomail.net"
                    subject = "Jarvis::Message from Vignesh"
                    sender = (f"From: {gmail_user}\n" + f"To: {to}\n" + f"Subject: {subject}\n" + "\n\n" + body)
                    server.sendmail(gmail_user, to, sender)
                    server.close()
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


def television(converted):
    """television() controls all actions on a TV. In the main() method tv is set to None if the
    TV class from tv_controls.py fails to connect to the tv, so the television function responds only
    if the request is to turn on the TV, else it exits with a bummer. Once the tv is turned on, the TV
    class is also initiated which is set global for other statements to use it."""
    global tv
    phrase = converted.replace('TV', '')
    if not vpn_checker():
        return
    elif 'wake' in phrase or 'turn on' in phrase or 'connect' in phrase or 'status' in phrase or 'control' in phrase:
        from wakeonlan import send_magic_packet as wake
        try:
            mac_address = os.getenv('tv_mac') or aws.tv_mac()
            wake(mac_address)
            tv = TV()
            speaker.say(f"TV features have been integrated sir!")
        except OSError:
            speaker.say("I wasn't able to connect to your TV sir! Please make sure you are on the "
                        "same network as your TV, and your TV is connected to a power source.")
    elif tv:
        if 'increase' in phrase:
            tv.increase_volume()
            speaker.say(f'{random.choice(ack)}!')
        elif 'decrease' in phrase or 'reduce' in phrase:
            tv.decrease_volume()
            speaker.say(f'{random.choice(ack)}!')
        elif 'mute' in phrase:
            tv.mute()
            speaker.say(f'{random.choice(ack)}!')
        elif 'pause' in phrase or 'hold' in phrase:
            tv.pause()
            speaker.say(f'{random.choice(ack)}!')
        elif 'resume' in phrase or 'play' in phrase:
            tv.play()
            speaker.say(f'{random.choice(ack)}!')
        elif 'rewind' in phrase:
            tv.rewind()
            speaker.say(f'{random.choice(ack)}!')
        elif 'forward' in phrase:
            tv.forward()
            speaker.say(f'{random.choice(ack)}!')
        elif 'stop' in phrase:
            tv.stop()
            speaker.say(f'{random.choice(ack)}!')
        elif 'set' in phrase:
            vol = int(''.join([str(s) for s in re.findall(r'\b\d+\b', phrase)]))
            sys.stdout.write(f'\rRequested volume: {vol}')
            if vol:
                tv.set_volume(vol)
                speaker.say(f"I've set the volume to {vol}% sir.")
            else:
                speaker.say(f"{vol} doesn't match the right format sir!")
        elif 'volume' in phrase:
            speaker.say(f"The current volume on your TV is, {tv.get_volume()}%")
        elif 'what are the apps' in phrase or 'what are the applications' in phrase:
            sys.stdout.write(f'\r{tv.list_apps()}')
            speaker.say('App list on your screen sir!')
            speaker.runAndWait()
            time.sleep(5)
        elif 'open' in phrase or 'launch' in phrase:
            app_name = ''
            for word in phrase.split():
                if word[0].isupper():
                    app_name += word + ' '
            if not app_name:
                speaker.say("I didn't quite get that.")
            try:
                tv.launch_app(app_name.strip())
                speaker.say(f"I've launched {app_name} on your TV sir!")
            except ValueError:
                speaker.say(f"I didn't find the app {app_name} on your TV sir!")
        elif "what's" in phrase or 'currently' in phrase:
            speaker.say(f'{tv.current_app()} is running on your TV.')
        elif 'change' in phrase or 'source' in phrase:
            tv_source = ''
            for word in phrase.split():
                if word[0].isupper():
                    tv_source += word + ' '
            if not tv_source:
                speaker.say("I didn't quite get that.")
            try:
                tv.set_source(tv_source.strip())
                speaker.say(f"I've changed the source to {tv_source}.")
            except ValueError:
                speaker.say(f"I didn't find the source {tv_source} on your TV sir!")
        elif 'shutdown' in phrase or 'shut down' in phrase or 'turn off' in phrase:
            speaker.say('Shutting down the TV now.')
            Thread(target=tv.shutdown).start()
            tv = None
        else:
            speaker.say("I didn't quite get that.")
    else:
        converted = converted.replace('my', 'your')
        speaker.say(f"I'm sorry sir! I wasn't able to {converted}, as the TV state is unknown! You can ask me to "
                    f"turn on or connect to the TV to start using the TV features.")


def google(query):
    """Uses Google's search engine parser and gets the first result that shows up on a google search.
    If it is unable to get the result, Jarvis sends a request to suggestqueries.google.com to rephrase
    the query and then looks up using the search engine parser once again. global suggestion_count is used
    to make sure the suggestions and parsing don't run on an infinite loop."""
    global suggestion_count
    from search_engine_parser.core.engines.google import Search as GoogleSearch
    from search_engine_parser.core.exceptions import NoResultsOrTrafficError
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
        r = requests.get(suggest_url, params)
        try:
            suggestion = r.json()[1][1]
            suggestion_count += 1
            if suggestion_count >= 3:
                suggestion_count = 0
                speaker.say(r.json()[1][0].replace('=', ''))
                speaker.runAndWait()
                maps_api.has_been_called = True
                return True
            else:
                google(suggestion)
        except IndexError:
            return True
    if results:
        output = results[0]
        if '\n' in output:
            required = output.split('\n')
            modify = required[0].strip()
            split_val = ' '.join(splitter(modify.replace('.', 'rEpLaCInG')))
            sentence = split_val.replace(' rEpLaCInG ', '.')
            repeats = []
            [repeats.append(word) for word in sentence.split() if word not in repeats]
            refined = ' '.join(repeats)
            output = refined + required[1] + '.' + required[2]
        match = re.search(r'(\w{3},|\w{3}) (\d,|\d|\d{2},|\d{2}) \d{4}', output)
        if match:
            output = output.replace(match.group(), '')
        sys.stdout.write(f'\r{output}')
        speaker.say(output)
        return
    else:
        return True


def google_search(phrase):
    """Opens up a google search for the phrase received. If nothing was received, gets phrase from user."""
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
    webbrowser.open(unknown_url)
    speaker.say(f"I've opened up a google search for: {phrase}.")


def volume_controller(level):
    """Controls volume from the numbers received. There are no chances for None. If you don't give a volume %
    conditions() is set to assume it as 50% Since Mac(s) run on a volume of 16 bars controlled by 8 digits, I have
    changed the level to become single digit with respect to 8 (eg: 50% becomes 4) for osX"""
    sys.stdout.write("\r")
    if operating_system == 'Darwin':
        level = round((8 * level) / 100)
        os.system(f'osascript -e "set Volume {level}"')
    elif operating_system == 'Windows':
        os.system(f'SetVol.exe {level}')


def face_recognition_detection():
    """Initiates face recognition script and looks for images stored in named directories within 'train' directory."""
    if operating_system == 'Darwin':
        from helper_functions.facial_recognition import Face
        sys.stdout.write("\r")
        train_dir = 'train'
        os.mkdir(train_dir) if train_dir not in current_dir else None
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
            if phrase != 'SR_ERROR':
                if any(word in phrase.lower() for word in keywords.exit()):
                    os.remove('cv2_open.jpg')
                    speaker.say("I've deleted the image.")
                else:
                    sys.stdout.write(f"\r{phrase}")
                    phrase = phrase.replace(' ', '_')
                    # creates a named directory if it is not found already else simply ignores
                    os.system(f'cd {train_dir} && mkdir {phrase}') if phrase not in os.listdir(train_dir) else None
                    c_time = datetime.now().strftime("%I_%M_%p")
                    img_name = f"{phrase}_{c_time}.jpg"  # adds current time to image name to avoid overwrite
                    os.rename('cv2_open.jpg', img_name)  # renames the files
                    os.system(f"mv {img_name} {train_dir}/{phrase}")  # move files into named directory within train_dir
                    speaker.say(f"Image has been saved as {img_name}. I will be able to recognize {phrase} in the "
                                f"future.")
            else:
                os.remove('cv2_open.jpg')
                speaker.say("I did not get any response, so I've deleted the image.")
        else:
            speaker.say(f'Hi {result}! How can I be of service to you?')
    elif operating_system == 'Windows':
        speaker.say("I am sorry, currently facial recognition and detection is only supported on Windows, due to the "
                    "package installation issues. Is there anything else I can help you with?")


def speed_test():
    """Initiates speed test and says the ping rate, download and upload speed."""
    client_locator = geo_locator.reverse(f"{st.results.client.get('lat')}, {st.results.client.get('lon')}")
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
    speaker.say(f'Ping rate: {ping} milli seconds')
    speaker.say(f'Download speed: {download} per second.')
    speaker.say(F'Upload speed: {upload} per second.')


def bluetooth(phrase):
    """Find and connect to bluetooth devices near by"""
    if 'turn off' in phrase or 'power off' in phrase:
        subprocess.call(f"blueutil --power 0", shell=True)
        sys.stdout.write('\rBluetooth has been turned off')
        speaker.say(f"Bluetooth has been turned off sir!")
    elif 'turn on' in phrase or 'power on' in phrase:
        subprocess.call(f"blueutil --power 1", shell=True)
        sys.stdout.write('\rBluetooth has been turned on')
        speaker.say(f"Bluetooth has been turned on sir!")
    elif 'disconnect' in phrase and ('bluetooth' in phrase or 'devices' in phrase):
        subprocess.call(f"blueutil --power 0", shell=True)
        time.sleep(2)
        subprocess.call(f"blueutil --power 1", shell=True)
        speaker.say('All bluetooth devices have been disconnected sir!')
    else:
        def connector(targets):
            """Scans bluetooth devices in range and establishes connection with the matching device in phrase."""
            connection_attempt = False
            for target in targets:
                if target['name']:
                    target['name'] = unicodedata.normalize("NFKD", target['name'])
                    if any(re.search(line, target['name'], flags=re.IGNORECASE) for line in phrase.split()):
                        connection_attempt = True
                        if 'disconnect' in phrase:
                            output = subprocess.getoutput(f"blueutil --disconnect {target['address']}")
                            if not output:
                                sys.stdout.write(f"\rDisconnected from {target['name']}")
                                time.sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                                speaker.say(f"Disconnected from {target['name']} sir!")
                            else:
                                speaker.say(f"I was unable to disconnect {target['name']} sir!. "
                                            f"Perhaps it was never connected.")
                        elif 'connect' in phrase:
                            output = subprocess.getoutput(f"blueutil --connect {target['address']}")
                            if not output:
                                sys.stdout.write(f"\rConnected to {target['name']}")
                                time.sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                                speaker.say(f"Connected to {target['name']} sir!")
                            else:
                                speaker.say(f"Unable to connect {target['name']} sir!, please make sure the device is "
                                            f"turned on and ready to pair.")
                        break
            return connection_attempt

        sys.stdout.write('\rScanning paired Bluetooth devices')
        paired = subprocess.getoutput("blueutil --paired --format json")
        paired = json.loads(paired)
        if not connector(targets=paired):
            sys.stdout.write('\rScanning UN-paired Bluetooth devices')
            speaker.say('No connections were established sir, looking for un-paired devices.')
            speaker.runAndWait()
            unpaired = subprocess.getoutput("blueutil --inquiry --format json")
            unpaired = json.loads(unpaired)
            connector(targets=unpaired) if unpaired else speaker.say('No un-paired devices found sir! '
                                                                     'You may want to be more precise.')


def increase_brightness():
    """Increases the brightness to maximum in macOS"""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def decrease_brightness():
    """Decreases the brightness to bare minimum in macOS"""
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")


def set_brightness(level):
    """Set brightness to a custom level. Since I'm using in-built apple script,
    the only way to achieve this is to: set the brightness to bare minimum and increase {*}% from there or vice-versa"""
    level = round((32 * int(level)) / 100)
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")
    for _ in range(level):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def lights(converted):
    """Controller for smart lights"""

    from helper_functions.lights import MagicHomeApi

    def turn_off(host):
        controller = MagicHomeApi(device_ip=host, device_type=1)
        controller.turn_off()

    def warm(host):
        controller = MagicHomeApi(device_ip=host, device_type=1)
        controller.update_device(r=0, g=0, b=0, warm_white=255)

    def cool(host):
        controller = MagicHomeApi(device_ip=host, device_type=2)
        controller.update_device(r=255, g=255, b=255, warm_white=255, cool_white=255)

    if 'hallway' in converted:
        light_host_id = [19, 20, 21, 22, 24]
    elif 'kitchen' in converted:
        light_host_id = [25, 26]
    else:
        light_host_id = [19, 20, 21, 22, 24, 25, 26]

    connection_status = vpn_checker()
    if not connection_status:
        return
    else:
        if 'turn on' in converted or 'cool' in converted or 'white' in converted:
            [cool(f'{connection_status}.{i}') for i in light_host_id]
        elif 'turn off' in converted:
            [turn_off(f'{connection_status}.{i}') for i in light_host_id]
        elif 'warm' in converted or 'yellow' in converted:
            [warm(f'{connection_status}.{i}') for i in light_host_id]


def vpn_checker():
    """Uses simple check on network id to see if it is connected to local host or not
    returns the network id if local host"""
    from urllib.request import urlopen
    import json
    socket_ = socket(AF_INET, SOCK_DGRAM)
    socket_.connect(("8.8.8.8", 80))
    ip_address = socket_.getsockname()[0]
    socket_.close()
    if not (ip_address.startswith('192') | ip_address.startswith('127')):
        info = json.load(urlopen('http://ipinfo.io/json'))
        sys.stdout.write(f"\rVPN connection is detected to {info.get('ip')} at {info.get('city')}, "
                         f"{info.get('region')} maintained by {info.get('org')}")
        speaker.say("You have your VPN turned on. Details on your screen sir! Please note that, none of the home "
                    "integrations will work with VPN enabled.")
    else:
        return '.'.join(ip_address.split('.')[0:3])


def celebrate():
    """Function to look if the current date is a holiday or a birthday."""
    day = datetime.today().date()
    today = datetime.now().strftime("%d-%B")
    us_holidays = holidays.CountryHoliday('US').get(day)  # checks if the current date is a US holiday
    in_holidays = holidays.CountryHoliday('IND', prov='TN', state='TN').get(day)  # checks if Indian (esp TN) holiday
    if in_holidays:
        return in_holidays
    elif us_holidays and 'Observed' not in us_holidays:
        return us_holidays
    elif today == os.getenv('birthday') or today == aws.birthday():
        return 'Birthday'


def time_travel():
    """Triggered only from sentry_mode() to give a quick update on your day. Starts the report() in personalized way"""
    speaker.say(f"Good {greeting()} Vignesh.")

    time_travel.has_been_called = True
    current_date()
    current_time(None)
    weather(None)
    todo()
    gmail()
    speaker.say('Would you like to hear the latest news?')
    speaker.runAndWait()
    phrase = listener(3, 5)
    if any(word in phrase.lower() for word in keywords.ok()):
        news()
    time_travel.has_been_called = False
    speaker.say(f"Activating sentry mode, enjoy yourself sir!")
    speaker.runAndWait()
    return


def guard(stop_flag):
    """Security Mode will enable camera and microphone in the background.
    If any speech is recognized or a face is detected, there will another thread triggered to send notifications.
    Notifications will be triggered only after 5 minutes of initial notification."""
    import cv2
    cam_source = None
    for i in range(0, 3):
        cam = cv2.VideoCapture(i)
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            pass
        else:
            cam_source = i
            break
    if cam_source is None:
        raise BlockingIOError
    validation_video = cv2.VideoCapture(cam_source)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    scale_factor = 1.1
    min_neighbors = 5

    notified = None
    while True:
        # Listens for any recognizable speech and saves it to a notes file
        converted = None
        try:
            listened = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            converted = recognizer.recognize_google(listened)
            if any(word in converted.lower() for word in keywords.guard_disable()):
                return
            else:
                logger.fatal(f'Conversation::{converted}')
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            pass

        # captures images and keeps storing it to a folder
        ignore, image = validation_video.read()
        scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(scale, scale_factor, min_neighbors)
        date_extn = f"{datetime.now().strftime('%B_%d_%Y_%I_%M_%S_%p')}"
        try:
            if faces:
                pass
        except ValueError:
            cv2.imwrite(f'threat/{date_extn}.jpg', image)
            logger.fatal(f'Image of detected face stored as {date_extn}.jpg')
        if f'{date_extn}.jpg' not in os.listdir('threat'):
            date_extn = None

        # if no notification was sent yet or if a phrase or face is detected notification thread will be triggered
        if (not notified or float(time.time() - notified) > 300) and (converted or date_extn):
            notified = time.time()
            Thread(target=threat_notify, args=(converted, date_extn)).start()
        else:
            logger.fatal('Waiting for 60 seconds\n')

        # if stop_flag value is received, security mode will be exited
        if stop_flag == 'True':
            return


def threat_notify(converted, date_extn):
    """threat notify is triggered by guard which sends an SMS using SNS and email using SES"""
    dt_string = f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    title_ = f'Intruder Alert on {dt_string}'
    text_ = None

    if converted:
        response = sns.publish(PhoneNumber=aws.phone(),
                               Message=f"!!INTRUDER ALERT!!\n{dt_string}\n{converted}")
        body_ = f"""<html><head></head><body><h2>Conversation of Intruder:</h2><br>{converted}<br><br>
                                    <h2>Attached is a photo of the intruder.</h2>"""
    else:
        response = sns.publish(PhoneNumber=aws.phone(),
                               Message=f"!!INTRUDER ALERT!!\n{dt_string}\nCheck your email for more information.")
        body_ = f"""<html><head></head><body><h2>No conversation was recorded,
                                but attached is a photo of the intruder.</h2>"""
    if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
        logger.fatal('SNS notification has been sent.')
    else:
        logger.fatal(f'Unable to send SNS notification.\n{response}')

    if date_extn:
        attachments_ = [f'threat/{date_extn}.jpg']
        response_ = send_mail(title_, text_, body_, attachments_)
        if response_.get('ResponseMetadata').get('HTTPStatusCode') == 200:
            logger.fatal('Email has been sent!\n')
        else:
            logger.fatal(f'Email dispatch was failed with response: {response_}\n')


def sentry_mode():
    """Sentry mode, all it does is to wait for the right keyword to wake up and get into action.
    threshold is used to sanity check sentry_mode() so that:
     1. Jarvis doesn't run into Fatal Python error
     2. Jarvis restarts at least twice a day and gets a new pid
    morning_msg and evening_msg are set to False initially and to True when their purpose is done for the day.
     this is done to avoid Jarvis repeating the task as it completes within a minute.
     Alternatively, a condition to check and run within first 15 seconds can be implemented."""
    threshold, morning_msg, evening_msg = 0, False, False
    while threshold < 5000:
        threshold += 1
        if not morning_msg and datetime.now().strftime("%I:%M %p") == '07:00 AM':
            # triggers at 7:00 AM and morning_msg is set to True so that,
            # Jarvis would not repeat the same message once again before a restart
            if operating_system == 'Darwin':
                Thread(target=increase_brightness).start()  # set to max brightness
            Thread(target=lights, args=['turn on']).start()  # turns on the lights
            volume_controller(100)
            speaker.say('Good Morning.')
            if event:
                speaker.say(f'Happy {event}!')
            report.has_been_called = True
            current_date()
            current_time(None)
            weather(None)
            speaker.runAndWait()
            report.has_been_called = False
            volume_controller(50)
            morning_msg = True
        if not evening_msg and datetime.now().strftime("%I:%M %p") == '09:00 PM':
            # triggers at 9:00 PM and evening_msg is set to True so that,
            # Jarvis would not repeat the same message once again before a restart
            if operating_system == 'Darwin':
                Thread(target=decrease_brightness).start()  # set to lowest brightness
            Thread(target=lights, args=['turn off']).start()  # turns off the lights
            speaker.say(f'Good Night Sir! Have a pleasant sleep.')
            speaker.runAndWait()
            evening_msg = True
        if greet_check == 'initialized':
            dummy.has_been_called = True
        try:
            sys.stdout.write("\rSentry Mode")
            listen = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            sys.stdout.write(f"\r")
            key = recognizer.recognize_google(listen).lower().strip()
            if key == 'jarvis' or key == 'buddy':
                speaker.say(f'{random.choice(wake_up3)}')
                initialize()
            elif 'good' in key:
                if ('morning' in key or 'night' in key or 'afternoon' in key or 'after noon' in key or
                        'evening' in key) and 'jarvis' in key:
                    if 'night' in key:
                        Thread(target=decrease_brightness).start()
                        Thread(target=lights, args=['turn off']).start()
                    elif 'morning' in key:
                        Thread(target=increase_brightness).start()
                        Thread(target=lights, args=['cool']).start()
                    if event:
                        speaker.say(f'Happy {event}!')
                    time_travel()
            elif 'look alive' in key in key or 'wake up' in key or 'wakeup' in key or 'show time' in key or \
                    'showtime' in key or 'time to work' in key or 'spin up' in key:
                speaker.say(f'{random.choice(wake_up1)}')
                initialize()
            elif 'you there' in key or 'are you there' in key or 'you up' in key:
                speaker.say(f'{random.choice(wake_up2)}')
                initialize()
            elif 'jarvis' in key or 'buddy' in key:
                key = key.replace('jarvis ', '').replace('buddy ', '').replace('hey ', '').replace(' jarvis', '')
                split(key)
            speaker.runAndWait()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            pass
        except KeyboardInterrupt:
            exit_process()
            Alarm(None, None, None)
            Reminder(None, None, None, None)
    speaker.say("My run time has reached the threshold!")
    logger.fatal('Restarting Now')
    volume_controller(20)
    restart()


def size_converter(byte_size):
    """Gets the current memory consumed and converts it to human friendly format"""
    if not byte_size:
        if operating_system == 'Darwin':
            import resource
            byte_size = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        elif operating_system == 'Windows':
            byte_size = Process(os.getpid()).memory_info().peak_wset
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    integer = int(math.floor(math.log(byte_size, 1024)))
    power = math.pow(1024, integer)
    size = round(byte_size / power, 2)
    response = str(size) + ' ' + size_name[integer]
    return response


def exit_message():
    """Variety of exit messages based on day of week and time of day"""
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


def remove_files():
    """Function that deletes all .lock files created for alarms and reminders."""
    [os.remove(f"alarm/{file}") if file != '.keep' else None for file in os.listdir('alarm')]
    [os.remove(f"reminder/{file}") if file != '.keep' else None for file in os.listdir('reminder')]


def exit_process():
    """Function that holds the list of operations done upon exit."""
    alarms, reminders = [], {}
    for file in os.listdir('alarm'):
        if file != '.keep' and file != '.DS_Store':
            alarms.append(file)
    for file in os.listdir('reminder'):
        if file != '.keep' and file != '.DS_Store':
            split_val = file.replace('.lock', '').split('|')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        if len(reminders) == 1:
            speaker.say(f'You have a pending reminder sir!')
        else:
            speaker.say(f'You have {len(reminders)} pending reminders sir!')
        for key, value in reminders.items():
            speaker.say(f"{value.replace('_', ' ')} at "
                        f"{key.replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')}")
    if alarms:
        alarms = ', and '.join(alarms) if len(alarms) != 1 else ''.join(alarms)
        alarms = alarms.replace('.lock', '').replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')
        sys.stdout.write(f"\r{alarms}")
        speaker.say(f'You have a pending alarm at {alarms} sir!')
    if reminders or alarms:
        speaker.say('This will be removed while shutting down!')
    speaker.say('Shutting down now sir!')
    speaker.say(exit_message())
    speaker.runAndWait()
    remove_files()
    sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                     f"\nTotal runtime: {time_converter(time.perf_counter())}")


def restart():
    """restart() triggers restart.py which in turn starts Jarvis after 5 seconds.
    Doing this changes the PID to avoid any Fatal Errors occurred by long running threads."""
    sys.stdout.write(f"\rMemory consumed: {size_converter(0)}\tTotal runtime: {time_converter(time.perf_counter())}")
    speaker.say('Restarting now sir! I will be up and running momentarily.')
    speaker.runAndWait()
    os.system(f'python3 restart.py')
    exit(1)


def shutdown():
    """Gets confirmation and turns off the machine"""
    global place_holder
    speaker.say(f"{random.choice(confirmation)} turn off the machine?")
    speaker.runAndWait()
    converted = listener(3, 5)
    if converted != 'SR_ERROR':
        place_holder = None
        if any(word in converted.lower() for word in keywords.ok()):
            exit_process()
            if operating_system == 'Darwin':
                subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
            elif operating_system == 'Windows':
                os.system("shutdown /s /t 1")
            exit(0)
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


def dummy():
    """dummy function to play around with conditional statements within other functions"""
    return None


if __name__ == '__main__':
    speaker = audio.init()  # initiates speaker
    recognizer = sr.Recognizer()  # initiates recognizer that uses google's translation
    keywords = Keywords()  # stores Keywords() class from helper_functions/keywords.py
    conversation = Conversation()  # stores Conversation() class from helper_functions/conversation.py
    operating_system = platform.system()  # detects current operating system
    current_dir = os.listdir()  # stores the list of files in current directory
    aws = AWSClients()  # initiates AWSClients object to fetch credentials from AWS secrets
    database = Database()  # initiates Database() for TO-DO items
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 100)  # increases the recursion limit by 100 times
    sns = boto3.client('sns')

    # Voice ID::reference
    sys.stdout.write(f'\rVoice ID::Female: 1/17 Male: 0/7')

    voices = speaker.getProperty("voices")  # gets the list of voices available

    if operating_system == 'Darwin':
        # noinspection PyTypeChecker,PyUnresolvedReferences
        speaker.setProperty("voice", voices[7].id)  # voice module #7 for MacOS
    elif operating_system == 'Windows':
        # noinspection PyTypeChecker,PyUnresolvedReferences
        speaker.setProperty("voice", voices[0].id)  # voice module #0 for Windows
        speaker.setProperty('rate', 190)  # speech rate is slowed down in Windows for optimal experience
        if 'SetVol.exe' not in current_dir:
            sys.stdout.write("\rPLEASE WAIT::Downloading volume controller for Windows")
            os.system("""curl https://thevickypedia.com/Jarvis/SetVol.exe --output SetVol.exe --silent""")
            sys.stdout.write("\r")
    else:
        operating_system = None
        exit(0)

    # place_holder is used in all the functions so that the "I didn't quite get that..." part runs only once
    # greet_check is used in initialize() to greet only for the first run
    # tv is set to None instead of TV() at the start to avoid turning on the TV unnecessarily
    # suggestion_count is used in google_searchparser to limit the number of times suggestions are used.
        # This is just a safety check so that Jarvis doesn't run into infinite loops while looking for suggestions.
    place_holder, greet_check, tv = None, None, None
    suggestion_count = 0

    # Uses speed test api to check for internet connection
    try:
        st = Speedtest()
    except ConfigRetrievalError:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet sir! Please check your connection settings and retry.")
        speaker.runAndWait()
        st = None
        exit(1)

    # stores icloud creds and necessary values for geo location to receive the latitude, longitude and address
    icloud_user = os.getenv('icloud_user') or aws.icloud_user()
    icloud_pass = os.getenv('icloud_pass') or aws.icloud_pass()
    options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())
    geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)
    current_lat, current_lon, location_info = location_services(device_selector(None))

    # different responses for different conditions in sentry mode
    wake_up1 = ['Up and running sir.', "We are online and ready sir.", "I have indeed been uploaded sir!",
                'My listeners have been activated sir!']
    wake_up2 = ['For you sir - Always!', 'At your service sir.']
    wake_up3 = ["I'm here sir!."]

    confirmation = ['Requesting confirmation sir! Did you mean', 'Sir, are you sure you want to']
    ack = ['Check', 'Will do sir!', 'You got it sir!', 'Roger that!', 'Done sir!', 'By all means sir!', 'Indeed sir!',
           'Gladly sir!', 'Without fail sir!', 'Sure sir!', 'Buttoned up sir!', 'Executed sir!']

    weekend = ['Friday', 'Saturday']

    # {function_name}.has_been_called is use to denote which function has triggered the other
    report.has_been_called, locate_places.has_been_called, directions.has_been_called, maps_api.has_been_called, \
        time_travel.has_been_called = False, False, False, False, False
    for functions in [dummy, delete_todo, todo, add_todo]:
        functions.has_been_called = False

    # triggers celebrate function and wishes for a event if found.
    event = celebrate()

    volume_controller(50)
    sys.stdout.write(f"\rCurrent Process ID: {Process(os.getpid()).pid}\tCurrent Volume: 50%")

    # Initiates logger to log start time, restart time and results from security mode
    logging.basicConfig(filename='threshold.log', filemode='a', level=logging.FATAL,
                        format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger('jarvis.py')
    logger.fatal('Starting Now')

    # starts sentry mode
    playsound('indicators/initialize.mp3')
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        sentry_mode()
