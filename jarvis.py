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
import webbrowser
from datetime import datetime, timedelta
from logging.config import dictConfig
from urllib.request import urlopen

import certifi
import pyttsx3 as audio
import requests
import speech_recognition as sr
import yaml
from geopy.distance import geodesic
from geopy.geocoders import Nominatim, options
from inflect import engine
from playsound import playsound
from psutil import Process, virtual_memory
from punctuator import Punctuator
from pyicloud import PyiCloudService
from requests.auth import HTTPBasicAuth
from wordninja import split as splitter

from alarm import Alarm
from helper_functions.aws_clients import AWSClients
from helper_functions.conversation import Conversation
from helper_functions.database import Database, file_name
from helper_functions.keywords import Keywords
from reminder import Reminder

# the following will allow only critical alerts from Jarvis and suppress the rest (mostly from imported packages)
logger = logging.getLogger('J.A.R.V.I.S')
logger.setLevel(level=logging.CRITICAL)
dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})

# TODO: include face recognition


def initialize():
    """Function to initialize when woke up from sleep mode. greet_check and dummy are to ensure greeting is given only
    for the first time, the script is run place_holder is set for all the functions so that the function runs only ONCE
    again in case of an exception"""
    global place_holder, greet_check
    greet_check = 'initialized'
    if dummy.has_been_called:
        speaker.say("What can I do for you?")
        dummy.has_been_called = False
    elif current == 'AM' and int(clock) < 10:
        speaker.say("Good Morning.")
    elif current == 'AM' and int(clock) >= 10:
        speaker.say("Hope you're having a nice morning.")
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 3):
        speaker.say("Good Afternoon.")
    elif current == 'PM' and int(clock) < 6:
        speaker.say("Good Evening.")
    else:
        speaker.say("Hope you're having a nice night.")
    speaker.runAndWait()

    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            received = recognizer.recognize_google(listener)
            place_holder = None
            return conditions(received)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            renew()


def renew():
    """renew() function resets the waiter count which indeed sends the alive() function to sentry mode after a minute"""
    global waiter
    waiter = 0
    alive()


def alive():
    """alive() function will keep listening and send the response to conditions() This function runs only for a minute
    and goes to sentry_mode() if nothing is heard"""
    global waiter
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3') if waiter == 0 else \
                sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3') if waiter == 0 else sys.stdout.write("\r")
            converted = recognizer.recognize_google(listener)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if waiter == 12:  # waits for a minute and goes to sleep
                sentry_mode()
            waiter += 1
            alive()
        if any(word in converted.lower() for word in keywords.sleep()):
            speaker.say(f"Activating sentry mode, enjoy yourself sir!")
            speaker.runAndWait()
            sentry_mode()
        else:
            conditions(converted)


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
    if any(word in converted.lower() for word in keywords.date()):
        date()

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
        if place:
            weather(place)
        else:
            weather(None)

    elif any(word in converted.lower() for word in keywords.system_info()):
        system_info()

    elif any(word in converted.lower() for word in keywords.webpage()) and \
            not any(word in converted.lower() for word in keywords.avoid()):
        converted = converted.replace(' In', 'in').replace(' Co. Uk', 'co.uk')
        host = (word for word in converted.split() if '.' in word)
        webpage(host)

    elif any(word in converted.lower() for word in keywords.wikipedia()):
        wiki_pedia()

    elif any(word in converted.lower() for word in keywords.news()):
        news()

    elif any(word in converted.lower() for word in keywords.report()):
        report()

    elif any(word in converted.lower() for word in keywords.robinhood()):
        robinhood()

    elif any(word in converted.lower() for word in keywords.apps()):
        apps(converted.split()[-1])

    elif any(word in converted.lower() for word in keywords.repeat()):
        repeater()

    elif any(word in converted.lower() for word in keywords.location()):
        location()

    elif any(word in converted.lower() for word in keywords.locate()):
        locate()

    elif any(word in converted.lower() for word in keywords.music()):
        if 'speaker' in converted.lower() or 'tv' in converted.lower():
            music(converted)
        else:
            music(None)

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

    elif any(word in converted.lower() for word in keywords.geopy()):
        # tries to look for words starting with an upper case letter
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        # if no words found starting with an upper case letter, fetches word after the keyword 'is' eg: where is chicago
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

    elif any(word in converted.lower() for word in keywords.kill_alarm()):
        kill_alarm()

    elif any(word in converted.lower() for word in keywords.alarm()):
        """uses regex to find numbers in your statement and processes AM and PM information"""
        try:
            extracted_time = re.findall(r'\s([0-9]+\:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
                r'\s([0-9]+\s?(?:a.m.|p.m.:?))', converted)
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
            alarm(hour, minute, am_pm)
        except IndexError:
            alarm(hour=None, minute=None, am_pm=None)

    elif any(word in converted.lower() for word in keywords.google_home()):
        google_home(device=None, file=None)

    elif any(word in converted.lower() for word in keywords.jokes()):
        jokes()

    elif any(word in converted.lower() for word in keywords.reminder()):
        message = re.search('to(.*)at', converted).group(1).strip()
        """uses regex to find numbers in your statement and processes AM and PM information"""
        try:
            extracted_time = re.findall(r'\s([0-9]+\:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
                r'\s([0-9]+\s?(?:a.m.|p.m.:?))', converted)
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
            reminder(hour, minute, am_pm, message)
        except IndexError:
            reminder(hour=None, minute=None, am_pm=None, message=None)

    elif any(word in converted.lower() for word in keywords.notes()):
        notes()

    elif any(word in converted.lower() for word in keywords.github()):
        git_user = os.getenv('git_user') or aws.git_user()
        git_pass = os.getenv('git_pass') or aws.git_pass()
        auth = HTTPBasicAuth(git_user, git_pass)
        request = requests.get(f'https://api.github.com/user/repos?type=all&per_page=100', auth=auth)
        response = request.json()
        result, repos, total, private, archived, licensed = [], [], 0, 0, 0, 0
        for i in range(len(response)):
            total += 1
            private += 1 if response[i]['private'] else 0
            archived += 1 if response[i]['archived'] else 0
            licensed += 1 if response[i]['license'] else 0
            repos.append({response[i]['name'].replace('_', ' ').replace('-', ' '): response[i]['clone_url']})
        if 'how many' in converted:
            speaker.say(f'You have {total} repositories sir, out of which {private} are private, {licensed} '
                        f'are licensed, and {archived} archived.')
            renew()
        [result.append(clone_url) if clone_url not in result and re.search(rf'\b{word}\b', repo.lower()) else None
         for word in converted.lower().split() for item in repos for repo, clone_url in item.items()]
        if result:
            github(target=result)
        else:
            speaker.say("Sorry sir! I did not find that repo.")
            renew()

    elif any(word in converted.lower() for word in keywords.txt_message()):
        number = '-'.join([str(s) for s in re.findall(r'\b\d+\b', converted)])
        send_sms(target=number)

    elif any(word in converted.lower() for word in keywords.google_search()):
        phrase = converted.split('for')[-1] if 'for' in converted else None
        google_search(phrase)

    elif any(word in converted.lower() for word in conversation.greeting()):
        speaker.say('I am spectacular. I hope you are doing fine too.')
        dummy.has_been_called = True
        renew()

    elif any(word in converted.lower() for word in conversation.capabilities()):
        speaker.say('There is a lot I can do. For example: I can get you the weather at any location, news around '
                    'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                    'system configuration, tell your investment details, locate your phone, find distance between '
                    'places, set an alarm, scan smart devices in your IP range, and play music, tell a joke, send '
                    'a message, remind you to do something, clone a GitHub repository, and much more. Time to ask,.')
        dummy.has_been_called = True
        renew()

    elif any(word in converted.lower() for word in conversation.languages()):
        speaker.say("Tricky question!. I'm configured in python, and I can speak English.")
        dummy.has_been_called = True
        renew()

    elif any(word in converted.lower() for word in conversation.form()):
        speaker.say("I am a program, I'm without form.")
        dummy.has_been_called = True
        renew()

    elif any(word in converted.lower() for word in conversation.whats_up()):
        speaker.say("My listeners are up. There is nothing I cannot process. So ask me anything..")
        dummy.has_been_called = True
        renew()

    elif any(word in converted.lower() for word in conversation.what()):
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI")
        renew()

    elif any(word in converted.lower() for word in conversation.who()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        renew()

    elif any(word in converted.lower() for word in conversation.about_me()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        speaker.say("I am a program, I'm without form.")
        speaker.say('There is a lot I can do. For example: I can get you the weather at any location, news around '
                    'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                    'system configuration, tell your investment details, locate your phone, find distance between '
                    'places, set an alarm, scan smart devices in your IP range, and play music, tell a joke, send '
                    'a message, remind you to do something, clone a GitHub repository, and much more. Time to ask,.')
        dummy.has_been_called = True
        renew()

    elif any(word in converted.lower() for word in keywords.exit()):
        speaker.say(f"Activating sentry mode, enjoy yourself sir.")
        speaker.runAndWait()
        sentry_mode()

    elif any(word in converted.lower() for word in keywords.kill()):
        memory_consumed = size_converter()
        speaker.say(f"Shutting down sir!")
        speaker.say(exit_msg)
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {memory_consumed}\nTotal runtime: {time_converter(time.perf_counter())}")
        Alarm(None, None, None)
        Reminder(None, None, None, None)
        exit(0)

    elif any(word in converted.lower() for word in keywords.shutdown()):
        shutdown()

    elif any(word in converted.lower() for word in keywords.chatbot()):
        chatBot()

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
                renew()


def report():
    """Initiates a list of function that I tend to check first thing in the morning"""
    sys.stdout.write("\rStarting today's report")
    report.has_been_called = True
    date()
    current_time(None)
    weather(None)
    todo()
    gmail()
    news()
    report.has_been_called = False
    renew()


def date():
    """Says today's date and skips going to renew() if the function is called by report()"""
    dt_string = datetime.now().strftime("%A, %B")
    date_ = engine().ordinal(datetime.now().strftime("%d"))
    year = datetime.now().strftime("%Y")
    dt_string = dt_string + date_ + ', ' + year
    speaker.say(f'Today is {dt_string}')
    if report.has_been_called:
        pass
    else:
        renew()


def current_time(place):
    """Says current time and skips going to renew() if the function is called by report()"""
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
        speaker.say(f'The current time is: {c_time}.')
    if report.has_been_called:
        pass
    else:
        renew()


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
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener1)
                if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                    renew()
                elif '.' in converted and len(list(converted)) == 1:
                    _target = (word for word in converted.split() if '.' in word)
                    webpage(_target)
                else:
                    converted = converted.lower().replace(' ', '')
                    target_ = [f"{converted}" if '.' in converted else f"{converted}.com"]
                    webpage(target_)
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                webpage(None)
            place_holder = None
    else:
        for web in host:
            web_url = f"https://{web}"
            webbrowser.open(web_url)
        speaker.say(f"I have opened {host}")
        speaker.runAndWait()
        renew()


def weather(place):
    """Says weather at any location and skips going to renew() if the function is called by report()
    Says weather at current location by getting IP using reverse geocoding if no place is received"""
    sys.stdout.write('\rGetting your weather info')
    import pytemperature
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
        city, state, = location_info['city'], location_info['state']
        lat = current_lat
        lon = current_lon
    api_endpoint = "http://api.openweathermap.org/data/2.5/"
    weather_url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}'
    r = urlopen(weather_url)  # sends request to the url created
    response = json.loads(r.read())  # loads the response in a json

    weather_location = f'{city} {state}'.replace('None', '') if city != state else f'{city}' or f'{state}'
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
    if place or not report.has_been_called:
        output = f'The weather at {weather_location} is {temp_f}°F, with a high of {high}, and a low of {low}. ' \
                 f'It currently feels like {temp_feel_f}°F, and the current condition is {condition}.'
    else:
        output = f'You are currently at {weather_location}. The weather at your location is {temp_f}°F, with a high ' \
                 f'of {high}, and a low of {low}. It currently feels Like {temp_feel_f}°F, and the current ' \
                 f'condition is {condition}. Sunrise at {sunrise}. Sunset at {sunset}'
    sys.stdout.write(f"\r{output}")
    speaker.say(output)
    speaker.runAndWait()
    if report.has_been_called:
        pass
    else:
        renew()


def system_info():
    """gets your system configuration for both mac and windows"""
    import shutil

    total, used, free = shutil.disk_usage("/")
    total = f"{(total // (2 ** 30))} GB"
    used = f"{(used // (2 ** 30))} GB"
    free = f"{(free // (2 ** 30))} GB"

    mem = virtual_memory()
    ram = f"{mem.total // (2 ** 30)} GB"

    cpu = str(os.cpu_count())
    if operating_system == 'Windows':
        o_system = platform.uname()[0] + platform.uname()[2]
    elif operating_system == 'Darwin':
        o_system = (platform.platform()).split('.')[0]
    else:
        o_system = None
    speaker.say(f"You're running {o_system}, with {cpu} cores. Your physical drive capacity is {total}. "
                f"You have used up {used} of space. Your free space is {free}. Your RAM capacity is {ram}")
    speaker.runAndWait()
    renew()


def wiki_pedia():
    """gets any information from wikipedia using it's API"""
    global place_holder
    import wikipedia
    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            keyword = recognizer.recognize_google(listener1)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            wiki_pedia()

        place_holder = None
        if 'no' in keyword.lower().split() or 'nope' in keyword.lower().split() or 'thank you' in \
                keyword.lower().split() or "that's it" in keyword.lower().split():
            renew()

        sys.stdout.write(f'\rGetting your info from Wikipedia API for {keyword}')
        try:
            summary = wikipedia.summary(keyword)
        except wikipedia.exceptions.DisambiguationError as e:  # checks for the right keyword in case of 1+ matches
            sys.stdout.write(f'\r{e}')
            speaker.say('Your keyword has multiple results sir. Please pick any one displayed on your screen.')
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            keyword1 = recognizer.recognize_google(listener1)
            summary = wikipedia.summary(keyword1)
        except wikipedia.exceptions.PageError:
            speaker.say(f"I'm sorry sir! I didn't get a response from wikipedia for the phrase: {keyword}. Try again!")
            wiki_pedia()
        # stops with two sentences before reading whole passage
        formatted = punctuation.punctuate(' '.join(splitter(' '.join(summary.split('.')[0:2]))))
        speaker.say(formatted)
        speaker.runAndWait()
        speaker.say("Do you want me to continue?")  # gets confirmation to read the whole passage
        speaker.runAndWait()
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener2 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            response = recognizer.recognize_google(listener2)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            sys.stdout.write("\r")
            speaker.say("I'm sorry sir, I didn't get your response.")
            renew()
        place_holder = None
        if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.ok()):
            speaker.say(''.join(summary.split('.')[3:-1]))
        else:
            pass
        renew()


def news():
    """Says news around you and skips going to renew() if the function is called by report()"""
    source = 'fox'
    sys.stdout.write(f'\rGetting news from {source} news.')
    speaker.say("News around you!")
    from newsapi import NewsApiClient
    newsapi = NewsApiClient(api_key=os.getenv('news_api') or aws.news_api())
    all_articles = newsapi.get_top_headlines(sources=f'{source}-news')

    for article in all_articles['articles']:
        speaker.say(article['title'])
        speaker.runAndWait()

    if report.has_been_called:
        pass
    else:
        renew()


def apps(keyword):
    """Launches an application skimmed from your statement and unable to skim asks for the app name"""
    global place_holder
    ignore = ['app', 'application']
    if (keyword in ignore or keyword is None) and operating_system == 'Windows':
        speaker.say("Please say the app name.")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                keyword = recognizer.recognize_google(listener)
                if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                    renew()
                status = os.system(f'start {keyword}')
                if status == 0:
                    speaker.say(f'I have opened {keyword}')
                    renew()
                else:
                    speaker.say(f"I wasn't able to find the app {keyword}. Try again.")
                    apps(None)
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                apps(None)
            place_holder = None

    elif operating_system == 'Windows':
        status = os.system(f'start {keyword}')
        if status == 0:
            speaker.say(f'I have opened {keyword}')
            renew()
        else:
            speaker.say(f"I wasn't able to find the app {keyword}. Try again.")
            apps(None)
    elif (keyword in ignore or keyword is None) and operating_system == 'Darwin':
        speaker.say("Please say the app name alone.")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                keyword = recognizer.recognize_google(listener)
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                apps(None)

            place_holder = None
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            renew()

        v = (subprocess.check_output("ls /Applications/", shell=True))
        apps_ = (v.decode('utf-8').split('\n'))

        for app in apps_:
            if re.search(keyword, app, flags=re.IGNORECASE) is not None:
                keyword = app

        app_status = os.system(f"open /Applications/'{keyword}'")
        if app_status == 256:
            speaker.say(f"I did not find the app {keyword}.")
            apps(None)
        else:
            speaker.say(f"I have opened {keyword}")
            renew()
    elif operating_system == 'Darwin':
        v = (subprocess.check_output("ls /Applications/", shell=True))
        apps_ = (v.decode('utf-8').split('\n'))

        for app in apps_:
            if re.search(keyword, app, flags=re.IGNORECASE) is not None:
                keyword = app

        app_status = os.system(f"open /Applications/'{keyword}'")
        if app_status == 256:
            speaker.say(f"I did not find the app {keyword}.")
            apps(None)
        else:
            keyword = keyword.replace('.app', '')
            speaker.say(f"I have opened {keyword}")
        renew()


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
    sys.stdout.write('\r')
    renew()


def repeater():
    """Repeats what ever you say"""
    global place_holder
    speaker.say("Please tell me what to repeat.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            sys.stdout.write("\r") and playsound('end.mp3')
            keyword = recognizer.recognize_google(listener)
            sys.stdout.write(keyword)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            repeater()
        place_holder = None
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            renew()
        speaker.say(f"I heard {keyword}")
        speaker.runAndWait()
    renew()


def chatBot():
    """Initiates chat bot, currently not supported for Windows"""
    global place_holder
    if operating_system == 'Windows':
        speaker.say('Seems like you are running a Windows operating system. Requirements have version conflicting '
                    'installations. So, currently chat bot is available only for mac OS.')
        renew()

    file1, file2 = 'db.sqlite3', f"/Users/{os.environ.get('USER')}/nltk_data"
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
        speaker.say('The chatbot is ready. You may start a conversation now.')
        speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            keyword = recognizer.recognize_google(listener)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            chatBot()

        place_holder = None
        if any(re.search(line, keyword, flags=re.IGNORECASE) for line in keywords.exit()):
            speaker.say('Let me remove the training modules.')
            os.system('rm db*')
            os.system(f'rm -rf {file2}')
            speaker.runAndWait()
            renew()
        else:
            response = bot.get_response(keyword)
            if response == 'What is AI?':
                speaker.say(f'The chat bot is unable to get a response for the phrase, {keyword}. Try something else.')
                speaker.runAndWait()
            else:
                speaker.say(f'{response}')
                speaker.runAndWait()
            chatBot()


def location():
    """Gets your current location"""
    city, state, country = location_info['city'], location_info['state'], location_info['country']
    speaker.say(f"You're at {city} {state}, in {country}")
    speaker.runAndWait()
    renew()


def locate():
    """Locates your iPhone using icloud api for python"""
    global place_holder
    if dummy.has_been_called:
        speaker.say("Would you like to ring it?")
    else:
        stat = icloud_api.iphone.status()
        bat_percent = round(stat['batteryLevel'] * 100)
        device_model = stat['deviceDisplayName']
        phone_name = stat['name']
        speaker.say(f"Your iPhone is at {location_info['city']}, {location_info['state']}.")
        speaker.say(f"Some more details. Battery: {bat_percent}%, Name: {phone_name}, Model: {device_model}")
        speaker.say("Would you like to ring it?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            phrase = recognizer.recognize_google(listener)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            place_holder = 0
            locate()

        place_holder = None
        if any(re.search(line, phrase, flags=re.IGNORECASE) for line in keywords.ok()):
            speaker.say("Ringing your iPhone now.")
            speaker.runAndWait()
            icloud_api.iphone.play_sound()
            speaker.say("I can also enable lost mode. Would you like to do it?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            phrase = recognizer.recognize_google(listener)
            if any(re.search(line, phrase, flags=re.IGNORECASE) for line in keywords.ok()):
                recovery = os.getenv('icloud_recovery') or aws.icloud_recovery()
                message = 'Return my phone immediately.'
                icloud_api.iphone.lost_device(recovery, message)
                speaker.say("I've enabled lost mode on your phone.")
                speaker.runAndWait()
            else:
                renew()
        else:
            renew()


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
        sys.stdout.write('\r')
        speaker.say("Enjoy your music sir!")
        speaker.runAndWait()
        sentry_mode()


def gmail():
    """Reads unread emails from your gmail account and skips going to renew() if the function is called by report()"""
    global place_holder
    sys.stdout.write("\rFetching new emails..")
    import email
    import imaplib
    from email.header import decode_header, make_header

    u = os.getenv('gmail_user') or aws.gmail_user()
    p = os.getenv('gmail_pass') or aws.gmail_pass()

    mail = imaplib.IMAP4_SSL('imap.gmail.com')  # connects to imaplib
    mail.login(u, p)
    mail.list()
    mail.select('inbox')  # choose inbox

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')  # looks for unread emails
    if return_code == 'OK':
        for num in messages[0].split():
            n = n + 1
    else:
        speaker.say("I'm unable access your email sir.")
        renew()
    if n == 0:
        speaker.say("You don't have any unread email sir")
        speaker.runAndWait()
    else:
        speaker.say(f'You have {n} unread emails sir. Do you want me to check it?')  # user check before reading subject
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                response = recognizer.recognize_google(listener)
                sys.stdout.write("\r") and playsound('end.mp3')
                if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.ok()):
                    for nm in messages[0].split():
                        ignore, mail_data = mail.fetch(nm, '(RFC822)')
                        for response_part in mail_data:
                            if isinstance(response_part, tuple):  # checks for type(response_part)
                                original_email = email.message_from_bytes(response_part[1])
                                raw_receive = (original_email['Received'].split(';')[-1]).strip()
                                try:
                                    datetime_obj = datetime.strptime(raw_receive, "%a, %d %b %Y %H:%M:%S -0700 (PDT)") \
                                                   + timedelta(hours=2)
                                except ValueError:
                                    datetime_obj = datetime.strptime(raw_receive, "%a, %d %b %Y %H:%M:%S -0800 (PST)") \
                                                   + timedelta(hours=2)
                                received_date = datetime_obj.strftime("%Y-%m-%d")
                                current_date = datetime.today().date()
                                yesterday = current_date - timedelta(days=1)
                                # replaces current date with today or yesterday
                                if received_date == str(current_date):
                                    receive = datetime_obj.strftime("today, at %I:%M %p")
                                elif received_date == str(yesterday):
                                    receive = datetime_obj.strftime("yesterday, at %I:%M %p")
                                else:
                                    receive = datetime_obj.strftime("on %A, %B %d, at %I:%M %p")
                                sender = (original_email['From']).split(' <')[0]
                                sub = make_header(decode_header(original_email['Subject']))
                                speaker.say(f"You have an email from, {sender}, with subject, {sub}, {receive}")
                                speaker.runAndWait()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                speaker.runAndWait()
                place_holder = 0
                gmail()

            place_holder = None
    if report.has_been_called:
        pass
    else:
        renew()


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
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                response = recognizer.recognize_google(listener)
                sys.stdout.write("\r") and playsound('end.mp3')
                if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.exit()):
                    renew()
                definition = dictionary.meaning(response)
                if definition:
                    n = 0
                    vowel = ['A', 'E', 'I', 'O', 'U']
                    for key, value in definition.items():
                        insert = 'an' if key[0] in vowel else 'a'
                        repeat = 'also' if n != 0 else ''
                        n += 1
                        mean = ', '.join(value[0:2])
                        speaker.say(f'{keyword} is {repeat} {insert} {key}, which means {mean}.')
                else:
                    speaker.say("Keyword should be a single word. Try again")
                    meaning(None)
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                speaker.runAndWait()
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
    renew()


def create_db():
    """Creates a database for to-do list by calling the create_db() function in helper_functions/database.py"""
    speaker.say(database.create_db())
    if todo.has_been_called:
        todo.has_been_called = False
        todo()
    elif add_todo.has_been_called:
        add_todo.has_been_called = False
        add_todo()
    renew()


def todo():
    """Says your to-do list and skips going to renew() if the function is called by report()"""
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    # if this function has been called by report() says database status and passes else it will ask for db creation
    if not os.path.isfile(file_name) and report.has_been_called:
        speaker.say("You don't have a database created for your to-do list sir.")
    elif not os.path.isfile(file_name):
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                sys.stdout.write("\r") and playsound('end.mp3')
                key = recognizer.recognize_google(listener)
                if any(re.search(line, key, flags=re.IGNORECASE) for line in keywords.ok()):
                    todo.has_been_called = True
                    sys.stdout.write("\r")
                    create_db()
                else:
                    renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
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
            for category, item in result.items():  # browses dictionary and stores result in response and says it
                response = f"Your to-do items are, {item}, in {category} category."
                speaker.say(response)
                sys.stdout.write(f"\r{response}")
        else:
            speaker.say("You don't have any tasks in your to-do list sir.")

    if report.has_been_called:
        speaker.runAndWait()
    else:
        renew()


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
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                key = recognizer.recognize_google(listener)
                if any(re.search(line, key, flags=re.IGNORECASE) for line in keywords.ok()):
                    add_todo.has_been_called = True
                    sys.stdout.write("\r")
                    create_db()
                else:
                    renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                add_todo()
            place_holder = None
    place_holder = None
    speaker.say("What's your plan sir?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            item = recognizer.recognize_google(listener)
            if 'exit' in item or 'quit' in item or 'Xzibit' in item:
                speaker.say('Your to-do list has been left intact sir.')
                renew()
            sys.stdout.write(f"Item: {item}")
            speaker.say(f"I heard {item}. Which category you want me to add it to?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener_ = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r") and playsound('end.mp3')
            category = recognizer.recognize_google(listener_)
            if 'exit' in category or 'quit' in category or 'Xzibit' in category:
                speaker.say('Your to-do list has been left intact sir.')
                renew()
            sys.stdout.write(f"Category: {category}")
            # passes the category and item to uploader() in helper_functions/database.py which updates the database
            response = database.uploader(category, item)
            speaker.say(response)
            speaker.say("Do you want to add anything else to your to-do list?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener_continue = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r") and playsound('end.mp3')
            category_continue = recognizer.recognize_google(listener_continue)
            if any(re.search(line, category_continue, flags=re.IGNORECASE) for line in keywords.exit()):
                renew()
            else:
                add_todo()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that.")
            renew()
        place_holder = None
    renew()


def delete_todo():
    """Deletes items from an existing to-do list"""
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name):
        speaker.say("You don't have a database created for your to-do list sir.")
        renew()
    speaker.say("Which one should I remove sir?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        dummy.has_been_called = True
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r") and playsound('end.mp3')
            item = recognizer.recognize_google(listener)
            if any(re.search(line, item, flags=re.IGNORECASE) for line in keywords.exit()):
                renew()
            response = database.deleter(item)
            # if the return message from database starts with 'Looks' it means that the item wasn't matched for deletion
            if response.startswith('Looks'):
                sys.stdout.write(f'\r{response}')
                speaker.say(response)
                speaker.runAndWait()
                delete_todo()
            else:
                speaker.say(response)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            delete_todo()
        place_holder = None
    renew()


def delete_db():
    """Deletes your database file after getting confirmation"""
    global place_holder
    if os.path.isfile(file_name):
        speaker.say(f'{random.choice(confirmation)} delete your database?')
        speaker.runAndWait()
    else:
        speaker.say(f'I did not find any database sir.')
        renew()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r") and playsound('end.mp3')
            response = recognizer.recognize_google(listener)
            if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.ok()):
                os.remove(file_name)
                speaker.say("I've removed your database sir.")
            else:
                speaker.say("Your database has been left intact sir.")
            renew()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
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
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                destination = recognizer.recognize_google(listener)
                if len(destination.split()) > 2:
                    speaker.say("I asked for a destination sir, not a sentence. Try again.")
                    distance(starting_point=None, destination=None)
                if 'exit' in destination or 'quit' in destination or 'Xzibit' in destination:
                    renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
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
    renew()


def locate_places(place):
    """Gets location details of a place"""
    global place_holder
    if not place:
        speaker.say("Tell me the name of a place!")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
                for word in converted.split():
                    if word[0].isupper():
                        place += word + ' '
                    elif '.' in word:
                        place += word + ' '
                if not place:
                    keyword = 'is'
                    before_keyword, keyword, after_keyword = converted.partition(keyword)
                    place = after_keyword.replace(' in', '').strip()
                if 'exit' in place or 'quit' in place or 'Xzibit' in place:
                    place_holder = None
                    renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, TypeError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
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
    except:
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
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
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
                    renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
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
    if re.match(start_country, end_country, flags=re.IGNORECASE):
        directions.has_been_called = True
        distance(starting_point=None, destination=place)
    else:
        speaker.say("You might need a flight to get there!")
    renew()


def alarm(hour, minute, am_pm):
    """Passes hour, minute and am/pm to Alarm class which initiates a thread for alarm clock in the background"""
    global place_holder
    if hour and minute and am_pm:
        f_name = f"{hour}_{minute}_{am_pm}"
        open(f'alarm/{f_name}.lock', 'a')
        Alarm(hour, minute, am_pm).start()
    else:
        speaker.say('Please tell me a time sir!')
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
                if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                    place_holder = None
                    renew()
                else:
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
                    alarm(hour=hour, minute=minute, am_pm=am_pm)
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, ValueError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                alarm(hour=None, minute=None, am_pm=None)
            place_holder = None
    speaker.say(f"Sure sir! Alarm has been set for {hour}:{minute} {am_pm}.")
    sys.stdout.write(f"Alarm has been set for {hour}:{minute} {am_pm} sir!")
    renew()


def kill_alarm():
    """Removes lock file to stop the alarm which rings only when the certain lock file is present
    alarm_state is the list of lock files currently present"""
    global place_holder
    alarm_state = []
    [alarm_state.append(file) if file != 'dummy.lock' else None for file in os.listdir('alarm')]
    alarm_state.remove('.DS_Store') if '.DS_Store' in alarm_state else None
    if not alarm_state:
        speaker.say("You have no alarms set sir!")
    elif len(alarm_state) == 1:
        hour, minute, am_pm = alarm_state[0][0:2], alarm_state[0][3:5], alarm_state[0][6:8]
        try:
            os.remove(f"alarm/{alarm_state[0]}")
        except FileNotFoundError:
            pass
        speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
    else:
        sys.stdout.write(f"{', '.join(alarm_state).replace('.lock', '')}")
        speaker.say("Please let me know which alarm you want to remove. Current alarms on your screen sir!")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
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
                try:
                    os.remove(f"alarm/{hour}_{minute}_{am_pm}.lock")
                except FileNotFoundError:
                    speaker.say(f"I wasn't able to find an alarm at {hour}:{minute} {am_pm}. Try again.")
                    kill_alarm()
                speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                kill_alarm()
            except FileNotFoundError as file_error:
                sys.stdout.write(f"{file_error}")
                speaker.say(f"Unable to find a lock file for {hour} {minute} {am_pm} sir! Try again!")
                kill_alarm()
    renew()


def google_home(device, file):
    """Uses socket lib to extract ip address and scans ip range for google home devices and play songs in your local.
    Can also play music on multiple devices at once.
    Changes made to google-home-push module:
        * Modified the way local IP is received: https://github.com/deblockt/google-home-push/pull/7
        * Instead of commenting/removing the final print statement on: site-packages/googlehomepush/__init__.py
        I have used "sys.stdout = open(os.devnull, 'w')" to suppress any print statements. To enable this again at a
        later time use "sys.stdout = sys.__stdout__"
    Note: When music is played and immediately stopped/tasked the google home device, it is most likely to except
    Broken Pipe error which usually happens when you write to a socket fully closed on the other Broken Pipe occurs
    when one end of the connection tries sending data while the other end has already closed the connection.
    This can simply be ignored or handled using the below in socket module (NOT PREFERRED).
    ''' except IOError as error:
            import errno
            if error.errno != errno.EPIPE:
                sys.stdout.write(e)
                pass'''
    """
    from socket import socket, AF_INET, SOCK_DGRAM
    from googlehomepush import GoogleHome
    from pychromecast.error import ChromecastConnectionError
    your_ip = ''
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    your_ip += s.getsockname()[0]
    s.close()
    look_up = ('.'.join(your_ip.split('.')[0:3]))
    ip_range = [3, 7, 15]
    devices = {}
    for n in ip_range:
        try:
            device_info = GoogleHome(host=f"{look_up}.{n}").cc
            device_info = str(device_info)
            device_name = device_info.split("'")[3]
            ip = device_info.split("'")[1]
            # port = sample.split("'")[2].split()[1].replace(',', '')
            devices.update({device_name: ip})
        except ChromecastConnectionError:
            pass
    if not device or not file:
        sys.stdout.write('\r')
        for device, ip in devices.items():
            sys.stdout.write(f"{device},  ")
        speaker.say(f"You have {len(devices)} devices in your IP range. Devices list on your screen sir! You can "
                    f"choose one and ask me to play some music on any of these.")
        renew()
    else:
        from googlehomepush.http_server import serve_file
        chosen = []
        [chosen.append(value) if key.lower() in device.lower() else None for key, value in devices.items()]
        if not chosen:
            speaker.say("I don't see any matching devices sir!. Let me help you.")
            google_home(None, None)
        for target in chosen:
            file_url = serve_file(file, "audio/mp3")  # serves the file on local host and generates the play url
            sys.stdout.write('\r')
            sys.stdout = open(os.devnull, 'w')  # suppresses print statement from "googlehomepush/__init.py__"
            GoogleHome(host=target).play(file_url, "audio/mp3")
            sys.stdout = sys.__stdout__  # removes print statement's suppression above
        speaker.say("Enjoy your music sir!") if len(chosen) == 1 else \
            speaker.say(f"That's interesting, you've asked me to play on {len(chosen)} devices at a time. "
                        f"I hope you'll enjoy this sir.")
        speaker.runAndWait()
        sentry_mode()


def jokes():
    """Uses jokes lib to say chucknorris jokes"""
    global place_holder
    from joke.jokes import geek, icanhazdad, chucknorris, icndb
    speaker.say(random.choice([geek, icanhazdad, chucknorris, icndb])())
    speaker.runAndWait()
    speaker.say("Do you want to hear another one sir?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            converted = recognizer.recognize_google(listener)
            place_holder = None
            if any(word in converted.lower() for word in keywords.ok()):
                jokes()
            else:
                renew()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            renew()


def reminder(hour, minute, am_pm, message):
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder"""
    global place_holder
    if hour and minute and am_pm and message:
        f_name = f"{hour}_{minute}_{am_pm}"
        open(f'reminder/{f_name}.lock', 'a')
        Reminder(hour, minute, am_pm, message).start()
    else:
        speaker.say('Please give me the reminder details sir!')
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
                if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                    place_holder = None
                    renew()
                else:
                    message = re.search('to(.*)at', converted).group(1).strip()
                    """uses regex to find numbers in your statement and processes AM and PM information"""
                    extracted_time = re.findall(r'\s([0-9]+\:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
                        r'\s([0-9]+\s?(?:a.m.|p.m.:?))', converted)
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
                    reminder(hour, minute, am_pm, message)
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, ValueError, IndexError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                reminder(hour=None, minute=None, am_pm=None, message=None)
            place_holder = None
    speaker.say(f"Sure sir! I will remind you to {message} at {hour}:{minute} {am_pm}.")
    sys.stdout.write(f"I will remind you to {message} at {hour}:{minute} {am_pm} sir!")
    renew()


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
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
                if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                    renew()
                if any(word in converted.lower() for word in keywords.ok()):
                    place_holder = None
                    maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
                    webbrowser.open(maps_url)
                    speaker.say("Directions on your screen sir!")
                    renew()
                elif results == 1:
                    renew()
                elif n == results:
                    speaker.say("I've run out of options sir!")
                    renew()
                else:
                    continue
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, ValueError, IndexError):
                maps_api.has_been_called = True
                return True


def notes():
    """Listens to the user and saves everything to a notes.txt file"""
    global place_holder
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rNotes::Listener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            sys.stdout.write("\r") and playsound('end.mp3')
            converted = recognizer.recognize_google(listener)
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                renew()
            else:
                with open(r'notes.txt', 'a') as writer:
                    writer.write(f"{datetime.now().strftime('%A, %B %d, %Y')}\n{datetime.now().strftime('%I:%M %p')}\n"
                                 f"{converted}\n")
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
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
        renew()
    elif len(target) <= 3:
        newest = []
        [newest.append(new.split('/')[-1]) for new in target]
        sys.stdout.write(f"\r{', '.join(newest)}")
        speaker.say(f"I found {len(target)} results. On your screen sir! Which one shall I clone?")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                converted = recognizer.recognize_google(listener)
                if any(word in converted.lower() for word in keywords.exit()):
                    place_holder = None
                    renew()
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
                renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                github(target)
    else:
        speaker.say(f"I found {len(target)} repositories sir! You may want to be more specific.")
        renew()


def send_sms(target):
    """Sends a message to the number received. If no number was received, it will ask for a number, looks if it is
    10 digits and then sends a message."""
    global place_holder
    import smtplib
    if not target:
        speaker.say("Please tell me a number sir!")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                number = recognizer.recognize_google(listener)
                sys.stdout.write(f'\rNumber: {number}')
                place_holder = None
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                send_sms(target=None)
    else:
        number = target
    if len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) != 10:
        sys.stdout.write(f'\r{number}')
        speaker.say("I don't think that's a right number sir! Phone numbers are 10 digits. Try again!")
        send_sms(target=None)
    speaker.say("What would you like to send sir?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            body = recognizer.recognize_google(listener)
            place_holder = None
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            send_sms(target=number)
    sys.stdout.write(f'\r{body}::to::{number}')
    speaker.say(f'{body} to {number}. Do you want me to proceed?')
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            converted = recognizer.recognize_google(listener)
            if not any(word in converted.lower() for word in keywords.ok()):
                speaker.say("Message will not be sent sir!")
                renew()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            send_sms(target=number)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    gmail_user = os.getenv('gmail_user') or aws.gmail_user()
    gmail_pass = os.getenv('gmail_pass') or aws.gmail_pass()
    server.login(user=gmail_user, password=gmail_pass)
    to = f"+1{number}@tmomail.net"
    subject = "Jarvis::Message from Vignesh"
    sender = (f"From: {gmail_user}\r\n" + f"To: {to}\r\n" + f"Subject: {subject}\r\n" + "\r\r\n\n" + body)
    server.sendmail(gmail_user, to, sender)
    server.close()
    speaker.say("Message has been sent sir!")
    renew()


def google(query):
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
            splitted = ' '.join(splitter(modify.replace('.', 'rEpLaCInG')))
            sentence = splitted.replace(' rEpLaCInG ', '.')
            repeats = []
            [repeats.append(word) for word in sentence.split() if word not in repeats]
            refined = ' '.join(repeats)
            output = refined + required[1] + '.' + required[2]
        # TODO: modify all regex searches in a single line
        match = re.search(r'\w{3} \d{1}, \d{4}', output) or re.search(r'\w{3} \d{2}, \d{4}', output) or \
                re.search(r'\w{3}, \d{1}, \d{4}', output) or re.search(r'\w{3}, \d{2}, \d{4}', output) or \
                re.search(r'\w{3} \d{1} \d{4}', output) or re.search(r'\w{3} \d{2} \d{4}', output)
        if match:
            output = output.replace(match.group(), '')
        sys.stdout.write(f'\r{output}')
        speaker.say(output)
        renew()
    else:
        return True


def google_search(phrase):
    global place_holder
    if not phrase:
        speaker.say("Please tell me the search phrase.")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r") and playsound('end.mp3')
                phrase = recognizer.recognize_google(listener)
                converted = phrase.lower()
                if 'exit' in converted or 'quit' in converted or 'xzibit' in converted or 'cancel' in converted:
                    renew()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                if place_holder == 0:
                    place_holder = None
                    renew()
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                place_holder = 0
                google_search(None)
    search = str(phrase).replace(' ', '+')
    unknown_url = f"https://www.google.com/search?q={search}"
    webbrowser.open(unknown_url)
    speaker.say(f"I've opened up a google search for: {phrase}.")
    renew()


def sentry_mode():
    """Sentry mode, all it does is to wait for the right keyword to wake up and get into action"""
    global waiter
    waiter = 0
    if greet_check == 'initialized':
        dummy.has_been_called = True
    try:
        sys.stdout.write("\rSentry Mode")
        listener = recognizer.listen(source_for_sentry_mode, timeout=None, phrase_time_limit=3)
        sys.stdout.write("\r")
        key = recognizer.recognize_google(listener)
        if 'look alive' in key in key or 'wake up' in key or 'wakeup' in key or 'show time' in key or 'Showtime' in \
                key or 'time to work' in key or 'spin up' in key:
            speaker.say(f'{random.choice(wake_up1)}')
            initialize()
        elif 'you there' in key or 'buddy' in key or 'are you there' in key:
            speaker.say(f'{random.choice(wake_up2)}')
            initialize()
        elif 'Jarvis' in key or 'jarvis' in key:
            speaker.say(f'{random.choice(wake_up3)}')
            initialize()
        else:
            sentry_mode()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, RecursionError):
        sentry_mode()
    except KeyboardInterrupt:
        memory_consumed = size_converter()
        speaker.say(f"Shutting down sir!")
        speaker.say(exit_msg)
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {memory_consumed}\nTotal runtime: {time_converter(time.perf_counter())}")
        Alarm(None, None, None)
        Reminder(None, None, None, None)
        exit(0)


def size_converter():
    """Gets the current memory consumed and converts it to human friendly format"""
    if operating_system == 'Darwin':
        import resource
        byte_size = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    elif operating_system == 'Windows':
        byte_size = Process(os.getpid()).memory_info().peak_wset
    else:
        byte_size = None
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    integer = int(math.floor(math.log(byte_size, 1024)))
    power = math.pow(1024, integer)
    size = round(byte_size / power, 2)
    response = str(size) + ' ' + size_name[integer]
    return response


def shutdown():
    """Gets confirmation and turns off the machine"""
    global place_holder
    speaker.say(f"{random.choice(confirmation)} turn off the machine?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            converted = recognizer.recognize_google(listener)
            place_holder = None
            if any(word in converted.lower() for word in keywords.ok()):
                memory_consumed = size_converter()
                speaker.say(f"Shutting down sir!")
                speaker.say(exit_msg)
                speaker.runAndWait()
                sys.stdout.write(
                    f"\rMemory consumed: {memory_consumed}\nTotal runtime: {time_converter(time.perf_counter())}")
                [os.remove(f"alarm/{file}") if file != 'dummy.lock' else None for file in os.listdir('alarm')]
                [os.remove(f"reminder/{file}") if file != 'dummy.lock' else None for file in os.listdir('reminder')]
                if operating_system == 'Darwin':
                    subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
                elif operating_system == 'Windows':
                    os.system("shutdown /s /t 1")
            else:
                speaker.say("Machine state is left intact sir!")
                renew()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
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
    aws = AWSClients()
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(limit * 10)

    # place_holder is used in all the functions so that the "I didn't quite get that..." part runs only once
    # greet_check is used in initialize() to greet only for the first run
    # waiter is used in renew() so that when waiter hits 12 count, active listener automatically goes to sentry mode
    place_holder, greet_check = None, None
    waiter = 0
    suggestion_count = 0

    # initiates geo_locator and stores current location info as json so it could be used in couple of other functions
    options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())
    geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)
    icloud_user = os.getenv('icloud_user') or aws.icloud_user()
    icloud_pass = os.getenv('icloud_pass') or aws.icloud_pass()
    icloud_api = PyiCloudService(icloud_user, icloud_pass)
    raw_location = icloud_api.iphone.location()
    current_lat = raw_location['latitude']
    current_lon = raw_location['longitude']
    locator = geo_locator.reverse(f'{current_lat}, {current_lon}')
    location_info = locator.raw['address']

    # different responses for different conditions in senty mode
    wake_up1 = ['Up and running sir.', 'Online and ready sir.', "I've indeed been uploaded sir!", 'Listeners have been '
                                                                                                  'activated sir!']
    wake_up2 = ['For you sir!, Always!', 'At your service sir.']
    wake_up3 = ["I'm here sir!."]

    confirmation = ['Requesting confirmation sir! Did you mean', 'Sir, are you sure you want to']

    model_file = os.listdir()
    if 'model.pcl' not in model_file:
        sys.stdout.write("\rPLEASE WAIT::Downloading model file for punctuations")
        os.system("""curl https://thevickypedia.com/punctuator/model.pcl --output model.pcl --silent""")

    sys.stdout.write("\rPLEASE WAIT::Training model for punctuations")
    punctuation = Punctuator(model_file='model.pcl')
    database = Database()
    current = datetime.now().strftime("%p")  # current part of day (AM/PM)
    clock = datetime.now().strftime("%I")  # current hour
    today = datetime.now().strftime("%A")  # current day

    # {function_name}.has_been_called is use to denote which function has triggered the other
    report.has_been_called, locate_places.has_been_called, directions.has_been_called, maps_api.has_been_called \
        = False, False, False, False
    for functions in [dummy, delete_todo, todo, add_todo]:
        functions.has_been_called = False

    # noinspection PyTypeChecker
    volume = int(speaker.getProperty("volume")) * 100
    sys.stdout.write(f'\rCurrent volume is: {volume}% Voice ID::Female: 1/17 Male: 0/7')

    voices = speaker.getProperty("voices")  # gets the list of voices available

    if operating_system == 'Darwin':
        # noinspection PyTypeChecker,PyUnresolvedReferences
        speaker.setProperty("voice", voices[7].id)  # voice module #7 for MacOS
    elif operating_system == 'Windows':
        # noinspection PyTypeChecker,PyUnresolvedReferences
        speaker.setProperty("voice", voices[0].id)  # voice module #0 for Windows
        speaker.setProperty('rate', 190)  # speech rate is slowed down in Windows for optimal experience
    else:
        operating_system = None
        exit(0)

    # variety of exit messages based on day of week and time of day
    weekend = ['Friday', 'Saturday']
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

    # starts sentry mode
    playsound('initialize.mp3')
    with sr.Microphone() as source_for_sentry_mode:
        recognizer.adjust_for_ambient_noise(source_for_sentry_mode)
        sentry_mode()
