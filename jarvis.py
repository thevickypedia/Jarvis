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
from urllib.request import urlopen

import certifi
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
from punctuator import Punctuator
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudAPIResponseException, PyiCloudFailedLoginException
from requests.auth import HTTPBasicAuth
from speedtest import Speedtest, ConfigRetrievalError
from wordninja import split as splitter

from alarm import Alarm
from helper_functions.aws_clients import AWSClients
from helper_functions.conversation import Conversation
from helper_functions.database import Database, file_name
from helper_functions.keywords import Keywords
from reminder import Reminder
from tv_controls import TV

# suppress all logging
logging.disable()


def initialize():
    """Function to initialize when woke up from sleep mode. greet_check and dummy are to ensure greeting is given only
    for the first time, the script is run place_holder is set for all the functions so that the function runs only ONCE
    again in case of an exception"""
    global place_holder, greet_check
    greet_check = 'initialized'
    if dummy.has_been_called:
        speaker.say("What can I do for you?")
        dummy.has_been_called = False
    elif str(datetime.now().strftime("%p")) == 'AM' and int(datetime.now().strftime("%I")) < 10:
        speaker.say("Good Morning.")
    elif str(datetime.now().strftime("%p")) == 'AM' and int(datetime.now().strftime("%I")) >= 10:
        speaker.say("Hope you're having a nice morning.")
    elif str(datetime.now().strftime("%p")) == 'PM' and (int(datetime.now().strftime("%I")) == 12 or
                                                         int(datetime.now().strftime("%I")) < 3):
        speaker.say("Good Afternoon.")
    elif str(datetime.now().strftime("%p")) == 'PM' and int(datetime.now().strftime("%I")) < 6:
        speaker.say("Good Evening.")
    else:
        speaker.say("Hope you're having a nice night.")
    speaker.runAndWait()
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
    try:
        sys.stdout.write("\rListener activated..") and playsound('start.mp3') if waiter == 0 else \
            sys.stdout.write("\rListener activated..")
        listener = recognizer.listen(source, timeout=None, phrase_time_limit=5)
        sys.stdout.write("\r") and playsound('end.mp3') if waiter == 0 else sys.stdout.write("\r")
        converted = recognizer.recognize_google(listener)
        if 'are you there' in converted.lower() or converted.strip() == 'Jarvis' or 'you there' in \
                converted.lower():
            speaker.say("I'm here sir!")
            renew()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
        if waiter == 12:  # waits for a minute and goes to sleep
            sentry_mode()
        waiter += 1
        converted = None
    if not converted:
        alive()
    elif any(word in converted.lower() for word in keywords.sleep()):
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
    if any(word in converted.lower() for word in keywords.date()) and \
            not any(word in converted.lower() for word in keywords.avoid()):
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
        checker = converted.lower()
        if 'tomorrow' in checker or 'day after' in checker or 'next week' in checker or 'tonight' in checker or \
                'afternoon' in checker or 'evening' in checker:
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
        locate()

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
        renew()

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
            level = re.findall(r'\b\d+\b', converted)
            level = int(level[0]) if level else 50
        volume_controller(level)

    elif any(word in converted.lower() for word in keywords.face_detection()):
        face_recognition_detection()

    elif any(word in converted.lower() for word in keywords.speed_test()):
        speed_test()

    elif any(word in converted.lower() for word in keywords.bluetooth()):
        if operating_system == 'Darwin':
            bluetooth(phrase=converted.lower())
        elif operating_system == 'Windows':
            speaker.say("Bluetooth connectivity on Windows hasn't been developed sir!")
            renew()

    elif any(word in converted.lower() for word in conversation.greeting()):
        speaker.say('I am spectacular. I hope you are doing fine too.')
        renew()

    elif any(word in converted.lower() for word in conversation.capabilities()):
        speaker.say('There is a lot I can do. For example: I can get you the weather at any location, news around '
                    'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                    'system configuration, tell your investment details, locate your phone, find distance between '
                    'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
                    ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')
        renew()

    elif any(word in converted.lower() for word in conversation.languages()):
        speaker.say("Tricky question!. I'm configured in python, and I can speak English.")
        renew()

    elif any(word in converted.lower() for word in conversation.whats_up()):
        speaker.say("My listeners are up. There is nothing I cannot process. So ask me anything..")
        renew()

    elif any(word in converted.lower() for word in conversation.what()):
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")
        renew()

    elif any(word in converted.lower() for word in conversation.who()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        renew()

    elif any(word in converted.lower() for word in conversation.about_me()):
        speaker.say("I am Jarvis. A virtual assistant designed by Mr.Raauv.")
        speaker.say("I'm just a pre-programmed virtual assistant, trying to become a natural language UI.")
        speaker.say("I can seamlessly take care of your daily tasks, and also help with most of your work!")
        renew()

    elif any(word in converted.lower() for word in keywords.exit()):
        speaker.say(f"Activating sentry mode, enjoy yourself sir.")
        speaker.runAndWait()
        sentry_mode()

    elif any(word in converted.lower() for word in keywords.restart()):
        restart()

    elif any(word in converted.lower() for word in keywords.kill()):
        speaker.say(f"Shutting down sir!")
        speaker.say(exit_message())
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                         f"\nTotal runtime: {time_converter(time.perf_counter())}")
        Alarm(None, None, None)
        Reminder(None, None, None, None)
        exit(0)

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
    if time_travel.has_been_called:
        dt_string = dt_string + date_
    else:
        dt_string = dt_string + date_ + ', ' + year
    speaker.say(f"It's {dt_string}")
    if report.has_been_called or time_travel.has_been_called:
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
        speaker.say(f'{c_time}.')
    if report.has_been_called or time_travel.has_been_called:
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
        renew()


def weather(place):
    """Says weather at any location and skips going to renew() if the function is called by report()
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
            output = f'The weather at {city} is a {feeling} {temp_f}°, but due to the current wind conditions ' \
                     f'(which is {wind_speed} miles per hour), it feels like {temp_feel_f}°. {weather_suggest}. '
        else:
            output = f'The weather at {city} is a {feeling} {temp_f}°, and it currently feels like {temp_feel_f}°. ' \
                     f'{weather_suggest}. '
    elif place or not report.has_been_called:
        output = f'The weather at {weather_location} is {temp_f}°F, with a high of {high}, and a low of {low}. ' \
                 f'It currently feels like {temp_feel_f}°F, and the current condition is {condition}.'
    else:
        output = f'You are currently at {weather_location}. The weather at your location is {temp_f}°F, with a high ' \
                 f'of {high}, and a low of {low}. It currently feels Like {temp_feel_f}°F, and the current ' \
                 f'condition is {condition}. Sunrise at {sunrise}. Sunset at {sunset}. '
    if 'alerts' in response:
        alerts = response['alerts'][0]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
    else:
        alerts, start_alert, end_alert = None, None, None
    if alerts and start_alert and end_alert:
        output += f'You have a weather alert for {alerts} between {start_alert} and {end_alert}'
    sys.stdout.write(f"\r{output}")
    speaker.say(output)
    speaker.runAndWait()
    if report.has_been_called or time_travel.has_been_called:
        pass
    else:
        renew()


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
    weather_location = f'{city} {state}'
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
        alerts = response['alerts'][key]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][key]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][key]['end']).strftime("%I:%M %p")
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
    renew()


def wikipedia_():
    """gets any information from wikipedia using it's API"""
    global place_holder
    import wikipedia
    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
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
        keyword = None
        wikipedia_()

    place_holder = None
    if any(re.search(line, keyword, flags=re.IGNORECASE) for line in keywords.exit()):
        renew()
    else:
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
            summary = None
            wikipedia_()
        # stops with two sentences before reading whole passage
        formatted = punctuation.punctuate(' '.join(splitter(' '.join(summary.split('.')[0:2]))))
        speaker.say(formatted)
        speaker.say("Do you want me to continue sir?")  # gets confirmation to read the whole passage
        speaker.runAndWait()
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener2 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            response = recognizer.recognize_google(listener2)
            place_holder = None
            if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.ok()):
                speaker.say(''.join(summary.split('.')[3:-1]))
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            sys.stdout.write("\r")
            speaker.say("I'm sorry sir, I didn't get your response.")
        renew()


def news():
    """Says news around you and skips going to renew() if the function is called by report()"""
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
    speaker.runAndWait()

    if report.has_been_called:
        pass
    elif time_travel.has_been_called:
        sentry_mode()
    else:
        renew()


def apps(keyword):
    """Launches an application skimmed from your statement and unable to skim asks for the app name"""
    global place_holder
    ignore = ['app', 'application']
    if (keyword in ignore or keyword is None) and operating_system == 'Windows':
        speaker.say("Please say the app name.")
        speaker.runAndWait()
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
    try:
        sys.stdout.write("\rListener activated..") and playsound('start.mp3')
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=10)
        sys.stdout.write("\r") and playsound('end.mp3')
        keyword = recognizer.recognize_google(listener)
        sys.stdout.write(keyword)
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            pass
        else:
            speaker.say(f"I heard {keyword}")
        renew()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
        if place_holder == 0:
            place_holder = None
            renew()
        else:
            sys.stdout.write("\r")
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
    try:
        sys.stdout.write("\rListener activated..") and playsound('start.mp3')
        listener = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        sys.stdout.write("\r") and playsound('end.mp3')
        keyword = recognizer.recognize_google(listener)
        place_holder = None
        if any(re.search(line, keyword, flags=re.IGNORECASE) for line in keywords.exit()):
            speaker.say('Let me remove the training modules.')
            os.system('rm db*')
            os.system(f'rm -rf {file2}')
            renew()
        else:
            response = bot.get_response(keyword)
            if response == 'What is AI?':
                speaker.say(f'The chat bot is unable to get a response for the phrase, {keyword}. Try something else.')
            else:
                speaker.say(f'{response}')
            speaker.runAndWait()
            chatter_bot()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
        if place_holder == 0:
            place_holder = None
            os.system('rm db*')
            os.system(f'rm -rf {file2}')
            renew()
        else:
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            chatter_bot()


def location():
    """Gets your current location"""
    city, state, country = location_info['city'], location_info['state'], location_info['country']
    speaker.say(f"You're at {city} {state}, in {country}")
    renew()


def locate():
    """Locates your iPhone using icloud api for python"""
    global place_holder
    if dummy.has_been_called:
        dummy.has_been_called = False
        speaker.say("Would you like to ring it?")
    else:
        stat = icloud_api.iphone.status()
        bat_percent = round(stat['batteryLevel'] * 100)
        device_model = stat['deviceDisplayName']
        phone_name = stat['name']
        post_code = '"'.join(list(location_info['postcode'].split('-')[0]))
        iphone_location = f"Your iphone is near {location_info['road']}, {location_info['city']} " \
                          f"{location_info['state']}. Zipcode: {post_code}, {location_info['country']}"
        speaker.say(iphone_location)
        speaker.say(f"Some more details. Battery: {bat_percent}%, Name: {phone_name}, Model: {device_model}")
        speaker.say("Would you like to ring it?")
    speaker.runAndWait()
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
        phrase = None
        locate()

    place_holder = None
    if any(re.search(line, phrase, flags=re.IGNORECASE) for line in keywords.ok()):
        speaker.say("Ringing your iPhone now.")
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

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(u, p)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError:
        mail = None
        speaker.say("I wasn't able to check your emails sir. I think you have your VPN turned ON. If so, disconnect "
                    "it.")
        speaker.runAndWait()
        sentry_mode()

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')  # looks for unread emails
    if return_code == 'OK':
        for _ in messages[0].split():
            n = n + 1
    else:
        speaker.say("I'm unable access your email sir.")
        renew()
    if n == 0:
        speaker.say("You don't have any emails to catch up sir")
        speaker.runAndWait()
    else:
        speaker.say(f'You have {n} unread emails sir. Do you want me to check it?')  # user check before reading subject
        speaker.runAndWait()
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
                            current_date = datetime.today().date()
                            yesterday = current_date - timedelta(days=1)
                            # replaces current date with today or yesterday
                            if received_date == str(current_date):
                                receive = datetime_obj.strftime("today, at %I:%M %p")
                            elif received_date == str(yesterday):
                                receive = datetime_obj.strftime("yesterday, at %I:%M %p")
                            else:
                                receive = datetime_obj.strftime("on %A, %B %d, at %I:%M %p")
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
    if report.has_been_called or time_travel.has_been_called:
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
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            response = recognizer.recognize_google(listener)
            sys.stdout.write("\r") and playsound('end.mp3')
            if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.exit()):
                renew()
            else:
                meaning(response)
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
            speaker.say(f'Do you wanna know how {keyword} is spelled?')
            speaker.runAndWait()
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                response = recognizer.recognize_google(listener)
                if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.ok()):
                    for letter in list(keyword.lower()):
                        speaker.say(letter)
                    speaker.runAndWait()
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                pass
        else:
            speaker.say("Keyword should be a single word. Try again")
            meaning(None)
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
    if not os.path.isfile(file_name) and time_travel.has_been_called:
        pass
    elif not os.path.isfile(file_name) and report.has_been_called:
        speaker.say("You don't have a database created for your to-do list sir.")
    elif not os.path.isfile(file_name):
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
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
    try:
        sys.stdout.write("\rListener activated..") and playsound('start.mp3')
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        sys.stdout.write("\r") and playsound('end.mp3')
        item = recognizer.recognize_google(listener)
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            speaker.say('Your to-do list has been left intact sir.')
            renew()
        sys.stdout.write(f"\rItem: {item}")
        speaker.say(f"I heard {item}. Which category you want me to add it to?")
        speaker.runAndWait()
        sys.stdout.write("\rListener activated..") and playsound('start.mp3')
        listener_ = recognizer.listen(source, timeout=3, phrase_time_limit=3)
        sys.stdout.write("\r") and playsound('end.mp3')
        category = recognizer.recognize_google(listener_)
        if 'exit' in category or 'quit' in category or 'Xzibit' in category:
            speaker.say('Your to-do list has been left intact sir.')
            renew()
        sys.stdout.write(f"\rCategory: {category}")
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
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            converted = recognizer.recognize_google(listener)
            if 'exit' in place or 'quit' in place or 'Xzibit' in place:
                place_holder = None
                renew()
            for word in converted.split():
                if word[0].isupper():
                    place += word + ' '
                elif '.' in word:
                    place += word + ' '
            if not place:
                keyword = 'is'
                before_keyword, keyword, after_keyword = converted.partition(keyword)
                place = after_keyword.replace(' in', '').strip()
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
            f_name = f"{hour}_{minute}_{am_pm}"
            open(f'alarm/{f_name}.lock', 'a')
            Alarm(hour, minute, am_pm).start()
            if 'wake' in msg.lower().strip():
                speaker.say(f"{random.choice(acknowledgement)} I will wake you up at {hour}:{minute} {am_pm}.")
            else:
                speaker.say(f"{random.choice(acknowledgement)} Alarm has been set for {hour}:{minute} {am_pm}.")
            sys.stdout.write(f"\rAlarm has been set for {hour}:{minute} {am_pm} sir!")
        else:
            speaker.say(f"An alarm at {hour} {minute} {am_pm}? Are you an alien? "
                        f"I don't think a time like that exists on Earth.")
    else:
        speaker.say('Please tell me a time sir!')
        speaker.runAndWait()
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            converted = recognizer.recognize_google(listener)
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                place_holder = None
                renew()
            else:
                alarm(converted)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            alarm(msg='')
        place_holder = None
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
        os.remove(f"alarm/{alarm_state[0]}")
        speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
    else:
        sys.stdout.write(f"\r{', '.join(alarm_state).replace('.lock', '')}")
        speaker.say("Please let me know which alarm you want to remove. Current alarms on your screen sir!")
        speaker.runAndWait()
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
            if f'{hour}_{minute}_{am_pm}.lock' in os.listdir('alarm'):
                os.remove(f"alarm/{hour}_{minute}_{am_pm}.lock")
                speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
            else:
                speaker.say(f"I wasn't able to find an alarm at {hour}:{minute} {am_pm}. Try again.")
                kill_alarm()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
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
    socket_ = socket(AF_INET, SOCK_DGRAM)
    socket_.connect(("8.8.8.8", 80))
    ip_address = socket_.getsockname()[0]
    socket_.close()
    look_up = ('.'.join(ip_address.split('.')[0:3]))
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


def reminder(converted):
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder"""
    global place_holder
    message = re.search('to(.*)at', converted)
    if not message:
        message = re.search('to(.*)', converted)
        if not message:
            speaker.say('Reminder format should be::Remind me to do something, at some time.')
            sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
            renew()
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
        r'([0-9]+\s?(?:a.m.|p.m.:?))', converted)
    if not extracted_time:
        speaker.say("When do you want to be reminded sir?")
        speaker.runAndWait()
        try:
            sys.stdout.write("\rListener activated..") and playsound('start.mp3')
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r") and playsound('end.mp3')
            converted = recognizer.recognize_google(listener)
            extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', converted) or re.findall(
                r'([0-9]+\s?(?:a.m.|p.m.:?))', converted)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            renew()
    if message and extracted_time:
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
            f_name = f"{hour}_{minute}_{am_pm}"
            open(f'reminder/{f_name}.lock', 'a')
            Reminder(hour, minute, am_pm, message).start()
            speaker.say(f"{random.choice(acknowledgement)} I will remind you to {message} at {hour}:{minute} {am_pm}.")
            sys.stdout.write(f"\rI will remind you to {message} at {hour}:{minute} {am_pm} sir!")
            renew()
        else:
            speaker.say(f"A reminder at {hour} {minute} {am_pm}? Are you an alien? "
                        f"I don't think a time like that exists on Earth.")
            renew()
    else:
        speaker.say('Reminder format should be::Remind me to do something, at some time.')
        sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
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
            number = None
            send_sms(target=None)
    else:
        number = target
    if len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) != 10:
        sys.stdout.write(f'\r{number}')
        speaker.say("I don't think that's a right number sir! Phone numbers are 10 digits. Try again!")
        send_sms(target=None)
    speaker.say("What would you like to send sir?")
    speaker.runAndWait()
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
        body = None
        send_sms(target=number)
    sys.stdout.write(f'\r{body}::to::{number}')
    speaker.say(f'{body} to {number}. Do you want me to proceed?')
    speaker.runAndWait()
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


def television(converted):
    """television() controls all actions on a TV. In the main() method tv is set to None if the
    TV class from tv_controls.py fails to connect to the tv, so the television function responds only
    if the request is to turn on the TV, else it exits with a bummer. Once the tv is turned on, the TV
    class is also initiated which is set global for other statements to use it."""
    global tv
    phrase = converted.replace('TV', '')
    if 'wake' in phrase or 'turn on' in phrase or 'connect' in phrase or 'status' in phrase:
        from wakeonlan import send_magic_packet as wake
        try:
            mac_address = os.getenv('tv_mac') or aws.tv_mac()
            wake(mac_address)
            tv = TV()
            speaker.say(f"TV features have been integrated sir!")
        except OSError:
            speaker.say("I wasn't able to turn on your TV sir! I think you have your VPN turned ON. If so, disconnect"
                        " it. And make sure you are on the same network as your TV.")
        renew()
    if tv:
        if 'increase' in phrase:
            tv.increase_volume()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'decrease' in phrase or 'reduce' in phrase:
            tv.decrease_volume()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'mute' in phrase:
            tv.mute()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'pause' in phrase or 'hold' in phrase:
            tv.pause()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'resume' in phrase or 'play' in phrase:
            tv.play()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'rewind' in phrase:
            tv.rewind()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'forward' in phrase:
            tv.forward()
            speaker.say(f'{random.choice(acknowledgement)}!')
        elif 'stop' in phrase:
            tv.stop()
            speaker.say(f'{random.choice(acknowledgement)}!')
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
            speaker.runAndWait()
            tv.shutdown()
            tv = None
        else:
            speaker.say("I didn't quite get that.")
    else:
        converted = converted.replace('my', 'your')
        speaker.say(f"I'm sorry sir! I wasn't able to {converted}, as the TV state is unknown! You can ask me to "
                    f"turn on or connect to the TV to start using the TV features.")
    renew()


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
            splitted = ' '.join(splitter(modify.replace('.', 'rEpLaCInG')))
            sentence = splitted.replace(' rEpLaCInG ', '.')
            repeats = []
            [repeats.append(word) for word in sentence.split() if word not in repeats]
            refined = ' '.join(repeats)
            output = refined + required[1] + '.' + required[2]
        match = re.search(r'(\w{3},|\w{3}) (\d,|\d|\d{2},|\d{2}) \d{4}', output)
        if match:
            output = output.replace(match.group(), '')
        sys.stdout.write(f'\r{output}')
        speaker.say(output)
        renew()
    else:
        return True


def google_search(phrase):
    """Opens up a google search for the phrase received. If nothing was received, gets phrase from user."""
    global place_holder
    if not phrase:
        speaker.say("Please tell me the search phrase.")
        speaker.runAndWait()

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
    speaker.say(f"{random.choice(acknowledgement)}")
    renew()


def face_recognition_detection():
    if operating_system == 'Darwin':
        from facial_recognition import Face
        sys.stdout.write("\r")
        train_dir = 'train'
        os.mkdir(train_dir) if train_dir not in current_dir else None
        speaker.say('Initializing facial recognition. Please smile at the camera for me.')
        speaker.runAndWait()
        sys.stdout.write('\rLooking for faces to recognize.')
        try:
            result = Face().face_recognition()
        except BlockingIOError:
            result = None
            speaker.say("I was unable to access the camera. Facial recognition can work only when cameras are "
                        "present and accessible.")
            renew()
        if not result:
            sys.stdout.write('\rLooking for faces to detect.')
            speaker.say("No faces were recognized. Switching on to face detection.")
            speaker.runAndWait()
            result = Face().face_detection()
            if not result:
                sys.stdout.write('\rNo faces were recognized nor detected.')
                speaker.say('No faces were recognized. nor detected. Please check if your camera is working, '
                            'and look at the camera when you retry.')
                renew()
            sys.stdout.write('\rNew face has been detected. Like to give it a name?')
            speaker.say('I was able to detect a face, but was unable to recognize it.')
            os.system('open cv2_open.jpg')
            speaker.say("I've taken a photo of you. Preview on your screen. Would you like to give it a name, "
                        "so that I can add it to my database of known list? If you're ready, please tell me a name, "
                        "or simply say exit.")
            speaker.runAndWait()
            try:
                sys.stdout.write("\rListener activated..") and playsound('start.mp3')
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
                phrase = recognizer.recognize_google(listener)
                if any(word in phrase.lower() for word in keywords.exit()):
                    os.remove('cv2_open.jpg')
                    speaker.say("I've deleted the image.")
                    renew()
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
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, RecursionError):
                os.remove('cv2_open.jpg')
                speaker.say("I did not get any response, so I've deleted the image.")
                renew()
        else:
            speaker.say(f'Hi {result}! How can I be of service to you?')
    elif operating_system == 'Windows':
        speaker.say("I am sorry, currently facial recognition and detection is only supported on MacOS, due to the "
                    "package installation issues on Windows. Is there anything else I can help you with?")
    renew()


def speed_test():
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
    renew()


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
    renew()


def time_travel():
    """Triggered only from sentry_mode() to give a quick update on your day. Starts the report() in personalized way"""
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

    speaker.say(f"Good {greet} Vignesh.")

    time_travel.has_been_called = True
    date()
    current_time(None)
    weather(None)
    todo()
    gmail()
    speaker.say('Would you like to hear the latest news?')
    speaker.runAndWait()
    try:
        sys.stdout.write("\rListener activated..") and playsound('start.mp3')
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        sys.stdout.write("\r")
        phrase = recognizer.recognize_google(listener)
        if any(word in phrase.lower() for word in keywords.ok()):
            news()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
        pass
    time_travel.has_been_called = False
    speaker.say(f"Activating sentry mode, enjoy yourself sir!")
    speaker.runAndWait()
    sentry_mode()


def sentry_mode():
    """Sentry mode, all it does is to wait for the right keyword to wake up and get into action"""
    global waiter, threshold
    threshold += 1
    if threshold > 5000:
        speaker.say("My run time has reached the threshold!")
        restart()

    waiter = 0
    if greet_check == 'initialized':
        dummy.has_been_called = True
    try:
        sys.stdout.write("\rSentry Mode")
        listener = recognizer.listen(source, timeout=None, phrase_time_limit=5)
        sys.stdout.write("\r")
        key = recognizer.recognize_google(listener)
        key = key.lower().strip()
        if key == 'jarvis' or key == 'buddy':
            speaker.say(f'{random.choice(wake_up3)}')
            initialize()
        elif 'good' in key:
            if 'good morning jarvis' in key or 'good afternoon jarvis' in key or 'good evening jarvis' in key or \
                    'good night jarvis' in key or 'goodnight jarvis' in key:
                time_travel()
        elif 'look alive' in key in key or 'wake up' in key or 'wakeup' in key or 'show time' in key or 'showtime' in \
                key or 'time to work' in key or 'spin up' in key:
            speaker.say(f'{random.choice(wake_up1)}')
            initialize()
        elif 'you there' in key or 'are you there' in key:
            speaker.say(f'{random.choice(wake_up2)}')
            initialize()
        elif 'jarvis' in key or 'buddy' in key:
            conditions(key)
        else:
            sentry_mode()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError, RecursionError):
        sentry_mode()
    except KeyboardInterrupt:
        speaker.say(f"Shutting down sir!")
        speaker.say(exit_message())
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                         f"\nTotal runtime: {time_converter(time.perf_counter())}")
        Alarm(None, None, None)
        Reminder(None, None, None, None)
        exit(0)


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
    """variety of exit messages based on day of week and time of day"""
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

    return exit_msg


def restart():
    """restart() triggers restart.py which triggers Jarvis after 5 seconds"""
    speaker.say('Restarting now sir! I will be up and running momentarily.')
    speaker.runAndWait()
    os.system(f'python3 restart.py')
    exit(1)


def shutdown():
    """Gets confirmation and turns off the machine"""
    global place_holder
    speaker.say(f"{random.choice(confirmation)} turn off the machine?")
    speaker.runAndWait()
    try:
        sys.stdout.write("\rListener activated..") and playsound('start.mp3')
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        sys.stdout.write("\r")
        converted = recognizer.recognize_google(listener)
        place_holder = None
        if any(word in converted.lower() for word in keywords.ok()):
            speaker.say(f"Shutting down sir!")
            speaker.say(exit_message())
            speaker.runAndWait()
            sys.stdout.write(f"\rMemory consumed: {size_converter(0)}"
                             f"\nTotal runtime: {time_converter(time.perf_counter())}")
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
    current_dir = os.listdir()  # stores the list of files in current directory
    aws = AWSClients()
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(limit * 100)

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
        if 'SetVol.exe' not in current_dir:
            sys.stdout.write("\rPLEASE WAIT::Downloading volume controller for Windows")
            os.system("""curl https://thevickypedia.com/Jarvis/SetVol.exe --output SetVol.exe --silent""")
            sys.stdout.write("\r")
    else:
        operating_system = None
        exit(0)

    # place_holder is used in all the functions so that the "I didn't quite get that..." part runs only once
    # greet_check is used in initialize() to greet only for the first run
    # tv is set to None at the start
    # waiter is used in renew() so that when waiter hits 12 count, active listener automatically goes to sentry mode
    # suggestion_count is used in google_searchparser to limit the number of times suggestions are used.
        # This is just a safety check so that Jarvis doesn't run into infinite loops while looking for suggestions.
    # threshold is used to sanity check the sentry_mode() so that Jarvis doesn't run into Fatal Python error.
        # This happens when the same functions is repeatedly called with no end::Cannot recover from stack overflow.
    place_holder, greet_check, tv = None, None, None
    waiter, suggestion_count, threshold = 0, 0, 0

    # Uses speed test api to check for internet connection
    try:
        st = Speedtest()
    except ConfigRetrievalError:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.say("I was unable to connect to the internet sir! Please check your connection settings and retry.")
        speaker.runAndWait()
        st = None
        exit()

    # initiates geo_locator and stores current location info as json so it could be used in couple of other functions
    try:
        # tries with icloud api to get your phone's location for precise location services
        icloud_user = os.getenv('icloud_user') or aws.icloud_user()
        icloud_pass = os.getenv('icloud_pass') or aws.icloud_pass()
        icloud_api = PyiCloudService(icloud_user, icloud_pass)
        raw_location = icloud_api.iphone.location()
        current_lat = raw_location['latitude']
        current_lon = raw_location['longitude']
    except (TypeError, PyiCloudAPIResponseException, PyiCloudFailedLoginException):
        # uses latitude and longitude information from your IP's client when unable to connect to icloud
        current_lat = st.results.client['lat']
        current_lon = st.results.client['lon']
        speaker.say("I had trouble accessing the iCloud API, so I'll be using your I.P address for location. "
                    "Please note that this may not be accurate enough for location services.")
        speaker.runAndWait()
    except requests.exceptions.ConnectionError:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        current_lat, current_lon = None, None
        speaker.say("I was unable to connect to the internet. Please check your connection settings and retry. "
                    "Remember to check for VPN settings, as it can also be a factor in open Wi-Fi connections.")
        speaker.runAndWait()
        exit()

    try:
        # Uses the latitude and longitude information and converts to the required address.
        options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())
        geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)
        locator = geo_locator.reverse(f'{current_lat}, {current_lon}')
        location_info = locator.raw['address']
    except (GeocoderUnavailable, GeopyError):
        speaker.say('Received an error while retrieving your address sir! I think a restart should fix this.')
        restart()

    # different responses for different conditions in sentry mode
    wake_up1 = ['Up and running sir.', 'Online and ready sir.', "I've indeed been uploaded sir!", 'Listeners have been '
                                                                                                  'activated sir!']
    wake_up2 = ['For you sir!, Always!', 'At your service sir.']
    wake_up3 = ["I'm here sir!."]

    confirmation = ['Requesting confirmation sir! Did you mean', 'Sir, are you sure you want to']
    acknowledgement = ['You got it sir!', 'Roger that!', 'Done sir!', 'By all means sir!', 'Indeed sir!', 'Gladly sir!',
                       'Without fail sir!', 'Sure sir!', 'Buttoned up sir!', 'Executed sir!']

    weekend = ['Friday', 'Saturday']
    if 'model.pcl' not in current_dir:
        sys.stdout.write("\rPLEASE WAIT::Downloading model file for punctuations")
        os.system("""curl https://thevickypedia.com/Jarvis/punctuator/model.pcl --output model.pcl --silent""")
        sys.stdout.write("\r")

    sys.stdout.write("\rPLEASE WAIT::Training model for punctuations")
    punctuation = Punctuator(model_file='model.pcl')
    database = Database()
    sys.stdout.write("\r")

    # {function_name}.has_been_called is use to denote which function has triggered the other
    report.has_been_called, locate_places.has_been_called, directions.has_been_called, maps_api.has_been_called, \
        time_travel.has_been_called = False, False, False, False, False
    for functions in [dummy, delete_todo, todo, add_todo]:
        functions.has_been_called = False

    sys.stdout.write(f"\rCurrent Process ID: {Process(os.getpid()).pid}")

    # starts sentry mode
    playsound('initialize.mp3')
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        sentry_mode()
