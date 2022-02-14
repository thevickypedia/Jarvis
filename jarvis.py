import json
import os
import random
import re
import struct
import subprocess
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email import message_from_bytes
from email.header import decode_header, make_header
from imaplib import IMAP4_SSL
from math import ceil
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from socket import gethostbyname
from string import punctuation
from threading import Thread, Timer
from time import perf_counter, sleep, time
from traceback import format_exc
from typing import Tuple
from unicodedata import normalize
from urllib.request import urlopen

import cv2
import psutil
import pvporcupine
import requests
from dotenv import load_dotenv
from geopy.distance import geodesic
from googlehomepush import GoogleHome
from googlehomepush.http_server import serve_file
from inflect import engine
from joke.jokes import chucknorris, geek, icanhazdad, icndb
from newsapi import NewsApiClient, newsapi_exception
from playsound import playsound
from pyaudio import PyAudio, paInt16
from pychromecast.error import ChromecastConnectionError
from PyDictionary import PyDictionary
from pytz import timezone
from randfacts import getFact
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from timezonefinder import TimezoneFinder
from wakeonlan import send_magic_packet as wake

from api.controller import offline_compatible
from executors import revive, sms
from executors.car import vehicle
from executors.custom_logger import logger
from executors.internet import get_ssid, internet_checker, ip_info, vpn_checker
from executors.location import current_location, geo_locator, location_services
from executors.meetings import (meeting_app_launcher, meeting_file_writer,
                                meetings_gatherer)
from executors.robinhood import robinhood
from executors.unconditional import alpha, google, google_maps
from executors.wiki import wikipedia_
from modules.audio.listener import listen
from modules.audio.speaker import audio_driver, speak
from modules.audio.voices import voice_changer, voice_default
from modules.conditions import conversation, keywords
from modules.database import database
from modules.face.facial_recognition import Face
from modules.lights.lights import MagicHomeApi
from modules.lights.preset_values import PRESET_VALUES
from modules.personalcloud import pc_handler
from modules.temperature import temperature
from modules.tv.tv_controls import TV
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
    if greet_check.get('status'):
        speak(text="What can I do for you?")
    else:
        speak(text=f'Good {support.part_of_day()}.')
        greet_check['status'] = True
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

    elif any(word in converted_lower for word in keywords.gmail):
        gmail()

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

    elif any(word in converted_lower for word in keywords.alarm):
        alarm(phrase=converted)

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
        return sleep_control(phrase=converted)

    elif any(word in converted_lower for word in keywords.restart_control):
        restart_control(phrase=converted)

    elif any(word in converted_lower for word in keywords.kill) and \
            not any(word in converted_lower for word in keywords.avoid):
        raise KeyboardInterrupt

    elif any(word in converted_lower for word in keywords.shutdown):
        shutdown()

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
    year = str(datetime.now().year)
    event = support.celebrate()
    if time_travel.has_been_called:
        dt_string = f'{dt_string} {date_}'
    else:
        dt_string = f'{dt_string} {date_}, {year}'
    speak(text=f"It's {dt_string}")
    if event and event == 'Birthday':
        speak(text=f"It's also your {event} sir!")
    elif event:
        speak(text=f"It's also {event} sir!")
    if report.has_been_called or time_travel.has_been_called:
        speak(text='The current time is, ')


def current_time(converted: str = None) -> None:
    """Says current time at the requested location if any, else with respect to the current timezone.

    Args:
        converted: Takes the phrase as an argument.
    """
    place = support.get_capitalized(phrase=converted) if converted else None
    if place and len(place) > 3:
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
            speak(text=f'The current time in {time_location} is {time_tz}, on {date_tz}.')
        else:
            speak(text=f'The current time in {time_location} is {time_tz}.')
    else:
        c_time = datetime.now().strftime("%I:%M %p")
        speak(text=f'{c_time}.')


def weather(phrase: str = None) -> None:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    Args:
        phrase: Takes the phrase as an optional argument.
    """
    if not weather_api:
        support.no_env_vars()
        return

    place = None
    if phrase:
        place = support.get_capitalized(phrase=phrase)
    sys.stdout.write('\rGetting your weather info')
    if place:
        desired_location = geo_locator.geocode(place)
        coordinates = desired_location.latitude, desired_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        address = located.raw['address']
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        lat = located.latitude
        lon = located.longitude
    else:
        city = globals.current_location_['location_info']['city']
        state = globals.current_location_['location_info']['state']
        lat = globals.current_location_['current_lat']
        lon = globals.current_location_['current_lon']
    weather_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,' \
                  f'hourly&appid={weather_api}'
    response = json.loads(urlopen(weather_url).read())  # loads the response in a json

    weather_location = f'{city} {state}'.replace('None', '') if city != state else city or state

    if any(match_word in phrase.lower() for match_word in
           ['tomorrow', 'day after', 'next week', 'tonight', 'afternoon', 'evening']):
        if 'tonight' in phrase:
            key = 0
            tell = 'tonight'
        elif 'day after' in phrase:
            key = 2
            tell = 'day after tomorrow '
        elif 'tomorrow' in phrase:
            key = 1
            tell = 'tomorrow '
        elif 'next week' in phrase:
            key = -1
            next_week = datetime.fromtimestamp(response['daily'][-1]['dt']).strftime("%A, %B %d")
            tell = f"on {' '.join(next_week.split()[0:-1])} {engine().ordinal(next_week.split()[-1])}"
        else:
            key = 0
            tell = 'today '
        if 'morning' in phrase:
            when = 'morn'
            tell += 'morning'
        elif 'evening' in phrase:
            when = 'eve'
            tell += 'evening'
        elif 'tonight' in phrase:
            when = 'night'
        elif 'night' in phrase:
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
        condition = response['daily'][key]['weather'][0]['description']
        high = int(round(temperature.k2f(response['daily'][key]['temp']['max']), 2))
        low = int(round(temperature.k2f(response['daily'][1]['temp']['min']), 2))
        temp_f = int(round(temperature.k2f(response['daily'][key]['temp'][when]), 2))
        temp_feel_f = int(round(temperature.k2f(response['daily'][key]['feels_like'][when]), 2))
        sunrise = datetime.fromtimestamp(response['daily'][key]['sunrise']).strftime("%I:%M %p")
        sunset = datetime.fromtimestamp(response['daily'][key]['sunset']).strftime("%I:%M %p")
        output = f"The weather in {weather_location} {tell} would be {temp_f}°F, with a high of {high}, and a low of " \
                 f"{low}. "
        if temp_feel_f != temp_f:
            output += f"But due to {condition} it will fee like it is {temp_feel_f}°F. "
        output += f"Sunrise at {sunrise}. Sunset at {sunset}. "
        if alerts and start_alert and end_alert:
            output += f'There is a weather alert for {alerts} between {start_alert} and {end_alert}'
        speak(text=output)
        return

    condition = response['current']['weather'][0]['description']
    high = int(round(temperature.k2f(arg=response['daily'][0]['temp']['max']), 2))
    low = int(round(temperature.k2f(arg=response['daily'][0]['temp']['min']), 2))
    temp_f = int(round(temperature.k2f(arg=response['current']['temp']), 2))
    temp_feel_f = int(round(temperature.k2f(arg=response['current']['feels_like']), 2))
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
    speak(text=output)


def system_info() -> None:
    """Speaks the system information."""
    speak(text=support.system_info())


def news(news_source: str = 'fox') -> None:
    """Says news around the user's location.

    Args:
        news_source: Source from where the news has to be fetched. Defaults to ``fox``.
    """
    if not (news_api := os.environ.get('news_api')):
        support.no_env_vars()
        return

    sys.stdout.write(f'\rGetting news from {news_source} news.')
    news_client = NewsApiClient(api_key=news_api)
    try:
        all_articles = news_client.get_top_headlines(sources=f'{news_source}-news')
    except newsapi_exception.NewsAPIException:
        all_articles = None
        speak(text="I wasn't able to get the news sir! I think the News API broke, you may try after sometime.")

    if all_articles:
        speak(text="News around you!")
        for article in all_articles['articles']:
            speak(text=article['title'])
        if globals.called_by_offline['status']:
            return

    if report.has_been_called or time_travel.has_been_called:
        speak(run=True)


def apps(phrase: str) -> None:
    """Launches the requested application and if Jarvis is unable to find the app, asks for the app name from the user.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    keyword = phrase.split()[-1] if phrase else None
    ignore = ['app', 'application']
    if not keyword or keyword in ignore:
        if globals.called_by_offline['status']:
            speak(text='I need an app name to open sir!')
            return
        speak(text="Which app shall I open sir?", run=True)
        keyword = listen(timeout=3, phrase_limit=4)
        if keyword != 'SR_ERROR':
            if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                return
        else:
            speak(text="I didn't quite get that. Try again.")
            return

    all_apps = subprocess.check_output("ls /Applications/", shell=True)
    apps_ = all_apps.decode('utf-8').split('\n')

    app_check = False
    for app in apps_:
        if re.search(keyword, app, flags=re.IGNORECASE) is not None:
            keyword = app
            app_check = True
            break

    if not app_check:
        speak(text=f"I did not find the app {keyword}. Try again.")
        Thread(target=support.unrecognized_dumper, args=[{'APPLICATIONS': keyword}]).start()
        return
    else:
        app_status = os.system(f"open /Applications/'{keyword}' > /dev/null 2>&1")
        keyword = keyword.replace('.app', '')
        if app_status == 256:
            speak(text=f"I'm sorry sir! I wasn't able to launch {keyword}. "
                       f"You might need to check its permissions.")
        else:
            speak(text=f"I have opened {keyword}")


def repeat() -> None:
    """Repeats whatever is heard."""
    speak(text="Please tell me what to repeat.", run=True)
    keyword = listen(timeout=3, phrase_limit=10)
    if keyword != 'SR_ERROR':
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            pass
        else:
            speak(text=f"I heard {keyword}")


def location() -> None:
    """Gets the user's current location."""
    speak(text=f"You're at {globals.current_location_['location_info']['city']} "
               f"{globals.current_location_['location_info']['state']}, "
               f"in {globals.current_location_['location_info']['country']}")


def locate(phrase: str, no_repeat: bool = False) -> None:
    """Locates an Apple device using icloud api for python.

    Args:
        no_repeat: A placeholder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
        phrase: Takes the voice recognized statement as argument and extracts device name from it.
    """
    if not (target_device := support.device_selector(icloud_user=icloud_user, icloud_pass=icloud_pass, phrase=phrase)):
        support.no_env_vars()
        return
    sys.stdout.write(f"\rLocating your {target_device}")
    if no_repeat:
        speak(text="Would you like to get the location details?")
    else:
        target_device.play_sound()
        before_keyword, keyword, after_keyword = str(target_device).partition(':')  # partitions the hostname info
        if before_keyword == 'Accessory':
            after_keyword = after_keyword.replace("Vignesh’s", "").replace("Vignesh's", "").strip()
            speak(text=f"I've located your {after_keyword} sir!")
        else:
            speak(text=f"Your {before_keyword} should be ringing now sir!")
        speak(text="Would you like to get the location details?")
    speak(run=True)
    phrase_location = listen(timeout=3, phrase_limit=3)
    if phrase_location == 'SR_ERROR':
        if no_repeat:
            return
        speak(text="I didn't quite get that. Try again.")
        locate(phrase=phrase, no_repeat=True)
    else:
        if any(word in phrase_location.lower() for word in keywords.ok):
            ignore_lat, ignore_lon, location_info_ = location_services(target_device)
            lookup = str(target_device).split(':')[0].strip()
            if location_info_ == 'None':
                speak(text=f"I wasn't able to locate your {lookup} sir! It is probably offline.")
            else:
                post_code = '"'.join(list(location_info_['postcode'].split('-')[0]))
                iphone_location = f"Your {lookup} is near {location_info_['road']}, {location_info_['city']} " \
                                  f"{location_info_['state']}. Zipcode: {post_code}, {location_info_['country']}"
                speak(text=iphone_location)
                stat = target_device.status()
                bat_percent = f"Battery: {round(stat['batteryLevel'] * 100)} %, " if stat['batteryLevel'] else ''
                device_model = stat['deviceDisplayName']
                phone_name = stat['name']
                speak(text=f"Some more details. {bat_percent} Name: {phone_name}, Model: {device_model}")
            if icloud_recovery := os.environ.get('icloud_recovery'):
                speak(text="I can also enable lost mode. Would you like to do it?", run=True)
                phrase_lost = listen(timeout=3, phrase_limit=3)
                if any(word in phrase_lost.lower() for word in keywords.ok):
                    message = 'Return my phone immediately.'
                    target_device.lost_device(number=icloud_recovery, text=message)
                    speak(text="I've enabled lost mode on your phone.")
                else:
                    speak(text="No action taken sir!")


def music(phrase: str = None) -> None:
    """Scans music directory in the user profile for ``.mp3`` files and plays using default player.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    sys.stdout.write("\rScanning music files...")
    get_all_files = (os.path.join(root, f) for root, _, files in os.walk(f"{home}/Music") for f in files)
    if music_files := [file for file in get_all_files if os.path.splitext(file)[1] == '.mp3']:
        chosen = random.choice(music_files)
        if phrase and 'speaker' in phrase:
            google_home(device=phrase, file=chosen)
        else:
            subprocess.call(["open", chosen])
            support.flush_screen()
            speak(text="Enjoy your music sir!")
    else:
        speak(text='No music files were found sir!')


def gmail() -> None:
    """Reads unread emails from the gmail account for which the credentials are stored in env variables."""
    if not all([gmail_user, gmail_pass]):
        support.no_env_vars()
        return

    sys.stdout.write("\rFetching unread emails..")
    try:
        mail = IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(gmail_user, gmail_pass)
        mail.list()
        mail.select('inbox')  # choose inbox
    except TimeoutError as TimeOut:
        logger.error(TimeOut)
        speak(text="I wasn't able to check your emails sir. You might need to check to logs.")
        return

    return_code, messages = mail.search(None, 'UNSEEN')  # looks for unread emails
    if return_code == 'OK':
        n = len(messages[0].split())
    else:
        speak(text="I'm unable access your email sir.")
        return
    if n == 0:
        speak(text="You don't have any emails to catch up sir")
        return
    else:
        if globals.called_by_offline['status']:
            speak(text=f'You have {n} unread emails sir.')
            return
        else:
            speak(text=f'You have {n} unread emails sir. Do you want me to check it?', run=True)
        response = listen(timeout=3, phrase_limit=3)
        if response == 'SR_ERROR':
            return
        if not any(word in response.lower() for word in keywords.ok):
            return
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
                    speak(text=f"You have an email from, {sender}, with subject, {subject}, {receive}", run=True)


def flip_a_coin() -> None:
    """Says ``heads`` or ``tails`` from a random choice."""
    playsound('indicators/coin.mp3')
    sleep(0.5)
    speak(text=f"""{random.choice(['You got', 'It landed on', "It's"])} {random.choice(['heads', 'tails'])} sir!""")


def facts() -> None:
    """Tells a random fact."""
    speak(text=getFact(filter=False))


def meaning(phrase: str) -> None:
    """Gets meaning for a word skimmed from the user statement using PyDictionary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    keyword = phrase.split()[-1] if phrase else None
    dictionary = PyDictionary()
    if not keyword or keyword == 'word':
        speak(text="Please tell a keyword.", run=True)
        response = listen(timeout=3, phrase_limit=3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.exit_):
                return
            else:
                meaning(phrase=response)
    else:
        definition = dictionary.meaning(keyword)
        if definition:
            n = 0
            vowel = ['A', 'E', 'I', 'O', 'U']
            for key, value in definition.items():
                insert = 'an' if key[0] in vowel else 'a'
                repeated = 'also' if n != 0 else ''
                n += 1
                mean = ', '.join(value[0:2])
                speak(text=f'{keyword} is {repeated} {insert} {key}, which means {mean}.')
            if globals.called_by_offline['status']:
                return
            speak(text=f'Do you wanna know how {keyword} is spelled?', run=True)
            response = listen(timeout=3, phrase_limit=3)
            if any(word in response.lower() for word in keywords.ok):
                for letter in list(keyword.lower()):
                    speak(text=letter)
                speak(run=True)
        elif globals.called_by_offline['status']:
            speak(text=f"I'm sorry sir! I was unable to get meaning for the word: {keyword}")
            return
        else:
            speak(text="Keyword should be a single word sir! Try again")
    return


def create_db() -> None:
    """Creates a database for to-do list by calling the ``create_db`` function in ``database`` module."""
    speak(text=database.create_db())
    if todo.has_been_called:
        todo.has_been_called = False
        todo()
    elif add_todo.has_been_called:
        add_todo.has_been_called = False
        add_todo()


def todo(no_repeat: bool = False) -> None:
    """Says the item and category stored in the to-do list.

    Args:
        no_repeat: A placeholder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
    """
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(database.TASKS_DB) and (time_travel.has_been_called or report.has_been_called):
        pass
    elif not os.path.isfile(database.TASKS_DB):
        if globals.called_by_offline['status']:
            speak(text="Your don't have any items in your to-do list sir!")
            return
        if no_repeat:
            speak(text="Would you like to create a database for your to-do list?")
        else:
            speak(text="You don't have a database created for your to-do list sir. Would you like to spin up one now?")
        speak(run=True)
        key = listen(timeout=3, phrase_limit=3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok):
                todo.has_been_called = True
                support.flush_screen()
                create_db()
            else:
                return
        else:
            if no_repeat:
                return
            speak(text="I didn't quite get that. Try again.")
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
        support.flush_screen()
        if result:
            if globals.called_by_offline['status']:
                speak(text=json.dumps(result))
                return
            speak(text='Your to-do items are')
            for category, item in result.items():  # browses dictionary and stores result in response and says it
                response = f"{item}, in {category} category."
                speak(text=response)
        elif report.has_been_called and not time_travel.has_been_called:
            speak(text="You don't have any tasks in your to-do list sir.")
        elif time_travel.has_been_called:
            pass
        else:
            speak(text="You don't have any tasks in your to-do list sir.")

    if report.has_been_called or time_travel.has_been_called:
        speak(run=True)


def add_todo() -> None:
    """Adds new items to the to-do list."""
    sys.stdout.write("\rLooking for to-do database..")
    # if database file is not found calls create_db()
    if not os.path.isfile(database.TASKS_DB):
        support.flush_screen()
        speak(text="You don't have a database created for your to-do list sir.")
        speak(text="Would you like to spin up one now?", run=True)
        key = listen(timeout=3, phrase_limit=3)
        if key != 'SR_ERROR':
            if any(word in key.lower() for word in keywords.ok):
                add_todo.has_been_called = True
                support.flush_screen()
                create_db()
            else:
                return
    speak(text="What's your plan sir?", run=True)
    item = listen(timeout=3, phrase_limit=5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            speak(text='Your to-do list has been left intact sir.')
        else:
            speak(text=f"I heard {item}. Which category you want me to add it to?", run=True)
            category = listen(timeout=3, phrase_limit=3)
            if category == 'SR_ERROR':
                category = 'Unknown'
            if 'exit' in category or 'quit' in category or 'Xzibit' in category:
                speak(text='Your to-do list has been left intact sir.')
            else:
                # passes the category and item to uploader() in modules/database.py which updates the database
                response = database.uploader(category, item)
                speak(text=response)
                speak(text="Do you want to add anything else to your to-do list?", run=True)
                category_continue = listen(timeout=3, phrase_limit=3)
                if any(word in category_continue.lower() for word in keywords.ok):
                    add_todo()
                else:
                    speak(text='Alright')


def delete_todo() -> None:
    """Deletes items from an existing to-do list."""
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(database.TASKS_DB):
        speak(text="You don't have a database created for your to-do list sir.")
        return
    speak(text="Which one should I remove sir?", run=True)
    item = listen(timeout=3, phrase_limit=5)
    if item != 'SR_ERROR':
        if 'exit' in item or 'quit' in item or 'Xzibit' in item:
            return
        response = database.deleter(keyword=item.lower())
        # if the return message from database starts with 'Looks' it means that the item wasn't matched for deletion
        speak(text=response, run=True)


def delete_db() -> None:
    """Deletes the ``tasks.db`` database file after getting confirmation."""
    if not os.path.isfile(database.TASKS_DB):
        speak(text='I did not find any database sir.')
        return
    else:
        speak(text=f'{random.choice(conversation.confirmation)} delete your database?', run=True)
        response = listen(timeout=3, phrase_limit=3)
        if response != 'SR_ERROR':
            if any(word in response.lower() for word in keywords.ok):
                os.remove(database.TASKS_DB)
                speak(text="I've removed your database sir.")
            else:
                speak(text="Your database has been left intact sir.")
            return


def distance(phrase):
    """Extracts the start and end location to get the distance for it.

    Args:
        phrase:Takes the phrase spoken as an argument.

    See Also:
        A loop differentiates between two-worded places and one-worded place.
        A condition below assumes two different words as two places but not including two words starting upper case
    right next to each other

    Examples:
        New York will be considered as one word and New York and Las Vegas will be considered as two words.
    """
    check = phrase.split()  # str to list
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

    if len(places) >= 2:
        start = places[0]
        end = places[1]
    elif len(places) == 1:
        start = None
        end = places[0]
    else:
        start, end = None, None
    distance_controller(start, end)


def distance_controller(origin: str = None, destination: str = None) -> None:
    """Calculates distance between two locations.

    Args:
        origin: Takes the starting place name as an optional argument.
        destination: Takes the destination place name as optional argument.

    Notes:
        - If ``origin`` is None, Jarvis takes the current location as ``origin``.
        - If ``destination`` is None, Jarvis will ask for a destination from the user.
    """
    if not destination:
        speak(text="Destination please?")
        if globals.called_by_offline['status']:
            return
        speak(run=True)
        destination = listen(timeout=3, phrase_limit=4)
        if destination != 'SR_ERROR':
            if len(destination.split()) > 2:
                speak(text="I asked for a destination sir, not a sentence. Try again.")
                distance_controller()
            if 'exit' in destination or 'quit' in destination or 'Xzibit' in destination:
                return

    if origin:
        # if starting_point is received gets latitude and longitude of that location
        desired_start = geo_locator.geocode(origin)
        sys.stdout.write(f"\r{desired_start.address} **")
        start = desired_start.latitude, desired_start.longitude
        start_check = None
    else:
        # else gets latitude and longitude information of current location
        start = (globals.current_location_['current_lat'], globals.current_location_['current_lon'])
        start_check = 'My Location'
    sys.stdout.write("::TO::") if origin else sys.stdout.write("\r::TO::")
    desired_location = geo_locator.geocode(destination)
    if desired_location:
        end = desired_location.latitude, desired_location.longitude
    else:
        end = destination[0], destination[1]
    if not all(isinstance(v, float) for v in start) or not all(isinstance(v, float) for v in end):
        speak(text=f"I don't think {destination} exists sir!")
        return
    miles = round(geodesic(start, end).miles)  # calculates miles from starting point to destination
    sys.stdout.write(f"** {desired_location.address} - {miles}")
    if directions.has_been_called:
        # calculates drive time using d = s/t and distance calculation is only if location is same country
        directions.has_been_called = False
        avg_speed = 60
        t_taken = miles / avg_speed
        if miles < avg_speed:
            drive_time = int(t_taken * 60)
            speak(text=f"It might take you about {drive_time} minutes to get there sir!")
        else:
            drive_time = ceil(t_taken)
            if drive_time == 1:
                speak(text=f"It might take you about {drive_time} hour to get there sir!")
            else:
                speak(text=f"It might take you about {drive_time} hours to get there sir!")
    elif start_check:
        speak(text=f"Sir! You're {miles} miles away from {destination}.")
        if not locate_places.has_been_called:  # promotes using locate_places() function
            speak(text=f"You may also ask where is {destination}")
    else:
        speak(text=f"{origin} is {miles} miles away from {destination}.")
    return


def locate_places(phrase: str = None) -> None:
    """Gets location details of a place.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    place = support.get_capitalized(phrase=phrase) if phrase else None
    # if no words found starting with an upper case letter, fetches word after the keyword 'is' eg: where is Chicago
    if not place:
        keyword = 'is'
        before_keyword, keyword, after_keyword = phrase.partition(keyword)
        place = after_keyword.replace(' in', '').strip()
    if not place:
        if globals.called_by_offline['status']:
            speak(text='I need a location to get you the details sir!')
            return
        speak(text="Tell me the name of a place!", run=True)
        converted = listen(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            place = support.get_capitalized(phrase=converted)
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
            speak(text=f"{place} is a country")
        elif place in (city or county):
            speak(text=f"{place} is in {state}" if country == globals.current_location_['location_info']['country'] else
                  f"{place} is in {state} in {country}")
        elif place in state:
            speak(text=f"{place} is a state in {country}")
        elif (city or county) and state and country:
            if country == globals.current_location_['location_info']['country']:
                speak(text=f"{place} is in {city or county}, {state}")
            else:
                speak(text=f"{place} is in {city or county}, {state}, in {country}")
        if globals.called_by_offline['status']:
            return
        locate_places.has_been_called = True
    except (TypeError, AttributeError):
        speak(text=f"{place} is not a real place on Earth sir! Try again.")
        if globals.called_by_offline['status']:
            return
        locate_places(phrase=None)
    distance_controller(origin=None, destination=place)


def directions(phrase: str = None, no_repeat: bool = False) -> None:
    """Opens Google Maps for a route between starting and destination.

    Uses reverse geocoding to calculate latitude and longitude for both start and destination.

    Args:
        phrase: Takes the phrase spoken as an argument.
        no_repeat: A placeholder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
    """
    place = support.get_capitalized(phrase=phrase)
    place = place.replace('I ', '').strip() if place else None
    if not place:
        speak(text="You might want to give a location.", run=True)
        converted = listen(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            place = support.get_capitalized(phrase=phrase)
            place = place.replace('I ', '').strip()
            if not place:
                if no_repeat:
                    return
                speak(text="I can't take you to anywhere without a location sir!")
                directions(phrase=None, no_repeat=True)
            if 'exit' in place or 'quit' in place or 'Xzibit' in place:
                return
    destination_location = geo_locator.geocode(place)
    if not destination_location:
        return
    try:
        coordinates = destination_location.latitude, destination_location.longitude
    except AttributeError:
        return
    located = geo_locator.reverse(coordinates, language='en')
    data = located.raw
    address = data['address']
    end_country = address['country'] if 'country' in address else None
    end = f"{located.latitude},{located.longitude}"

    start_country = globals.current_location_['location_info']['country']
    start = globals.current_location_['current_lat'], globals.current_location_['current_lon']
    maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
    webbrowser.open(maps_url)
    speak(text="Directions on your screen sir!")
    if start_country and end_country:
        if re.match(start_country, end_country, flags=re.IGNORECASE):
            directions.has_been_called = True
            distance_controller(origin=None, destination=place)
        else:
            speak(text="You might need a flight to get there!")
    return


def alarm(phrase: str) -> None:
    """Passes hour, minute and am/pm to ``Alarm`` class which initiates a thread for alarm clock in the background.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts time from it.
    """
    phrase = phrase.lower()
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', phrase) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', phrase) or re.findall(r'([0-9]+\s?(?:am|pm:?))', phrase)
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
            os.system(f'mkdir -p alarm && touch alarm/{hour}_{minute}_{am_pm}.lock')
            if 'wake' in phrase.strip():
                speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"I will wake you up at {hour}:{minute} {am_pm}.")
            else:
                speak(text=f"{random.choice(conversation.acknowledgement)}! "
                           f"Alarm has been set for {hour}:{minute} {am_pm}.")
        else:
            speak(text=f"An alarm at {hour}:{minute} {am_pm}? Are you an alien? "
                       f"I don't think a time like that exists on Earth.")
    else:
        speak(text='Please tell me a time sir!')
        if globals.called_by_offline['status']:
            return
        speak(run=True)
        converted = listen(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            else:
                alarm(converted)


def kill_alarm() -> None:
    """Removes lock file to stop the alarm which rings only when the certain lock file is present."""
    alarm_state = support.lock_files(alarm_files=True)
    if not alarm_state:
        speak(text="You have no alarms set sir!")
    elif len(alarm_state) == 1:
        hour, minute, am_pm = alarm_state[0][0:2], alarm_state[0][3:5], alarm_state[0][6:8]
        os.remove(f"alarm/{alarm_state[0]}")
        speak(text=f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
    else:
        sys.stdout.write(f"\r{', '.join(alarm_state).replace('.lock', '')}")
        speak(text="Please let me know which alarm you want to remove. Current alarms on your screen sir!", run=True)
        converted = listen(timeout=3, phrase_limit=4)
        if converted == 'SR_ERROR':
            return
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
            speak(text=f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
        else:
            speak(text=f"I wasn't able to find an alarm at {hour}:{minute} {am_pm}. Try again.")


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
    """Uses ``socket lib`` to extract ip address and scan ip range for Google home devices.

    Notes:
        - Can also play music on multiple devices at once.

    See Also:
        - https://github.com/deblockt/google-home-push/pull/7
        - Instead of commenting/removing the final print statement on: site-packages/googlehomepush/__init__.py

            - ``sys.stdout = open(os.devnull, 'w')`` is used to suppress any print statements.
            - To enable this again at a later time use ``sys.stdout = sys.__stdout__``

        - When music is played and immediately stopped/tasked the Google home device, it is most likely to except.
        - Broken Pipe error. This usually happens when a socket is written after it is fully closed.
        - This error occurs when one end of the connection tries sending data while the other has closed the connection.
        - This can simply be ignored or handled adding the code below in socket module (NOT PREFERRED).

        .. code-block:: python

            except IOError as error:
                import errno
                if error.errno != errno.EPIPE:
                    sys.stdout.write(error)

    Args:
        device: Name of the Google home device on which the music has to be played.
        file: Scanned audio file to be played.
    """
    network_id = vpn_checker()
    if network_id.startswith('VPN'):
        return

    if not globals.called_by_offline['status']:
        speak(text='Scanning your IP range for Google Home devices sir!', run=True)
        sys.stdout.write('\rScanning your IP range for Google Home devices..')
    network_id = '.'.join(network_id.split('.')[0:3])

    def ip_scan(host_id: int) -> Tuple[str, str]:
        """Scans the IP range using the received args as host id in an IP address.

        Args:
            host_id: Host ID passed in a multithreaded fashion to scan for Google home devices in IP range.

        Returns:
            Tuple(str, str):
            Device name, and it's IP address.
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

    devices = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        for info in executor.map(ip_scan, range(1, 101)):  # scans host IDs 1 to 255 (eg: 192.168.1.1 to 192.168.1.255)
            devices.append(info)  # this includes all the NoneType values returned by unassigned host IDs
    devices = dict([i for i in devices if i])  # removes None values and converts list to dictionary of name and ip pair

    if not device or not file:
        support.flush_screen()
        speak(text=f"You have {len(devices)} devices in your IP range sir! {comma_separator(list(devices.keys()))}. "
                   f"You can choose one and ask me to play some music on any of these.")
        return
    else:
        chosen = [value for key, value in devices.items() if key.lower() in device.lower()]
        if not chosen:
            speak(text="I don't see any matching devices sir!. Let me help you.")
            google_home()
        for target in chosen:
            file_url = serve_file(file, "audio/mp3")  # serves the file on local host and generates the play url
            support.flush_screen()
            sys.stdout = open(os.devnull, 'w')  # suppresses print statement from "googlehomepush/__init.py__"
            GoogleHome(host=target).play(file_url, "audio/mp3")
            sys.stdout = sys.__stdout__  # removes print statement's suppression above
        if len(chosen) == 1:
            speak(text="Enjoy your music sir!", run=True)
        else:
            speak(text=f"That's interesting, you've asked me to play on {len(chosen)} devices at a time. "
                       f"I hope you'll enjoy this sir.", run=True)


def jokes() -> None:
    """Uses jokes lib to say chucknorris jokes."""
    speak(text=random.choice([geek, icanhazdad, chucknorris, icndb])())


def reminder(phrase: str) -> None:
    """Passes hour, minute, am/pm and reminder message to Reminder class which initiates a thread for reminder.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts the time and message from it.
    """
    message = re.search(' to (.*) at ', phrase) or re.search(' about (.*) at ', phrase)
    if not message:
        message = re.search(' to (.*)', phrase) or re.search(' about (.*)', phrase)
        if not message:
            speak(text='Reminder format should be::Remind me to do something, at some time.')
            sys.stdout.write('\rReminder format should be::Remind ME to do something, AT some time.')
            return
    phrase = phrase.lower()
    extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', phrase) or \
        re.findall(r'([0-9]+\s?(?:a.m.|p.m.:?))', phrase) or re.findall(r'([0-9]+\s?(?:am|pm:?))', phrase)
    if not extracted_time:
        if globals.called_by_offline['status']:
            speak(text='Reminder format should be::Remind me to do something, at some time.')
            return
        speak(text="When do you want to be reminded sir?", run=True)
        phrase = listen(timeout=3, phrase_limit=4)
        if phrase != 'SR_ERROR':
            extracted_time = re.findall(r'([0-9]+:[0-9]+\s?(?:a.m.|p.m.:?))', phrase) or re.findall(
                r'([0-9]+\s?(?:a.m.|p.m.:?))', phrase)
        else:
            return
    if message and extracted_time:
        to_about = 'about' if 'about' in phrase else 'to'
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
            os.system(f'mkdir -p reminder && touch reminder/{hour}_{minute}_{am_pm}-{message.replace(" ", "_")}.lock')
            speak(text=f"{random.choice(conversation.acknowledgement)}! "
                       f"I will remind you {to_about} {message}, at {hour}:{minute} {am_pm}.")
        else:
            speak(text=f"A reminder at {hour}:{minute} {am_pm}? Are you an alien? "
                       f"I don't think a time like that exists on Earth.")
    else:
        speak(text='Reminder format should be::Remind me to do something, at some time.')
        sys.stdout.write('Reminder format should be::Remind ME to do something, AT some time.')
    return


def notes() -> None:
    """Listens to the user and saves everything to a ``notes.txt`` file."""
    converted = listen(timeout=5, phrase_limit=10)
    if converted != 'SR_ERROR':
        if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
            return
        else:
            with open(r'notes.txt', 'a') as writer:
                writer.write(f"{datetime.now().strftime('%A, %B %d, %Y')}\n{datetime.now().strftime('%I:%M %p')}\n"
                             f"{converted}\n")


def github(phrase: str):
    """Pre-process to check the phrase received and call the ``GitHub`` function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    git_user = os.environ.get('git_user')
    git_pass = os.environ.get('git_pass')
    if not all([git_user, git_pass]):
        support.no_env_vars()
        return
    auth = HTTPBasicAuth(git_user, git_pass)
    response = requests.get('https://api.github.com/user/repos?type=all&per_page=100', auth=auth).json()
    result, repos, total, forked, private, archived, licensed = [], [], 0, 0, 0, 0, 0
    for i in range(len(response)):
        total += 1
        forked += 1 if response[i]['fork'] else 0
        private += 1 if response[i]['private'] else 0
        archived += 1 if response[i]['archived'] else 0
        licensed += 1 if response[i]['license'] else 0
        repos.append({response[i]['name'].replace('_', ' ').replace('-', ' '): response[i]['clone_url']})
    if 'how many' in phrase:
        speak(text=f'You have {total} repositories sir, out of which {forked} are forked, {private} are private, '
                   f'{licensed} are licensed, and {archived} archived.')
    else:
        [result.append(clone_url) if clone_url not in result and re.search(rf'\b{word}\b', repo.lower()) else None
         for word in phrase.lower().split() for item in repos for repo, clone_url in item.items()]
        if result:
            github_controller(target=result)
        else:
            speak(text="Sorry sir! I did not find that repo.")


def github_controller(target: list) -> None:
    """Clones the GitHub repository matched with existing repository in conditions function.

    Asks confirmation if the results are more than 1 but less than 3 else asks to be more specific.

    Args:
        target: Takes repository name as argument which has to be cloned.
    """
    if len(target) == 1:
        os.system(f"cd {home} && git clone -q {target[0]}")
        cloned = target[0].split('/')[-1].replace('.git', '')
        speak(text=f"I've cloned {cloned} on your home directory sir!")
        return
    elif len(target) <= 3:
        newest = [new.split('/')[-1] for new in target]
        sys.stdout.write(f"\r{', '.join(newest)}")
        speak(text=f"I found {len(target)} results. On your screen sir! Which one shall I clone?", run=True)
        converted = listen(timeout=3, phrase_limit=5)
        if converted != 'SR_ERROR':
            if any(word in converted.lower() for word in keywords.exit_):
                return
            if 'first' in converted.lower():
                item = 1
            elif 'second' in converted.lower():
                item = 2
            elif 'third' in converted.lower():
                item = 3
            else:
                item = None
                speak(text="Only first second or third can be accepted sir! Try again!")
                github_controller(target)
            os.system(f"cd {home} && git clone -q {target[item]}")
            cloned = target[item].split('/')[-1].replace('.git', '')
            speak(text=f"I've cloned {cloned} on your home directory sir!")
    else:
        speak(text=f"I found {len(target)} repositories sir! You may want to be more specific.")


def send_sms(phrase: str = None) -> None:
    """Sends a message to the number received.

    If no number was received, it will ask for a number, looks if it is 10 digits and then sends a message.

    Args:
        phrase: Takes phrase spoken as an argument.
    """
    number = '-'.join([str(s) for s in re.findall(r'\b\d+\b', phrase)]) if phrase else None
    if not number:
        speak(text="Please tell me a number sir!", run=True)
        number = listen(timeout=3, phrase_limit=7)
        if number != 'SR_ERROR':
            if 'exit' in number or 'quit' in number or 'Xzibit' in number:
                return
    elif len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) != 10:
        speak(text="I don't think that's a right number sir! Phone numbers are 10 digits. Try again!")
        send_sms()
    if number and len(''.join([str(s) for s in re.findall(r'\b\d+\b', number)])) == 10:
        speak(text="What would you like to send sir?", run=True)
        body = listen(timeout=3, phrase_limit=5)
        if body != 'SR_ERROR':
            speak(text=f'{body} to {number}. Do you want me to proceed?', run=True)
            converted = listen(timeout=3, phrase_limit=3)
            if converted != 'SR_ERROR':
                if any(word in converted.lower() for word in keywords.ok):
                    sms.notify(user=gmail_user, password=gmail_pass, number=number, body=body)
                    speak(text="Message has been sent sir!")
                else:
                    speak(text="Message will not be sent sir!")
                return


def television(phrase: str) -> None:
    """Controls all actions on a TV (LG Web OS).

    Notes:
        - In the ``__main__`` method tv is set to None.
        - Jarvis will try to ping the TV and then power it on if the host is unreachable initially.
        - Once the tv is turned on, the TV class is also initiated and assigned to tv variable.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    tv_client_key = os.environ.get('tv_client_key')
    if not all([globals.smart_devices.get('tv_ip'), globals.smart_devices.get('tv_mac'), tv_client_key]):
        support.no_env_vars()
        return
    global tv
    phrase_exc = phrase.replace('TV', '')
    phrase_lower = phrase_exc.lower()

    def tv_status() -> int:
        """Pings the tv and returns the status. 0 if able to ping, 256 if unable to ping."""
        return os.system(f"ping -c 1 -t 3 {globals.smart_devices.get('tv_ip')} >/dev/null")

    if vpn_checker().startswith('VPN'):
        return
    elif ('turn off' in phrase_lower or 'shutdown' in phrase_lower or 'shut down' in phrase_lower) and tv_status() != 0:
        speak(text="I wasn't able to connect to your TV sir! I guess your TV is powered off already.")
        return
    elif tv_status():
        if globals.called_by_offline['status']:
            wake(globals.smart_devices.get('tv_mac'))
        else:
            Thread(target=wake, args=[globals.smart_devices.get('tv_mac')]).start()
            speak(text="Looks like your TV is powered off sir! Let me try to turn it back on!", run=True)

    for i in range(5):
        if not tv_status():
            break
        elif i == 4:  # checks if the TV is turned ON (thrice) even before launching the TV connector
            speak(text="I wasn't able to connect to your TV sir! Please make sure you are on the "
                       "same network as your TV, and your TV is connected to a power source.")
            return
        sleep(1)

    if not tv:
        try:
            tv = TV(ip_address=globals.smart_devices.get('tv_ip'), client_key=tv_client_key)
        except ConnectionResetError as error:
            logger.error(f"Failed to connect to the TV. {error}")
            speak(text="I was unable to connect to the TV sir! It appears to be a connection issue. "
                       "You might want to try again later.")
            return
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speak(text="TV features have been integrated sir!")
            return

    if tv:
        if 'turn on' in phrase_lower or 'connect' in phrase_lower:
            speak(text='Your TV is already powered on sir!')
        elif 'increase' in phrase_lower:
            tv.increase_volume()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'decrease' in phrase_lower or 'reduce' in phrase_lower:
            tv.decrease_volume()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'mute' in phrase_lower:
            tv.mute()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'pause' in phrase_lower or 'boss' in phrase_lower or 'pass' in phrase_lower or 'hold' in phrase_lower:
            tv.pause()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'resume' in phrase_lower or 'play' in phrase_lower:
            tv.play()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'rewind' in phrase_lower:
            tv.rewind()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'forward' in phrase_lower:
            tv.forward()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'stop' in phrase_lower:
            tv.stop()
            speak(text=f'{random.choice(conversation.acknowledgement)}!')
        elif 'set' in phrase_lower and 'volume' in phrase_lower:
            vol = int(''.join([str(s) for s in re.findall(r'\b\d+\b', phrase_exc)]))
            if vol:
                tv.set_volume(target=vol)
                speak(text=f"I've set the volume to {vol}% sir.")
            else:
                speak(text=f"{vol} doesn't match the right format sir!")
        elif 'volume' in phrase_lower:
            speak(text=f"The current volume on your TV is, {tv.get_volume()}%")
        elif 'app' in phrase_lower or 'application' in phrase_lower:
            sys.stdout.write(f'\r{tv.get_apps()}')
            speak(text='App list on your screen sir!', run=True)
            sleep(5)
        elif 'open' in phrase_lower or 'launch' in phrase_lower:
            cleaned = ' '.join([w for w in phrase.split() if w not in ['launch', 'open', 'tv', 'on', 'my', 'the']])
            app_name = support.get_closest_match(text=cleaned, match_list=tv.get_apps())
            logger.info(f'{phrase} -> {app_name}')
            tv.launch_app(app_name=app_name)
            speak(text=f"I've launched {app_name} on your TV sir!")
        elif "what's" in phrase_lower or 'currently' in phrase_lower:
            speak(text=f'{tv.current_app()} is running on your TV.')
        elif 'change' in phrase_lower or 'source' in phrase_lower:
            cleaned = ' '.join([word for word in phrase.split() if word not in ('set', 'the', 'source', 'on', 'my',
                                                                                'of', 'to', 'tv')])
            source = support.get_closest_match(text=cleaned, match_list=tv.get_sources())
            logger.info(f'{phrase} -> {source}')
            tv.set_source(val=source)
            speak(text=f"I've changed the source to {source}.")
        elif 'shutdown' in phrase_lower or 'shut down' in phrase_lower or 'turn off' in phrase_lower:
            Thread(target=tv.shutdown).start()
            speak(text=f'{random.choice(conversation.acknowledgement)}! Turning your TV off.')
            tv = None
        else:
            speak(text="I didn't quite get that.")
            Thread(target=support.unrecognized_dumper, args=[{'TV': phrase}]).start()
    else:
        phrase = phrase.replace('my', 'your').replace('please', '').replace('will you', '').strip()
        speak(text=f"I'm sorry sir! I wasn't able to {phrase}, as the TV state is unknown!")


def google_search(phrase: str = None) -> None:
    """Opens up a Google search for the phrase received. If nothing was received, gets phrase from user.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.split('for')[-1] if 'for' in phrase else None
    if not phrase:
        speak(text="Please tell me the search phrase.", run=True)
        converted = listen(timeout=3, phrase_limit=5)
        if converted == 'SR_ERROR':
            return
        elif 'exit' in converted or 'quit' in converted or 'xzibit' in converted or 'cancel' in converted:
            return
        else:
            phrase = converted.lower()
    search_query = str(phrase).replace(' ', '+')
    unknown_url = f"https://www.google.com/search?q={search_query}"
    webbrowser.open(unknown_url)
    speak(text=f"I've opened up a google search for: {phrase}.")


def volume(phrase: str = None, level: int = None) -> None:
    """Controls volume from the numbers received. Defaults to 50%.

    Args:
        phrase: Takes the phrase spoken as an argument.
        level: Level of volume to which the system has to set.
    """
    if not level:
        phrase_lower = phrase.lower()
        if 'mute' in phrase_lower:
            level = 0
        elif 'max' in phrase_lower or 'full' in phrase_lower:
            level = 100
        else:
            level = re.findall(r'\b\d+\b', phrase)  # gets integers from string as a list
            level = int(level[0]) if level else 50  # converted to int for volume
    support.flush_screen()
    level = round((8 * level) / 100)
    os.system(f'osascript -e "set Volume {level}"')
    if phrase:
        speak(text=f"{random.choice(conversation.acknowledgement)}!")


def face_detection() -> None:
    """Initiates face recognition script and looks for images stored in named directories within ``train`` directory."""
    support.flush_screen()
    train_dir = 'train'
    os.mkdir(train_dir) if not os.path.isdir(train_dir) else None
    speak(text='Initializing facial recognition. Please smile at the camera for me.', run=True)
    sys.stdout.write('\rLooking for faces to recognize.')
    try:
        result = Face().face_recognition()
    except BlockingIOError:
        support.flush_screen()
        logger.error('Unable to access the camera.')
        speak(text="I was unable to access the camera. Facial recognition can work only when cameras are "
                   "present and accessible.")
        return
    if not result:
        sys.stdout.write('\rLooking for faces to detect.')
        speak(text="No faces were recognized. Switching on to face detection.", run=True)
        result = Face().face_detection()
        if not result:
            sys.stdout.write('\rNo faces were recognized nor detected.')
            speak(text='No faces were recognized. nor detected. Please check if your camera is working, '
                       'and look at the camera when you retry.')
            return
        sys.stdout.write('\rNew face has been detected. Like to give it a name?')
        speak(text='I was able to detect a face, but was unable to recognize it.')
        os.system('open cv2_open.jpg')
        speak(text="I've taken a photo of you. Preview on your screen. Would you like to give it a name, "
                   "so that I can add it to my database of known list? If you're ready, please tell me a name, "
                   "or simply say exit.", run=True)
        phrase = listen(timeout=3, phrase_limit=5)
        if phrase == 'SR_ERROR' or 'exit' in phrase or 'quit' in phrase or 'Xzibit' in phrase:
            os.remove('cv2_open.jpg')
            speak(text="I've deleted the image.", run=True)
        else:
            phrase = phrase.replace(' ', '_')
            # creates a named directory if it is not found already else simply ignores
            os.system(f'cd {train_dir} && mkdir {phrase}') if not os.path.exists(f'{train_dir}/{phrase}') else None
            c_time = datetime.now().strftime("%I_%M_%p")
            img_name = f"{phrase}_{c_time}.jpg"  # adds current time to image name to avoid overwrite
            os.rename('cv2_open.jpg', img_name)  # renames the files
            os.system(f"mv {img_name} {train_dir}/{phrase}")  # move files into named directory within train_dir
            speak(text=f"Image has been saved as {img_name}. I will be able to recognize {phrase} in the future.")
    else:
        speak(text=f'Hi {result}! How can I be of service to you?')


def speed_test() -> None:
    """Initiates speed test and says the ping rate, download and upload speed.

    References:
        Number of threads per core: https://psutil.readthedocs.io/en/latest/#psutil.cpu_count
    """
    client_locator = geo_locator.reverse(st.lat_lon, language='en')
    client_location = client_locator.raw['address']
    city = client_location.get('city') or client_location.get('residential') or \
        client_location.get('hamlet') or client_location.get('county')
    state = client_location.get('state')
    isp = st.results.client.get('isp').replace(',', '').replace('.', '')
    threads_per_core = int(psutil.cpu_count() / psutil.cpu_count(logical=False))
    upload_thread = Thread(target=st.upload, kwargs={'threads': threads_per_core})
    download_thread = Thread(target=st.download, kwargs={'threads': threads_per_core})
    upload_thread.start()
    download_thread.start()
    speak(text=f"Starting speed test sir! I.S.P: {isp}. Location: {city} {state}", run=True)
    upload_thread.join()
    download_thread.join()
    ping = round(st.results.ping)
    download = support.size_converter(byte_size=st.results.download)
    upload = support.size_converter(byte_size=st.results.upload)
    sys.stdout.write(f'\rPing: {ping}m/s\tDownload: {download}\tUpload: {upload}')
    speak(text=f'Ping rate: {ping} milli seconds. '
               f'Download speed: {download} per second. '
               f'Upload speed: {upload} per second.')


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
                    output = subprocess.getoutput(cmd=f"blueutil --disconnect {target['address']}")
                    if not output:
                        sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                        speak(text=f"Disconnected from {target['name']} sir!")
                    else:
                        speak(text=f"I was unable to disconnect {target['name']} sir!. "
                                   f"Perhaps it was never connected.")
                elif 'connect' in phrase:
                    output = subprocess.getoutput(cmd=f"blueutil --connect {target['address']}")
                    if not output:
                        sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                        speak(text=f"Connected to {target['name']} sir!")
                    else:
                        speak(text=f"Unable to connect {target['name']} sir!, please make sure the device is "
                                   f"turned on and ready to pair.")
                break
    return connection_attempt


def bluetooth(phrase: str) -> None:
    """Find and connect to bluetooth devices nearby.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    phrase = phrase.lower()
    if 'turn off' in phrase or 'power off' in phrase:
        subprocess.call("blueutil --power 0", shell=True)
        sys.stdout.write('\rBluetooth has been turned off')
        speak(text="Bluetooth has been turned off sir!")
    elif 'turn on' in phrase or 'power on' in phrase:
        subprocess.call("blueutil --power 1", shell=True)
        sys.stdout.write('\rBluetooth has been turned on')
        speak(text="Bluetooth has been turned on sir!")
    elif 'disconnect' in phrase and ('bluetooth' in phrase or 'devices' in phrase):
        subprocess.call("blueutil --power 0", shell=True)
        sleep(2)
        subprocess.call("blueutil --power 1", shell=True)
        speak(text='All bluetooth devices have been disconnected sir!')
    else:
        sys.stdout.write('\rScanning paired Bluetooth devices')
        paired = subprocess.getoutput(cmd="blueutil --paired --format json")
        paired = json.loads(paired)
        if not connector(phrase=phrase, targets=paired):
            sys.stdout.write('\rScanning UN-paired Bluetooth devices')
            speak(text='No connections were established sir, looking for un-paired devices.', run=True)
            unpaired = subprocess.getoutput(cmd="blueutil --inquiry --format json")
            unpaired = json.loads(unpaired)
            connector(phrase=phrase, targets=unpaired) if unpaired else speak(text='No un-paired devices found sir! '
                                                                                   'You may want to be more precise.')


def brightness(phrase: str):
    """Pre-process to check the phrase received and call the appropriate brightness function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    speak(text=random.choice(conversation.acknowledgement))
    if 'set' in phrase or re.findall(r'\b\d+\b', phrase):
        level = re.findall(r'\b\d+\b', phrase)  # gets integers from string as a list
        if not level:
            level = ['50']  # pass as list for brightness, as args must be iterable
        Thread(target=set_brightness, args=level).start()
    elif 'decrease' in phrase or 'reduce' in phrase or 'lower' in phrase or \
            'dark' in phrase or 'dim' in phrase:
        Thread(target=decrease_brightness).start()
    elif 'increase' in phrase or 'bright' in phrase or 'max' in phrase or \
            'brighten' in phrase or 'light up' in phrase:
        Thread(target=increase_brightness).start()


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

    - | Since Jarvis uses in-built apple script, the only way to achieve this is to set the brightness to absolute
      | minimum/maximum and increase/decrease the required % from there.

    Args:
        level: Percentage of brightness to be set.
    """
    level = round((32 * int(level)) / 100)
    for _ in range(32):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 145' -e ' end tell'""")
    for _ in range(level):
        os.system("""osascript -e 'tell application "System Events"' -e 'key code 144' -e ' end tell'""")


def lights(phrase: str) -> None:
    """Controller for smart lights.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    phrase = phrase.lower()
    if not any([globals.smart_devices.get('hallway_ip'), globals.smart_devices.get('kitchen_ip'),
                globals.smart_devices.get('bedroom_ip')]):
        support.no_env_vars()
        return

    if vpn_checker().startswith('VPN'):
        return

    def light_switch():
        """Says a message if the physical switch is toggled off."""
        speak(text="I guess your light switch is turned off sir! I wasn't able to read the device. "
                   "Try toggling the switch and ask me to restart myself!")

    def turn_off(host: str):
        """Turns off the device.

        Args:
            host: Takes target device IP address as an argument.
        """
        MagicHomeApi(device_ip=host, device_type=1, operation='Turn Off').turn_off()

    def warm(host: str):
        """Sets lights to warm/yellow.

        Args:
            host: Takes target device IP address as an argument.
        """
        MagicHomeApi(device_ip=host, device_type=1,
                     operation='Warm Lights').update_device(r=0, g=0, b=0, warm_white=255)

    def cool(host: str):
        """Sets lights to cool/white.

        Args:
            host: Takes target device IP address as an argument.
        """
        MagicHomeApi(device_ip=host, device_type=2,
                     operation='Cool Lights').update_device(r=255, g=255, b=255, warm_white=255, cool_white=255)

    def preset(host: str, value: int):
        """Changes light colors to preset values.

        Args:
            host: Takes target device IP address as an argument.
            value: Preset value extracted from list of verified values.
        """
        MagicHomeApi(device_ip=host, device_type=2,
                     operation='Preset Values').send_preset_function(preset_number=value, speed=101)

    def lumen(host: str, warm_lights: bool, rgb: int = 255):
        """Sets lights to custom brightness.

        Args:
            host: Takes target device IP address as an argument.
            warm_lights: Boolean value if lights have been set to warm or cool.
            rgb: Red, Green andBlue values to alter the brightness.
        """
        args = {'r': 255, 'g': 255, 'b': 255, 'warm_white': rgb}
        if not warm_lights:
            args.update({'cool_white': rgb})
        MagicHomeApi(device_ip=host, device_type=1, operation='Custom Brightness').update_device(**args)

    if 'hallway' in phrase:
        if not (host_ip := globals.smart_devices.get('hallway_ip')):
            light_switch()
            return
    elif 'kitchen' in phrase:
        if not (host_ip := globals.smart_devices.get('kitchen_ip')):
            light_switch()
            return
    elif 'bedroom' in phrase:
        if not (host_ip := globals.smart_devices.get('bedroom_ip')):
            light_switch()
            return
    else:
        host_ip = globals.smart_devices.get('hallway_ip') + \
                  globals.smart_devices.get('kitchen_ip') + \
                  globals.smart_devices.get('bedroom_ip')  # noqa: E126

    lights_count = len(host_ip)

    def thread_worker(function_to_call: staticmethod) -> None:
        """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        with ThreadPoolExecutor(max_workers=lights_count) as executor:
            executor.map(function_to_call, host_ip)

    plural = 'lights!' if lights_count > 1 else 'light!'
    if 'turn on' in phrase or 'cool' in phrase or 'white' in phrase:
        warm_light.pop('status') if warm_light.get('status') else None
        tone = 'white' if 'white' in phrase else 'cool'
        if 'turn on' in phrase:
            speak(text=f'{random.choice(conversation.acknowledgement)}! Turning on {lights_count} {plural}')
        else:
            speak(text=f'{random.choice(conversation.acknowledgement)}! Setting {lights_count} {plural} to {tone}!')
        Thread(target=thread_worker, args=[cool]).start()
    elif 'turn off' in phrase:
        speak(text=f'{random.choice(conversation.acknowledgement)}! Turning off {lights_count} {plural}')
        Thread(target=thread_worker, args=[turn_off]).start()
    elif 'warm' in phrase or 'yellow' in phrase:
        warm_light['status'] = True
        if 'yellow' in phrase:
            speak(text=f'{random.choice(conversation.acknowledgement)}! Setting {lights_count} {plural} to yellow!')
        else:
            speak(text=f'Sure sir! Setting {lights_count} {plural} to warm!')
        Thread(target=thread_worker, args=[warm]).start()
    elif any(word in phrase for word in list(PRESET_VALUES.keys())):
        speak(text=f"{random.choice(conversation.acknowledgement)}! I've changed {lights_count} {plural} to red!")
        for light_ip in host_ip:
            preset(host=light_ip,
                   value=[PRESET_VALUES[_type] for _type in list(PRESET_VALUES.keys()) if _type in phrase][0])
    elif 'set' in phrase or 'percentage' in phrase or '%' in phrase or 'dim' in phrase \
            or 'bright' in phrase:
        if 'bright' in phrase:
            level = 100
        elif 'dim' in phrase:
            level = 50
        else:
            if level := re.findall(r'\b\d+\b', phrase):
                level = int(level[0])
            else:
                level = 100
        speak(text=f"{random.choice(conversation.acknowledgement)}! I've set {lights_count} {plural} to {level}%!")
        level = round((255 * level) / 100)
        for light_ip in host_ip:
            lumen(host=light_ip, warm_lights=warm_light.get('status'), rgb=level)
    else:
        speak(text=f"I didn't quite get that sir! What do you want me to do to your {plural}?")
        Thread(target=support.unrecognized_dumper, args=[{'LIGHTS': phrase}]).start()


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
    gmail()
    speak(text='Would you like to hear the latest news?', run=True)
    phrase = listen(timeout=3, phrase_limit=3)
    if any(word in phrase.lower() for word in keywords.ok):
        news()
    time_travel.has_been_called = False


def guard_enable() -> None:
    """Security Mode will enable camera and microphone in the background.

    Notes:
        - If any speech is recognized or a face is detected, there will another thread triggered to send notifications.
        - Notifications will be triggered only after 5 minutes of previous notification.
    """
    logger.info('Enabled Security Mode')
    speak(text=f"Enabled security mode sir! I will look out for potential threats and keep you posted. "
               f"Have a nice {support.part_of_day()}, and enjoy yourself sir!", run=True)

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
        sms.notify(user=gmail_user, password=gmail_pass, number=phone_number, body=cam_error,
                   subject="IMPORTANT::Guardian mode faced an exception.")
        return

    scale_factor = 1.1  # Parameter specifying how much the image size is reduced at each image scale.
    min_neighbors = 5  # Parameter specifying how many neighbors each candidate rectangle should have, to retain it.
    notified, date_extn, converted = None, None, None

    while True:
        # Listens for any recognizable speech and saves it to a notes file
        sys.stdout.write("\rSECURITY MODE")
        converted = listen(timeout=3, phrase_limit=10)
        if converted == 'SR_ERROR':
            continue

        converted = converted.replace('Jarvis', '').strip()
        if converted and any(word.lower() in converted.lower() for word in keywords.guard_disable):
            logger.info('Disabled security mode')
            speak(text=f'Welcome back sir! Good {support.part_of_day()}.')
            if os.path.exists(f'threat/{date_extn}.jpg'):
                speak(text="We had a potential threat sir! Please check your email to confirm.")
            speak(run=True)
            sys.stdout.write('\rDisabled Security Mode')
            break
        elif converted:
            logger.info(f'Conversation::{converted}')

        if cam_source is not None:
            # Capture images and keeps storing it to a folder
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
            Thread(target=support.threat_notify, kwargs=({
                "converted": converted,
                "gmail_user": gmail_user,
                "gmail_pass": gmail_pass,
                "phone_number": phone_number,
                "recipient": recipient,
                "date_extn": date_extn
            })).start()


def offline_communicator(command: str = None, respond: bool = True) -> None:
    """Reads ``offline_request`` file generated by `fast.py <https://git.io/JBPFQ>`__ containing request sent via API.

    Args:
        command: Takes the command that has to be executed as an argument.
        respond: Takes the argument to decide whether to create the ``offline_response`` file.

    Env Vars:
        - ``offline_phrase`` - Phrase to authenticate the requests to API. Defaults to ``jarvis``

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
    except RuntimeError:
        if command and not response:
            with open('offline_request', 'w') as off_request:
                off_request.write(command)
        logger.fatal(f'Received a RuntimeError while executing offline request.\n{format_exc()}')
        revive.restart(quiet=True, quick=True)


def meeting_reader() -> None:
    """Speaks meeting information that ``meeting_gatherer()`` stored in a file named 'meetings'.

    If the file is not available, meeting information is directly fetched from the ``meetings()`` function.
    """
    with open('meetings', 'r') as meeting:
        meeting_info = meeting.read()
        speak(text=meeting_info)


def meetings():
    """Controller for meetings."""
    if os.path.isfile('meetings'):
        meeting_reader()
    else:
        if globals.called_by_offline['status']:
            speak(text="Meetings file is not ready yet. Please try again in a minute or two.")
            return False
        meeting = ThreadPool(processes=1).apply_async(func=meetings_gatherer)  # Runs parallely and awaits completion
        speak(text="Please give me a moment sir! Let me check your calendar.", run=True)
        try:
            speak(text=meeting.get(timeout=60), run=True)
        except ThreadTimeoutError:
            logger.error('Unable to read the calendar within 60 seconds.')
            speak(text="I wasn't able to read your calendar within the set time limit sir!", run=True)


def system_vitals() -> None:
    """Reads system vitals on macOS.

    See Also:
        - Jarvis will suggest a reboot if the system uptime is more than 2 days.
        - If confirmed, invokes `restart <https://thevickypedia.github.io/Jarvis/#jarvis.restart>`__ function.
    """
    if not (root_password := os.environ.get('root_password')):
        speak(text="You haven't provided a root password for me to read system vitals sir! "
                   "Add the root password as an environment variable for me to read.")
        return

    version = globals.hosted_device.get('os_version')
    model = globals.hosted_device.get('device')

    cpu_temp, gpu_temp, fan_speed, output = None, None, None, ""
    if version >= 10.14:  # Tested on 10.13, 10.14 and 11.6 versions
        critical_info = [each.strip() for each in (os.popen(
            f'echo {root_password} | sudo -S powermetrics --samplers smc -i1 -n1'
        )).read().split('\n') if each != '']
        support.flush_screen()

        for info in critical_info:
            if 'CPU die temperature' in info:
                cpu_temp = info.strip('CPU die temperature: ').replace(' C', '').strip()
            if 'GPU die temperature' in info:
                gpu_temp = info.strip('GPU die temperature: ').replace(' C', '').strip()
            if 'Fan' in info:
                fan_speed = info.strip('Fan: ').replace(' rpm', '').strip()
    else:
        fan_speed = subprocess.check_output(
            f'echo {root_password} | sudo -S spindump 1 1 -file /tmp/spindump.txt > /dev/null 2>&1;grep "Fan speed" '
            '/tmp/spindump.txt;sudo rm /tmp/spindump.txt', shell=True
        ).decode('utf-8')

    if cpu_temp:
        cpu = f'Your current average CPU temperature is ' \
              f'{support.format_nos(input_=temperature.c2f(arg=support.extract_nos(input_=cpu_temp)))}°F. '
        output += cpu
        speak(text=cpu)
    if gpu_temp:
        gpu = f'GPU temperature is {support.format_nos(temperature.c2f(support.extract_nos(gpu_temp)))}°F. '
        output += gpu
        speak(text=gpu)
    if fan_speed:
        fan = f'Current fan speed is {support.format_nos(support.extract_nos(fan_speed))} RPM. '
        output += fan
        speak(text=fan)

    restart_time = datetime.fromtimestamp(psutil.boot_time())
    second = (datetime.now() - restart_time).total_seconds()
    restart_time = datetime.strftime(restart_time, "%A, %B %d, at %I:%M %p")
    restart_duration = support.time_converter(seconds=second)
    output += f'Restarted on: {restart_time} - {restart_duration} ago from now.'
    if globals.called_by_offline['status']:
        speak(text=output)
        return
    sys.stdout.write(f'\r{output}')
    speak(text=f'Your {model} was last booted on {restart_time}. '
               f'Current boot time is: {restart_duration}.')
    if second >= 259_200:  # 3 days
        if boot_extreme := re.search('(.*) days', restart_duration):
            warn = int(boot_extreme.group().replace(' days', '').strip())
            speak(text=f'Sir! your {model} has been running continuously for more than {warn} days. You must '
                       f'consider a reboot for better performance. Would you like me to restart it for you sir?',
                  run=True)
            response = listen(timeout=3, phrase_limit=3)
            if any(word in response.lower() for word in keywords.ok):
                logger.info(f'JARVIS::Restarting {globals.hosted_device.get("device")}')
                revive.restart(target='PC_Proceed')


def personal_cloud(phrase: str) -> None:
    """Enables or disables personal cloud.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    # todo: Get rid of this by making personal cloud a pypi package
    phrase = phrase.lower()
    if 'enable' in phrase or 'initiate' in phrase or 'kick off' in phrase or 'start' in phrase:
        Thread(target=pc_handler.enable,
               kwargs={"target_path": home, "username": gmail_user, "password": gmail_pass,
                       "phone_number": phone_number, "recipient": recipient}).start()
        speak(text="Personal Cloud has been triggered sir! I will send the login details to your phone number "
                   "once the server is up and running.")
    elif 'disable' in phrase or 'stop' in phrase:
        Thread(target=pc_handler.disable, args=[home]).start()
        speak(text=random.choice(conversation.acknowledgement))
    else:
        speak(text="I didn't quite get that sir! Please tell me if I should enable or disable your server.")
        Thread(target=support.unrecognized_dumper, args=[{'PERSONAL_CLOUD': phrase}])


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if status := globals.vpn_status['active']:
        speak(text=f'VPN Server was recently {status}, and the process is still running sir! Please wait and retry.')
        return

    phrase = phrase.lower()
    if 'start' in phrase or 'trigger' in phrase or 'initiate' in phrase or 'enable' in phrase or 'spin up' in phrase:
        Thread(target=support.vpn_server_switch,
               kwargs={'operation': 'START', 'phone_number': phone_number, 'recipient': recipient}).start()
        speak(text='VPN Server has been initiated sir! Login details will be sent to you shortly.')
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        Thread(target=support.vpn_server_switch,
               kwargs={'operation': 'STOP', 'phone_number': phone_number, 'recipient': recipient}).start()
        speak(text='VPN Server will be shutdown sir!')
    else:
        speak(text="I don't understand the request sir! You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}])


def morning() -> None:
    """Checks for the current time of the day and day of the week to trigger a series of morning messages."""
    if datetime.now().strftime('%A') not in ['Saturday', 'Sunday'] and int(datetime.now().second) < 10:
        speak(text="Good Morning. It's 7 AM.")
        time_travel.has_been_called = True
        weather()
        time_travel.has_been_called = False
        volume(level=100)
        speak(run=True)
        volume(level=50)


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
        time_travel.has_been_called = True
        if event := support.celebrate():
            speak(text=f'Happy {event}!')
        if 'night' in key_split or 'goodnight' in key_split:
            Thread(target=pc_sleep).start()
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


def rewrite_automator(filename: str, json_object: dict) -> None:
    """Rewrites the ``automation_file`` with the updated json object.

    Args:
        filename: Name of the automation source file.
        json_object: Takes the new json object as a dictionary.
    """
    with open(filename, 'w') as file:
        logger.warning('Data has been modified. Rewriting automation data into JSON file.')
        json.dump(json_object, file, indent=2)


def on_demand_offline_automation(task: str) -> bool:
    """Makes a ``POST`` call to offline-communicator running on ``localhost`` to execute a said task.

    Args:
        task: Takes the command to be executed as an argument.

    Returns:
        bool:
        Returns a boolean ``True`` if the request was successful.
    """
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {
        'phrase': os.environ.get('offline_phrase', 'jarvis'),
        'command': task
    }

    offline_endpoint = f"http://{offline_host}:{offline_port}/offline-communicator"
    try:
        response = requests.post(url=offline_endpoint, headers=headers, data=json.dumps(data))
    except ConnectionError:
        return False
    if response.ok:
        return True


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
    offline_list = offline_compatible()
    start_1 = start_2 = time()
    while True:
        if os.path.isfile('offline_request'):
            sleep(0.1)  # Read file after 0.1 second for the content to be written
            with open('offline_request') as off_request:
                request = off_request.read()
            offline_communicator(command=request)
            support.flush_screen()
        elif os.path.isfile(automation_file):
            with open(automation_file) as read_file:
                try:
                    automation_data = json.load(read_file)
                except json.JSONDecodeError:
                    logger.error('Invalid file format. '
                                 'Logging automation data and removing the file to avoid endless errors.\n'
                                 f'{"".join(["*" for _ in range(120)])}\n\n'
                                 f'{open(automation_file).read()}\n\n'
                                 f'{"".join(["*" for _ in range(120)])}')
                    os.remove(automation_file)
                    continue

            for automation_time, automation_info in automation_data.items():
                exec_status = automation_info.get('status')
                if not (exec_task := automation_info.get('task')) or \
                        not any(word in exec_task.lower() for word in offline_list):
                    logger.error("Following entry doesn't have a task or the task is not a part of offline compatible.")
                    logger.error(f'{automation_time} - {automation_info}')
                    automation_data.pop(automation_time)
                    rewrite_automator(filename=automation_file, json_object=automation_data)
                    break  # Using break instead of continue as python doesn't like dict size change in-between a loop
                try:
                    datetime.strptime(automation_time, "%I:%M %p")
                except ValueError:
                    logger.error(f'Incorrect Datetime format: {automation_time}. '
                                 'Datetime string should be in the format: 6:00 AM. '
                                 'Removing the key-value from automation.json')
                    automation_data.pop(automation_time)
                    rewrite_automator(filename=automation_file, json_object=automation_data)
                    break  # Using break instead of continue as python doesn't like dict size change in-between a loop

                if day := automation_info.get('day'):
                    today = datetime.today().strftime('%A').upper()
                    if isinstance(day, list):
                        day_list = [d.upper() for d in day]
                        if today not in day_list:
                            continue
                    elif isinstance(day, str):
                        day = day.upper()
                        if day == 'WEEKEND' and today in ['SATURDAY', 'SUNDAY']:
                            pass
                        elif day == 'WEEKDAY' and today in ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']:
                            pass
                        elif today == day:
                            pass
                        else:
                            continue

                if automation_time != datetime.now().strftime("%-I:%M %p"):  # "%-I" to consider 06:05 AM as 6:05 AM
                    if exec_status:
                        logger.info(f"Reverting execution status flag for task: {exec_task} runs at {automation_time}")
                        automation_data[automation_time]['status'] = False
                        rewrite_automator(filename=automation_file, json_object=automation_data)
                    continue

                if exec_status:
                    continue
                exec_task = exec_task.translate(str.maketrans('', '', punctuation))  # Remove punctuations from the str
                offline_communicator(command=exec_task, respond=False)
                support.flush_screen()
                automation_data[automation_time]['status'] = True
                rewrite_automator(filename=automation_file, json_object=automation_data)

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


def alarm_executor() -> None:
    """Runs the ``alarm.mp3`` file at max volume and reverts the volume after 3 minutes."""
    volume(level=100)
    subprocess.call(["open", "indicators/alarm.mp3"])
    sleep(200)
    volume(level=50)


def reminder_executor(message: str) -> None:
    """Notifies user about the reminder and displays a notification on the device.

    Args:
        message: Takes the reminder message as an argument.
    """
    sms.notify(user=gmail_user, password=gmail_pass, number=phone_number, body=message, subject="REMINDER from Jarvis")
    os.system(f"""osascript -e 'display notification "{message}" with title "REMINDER from Jarvis"'""")


def switch_volumes() -> None:
    """Automatically puts the Mac on sleep and sets the volume to 25% at 9 PM and 50% at 6 AM."""
    hour = int(datetime.now().strftime('%H'))
    locker = """osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'"""
    if 20 >= hour >= 7:
        volume(level=50)
    elif hour >= 21 or hour <= 6:
        volume(level=20)
        Thread(target=decrease_brightness).start()
        os.system(locker)


def car(phrase: str) -> None:
    """Controls the car to lock, unlock or remote start.

    Args:
        phrase: Takes the phrase spoken as an argument.

    See Also:
        API climate controls: 31 is LO, 57 is HOT
        Car Climate controls: 58 is LO, 84 is HOT
    """
    car_email = os.environ.get('car_email')
    car_pass = os.environ.get('car_pass')
    car_pin = os.environ.get('car_pin')
    if not all([car_email, car_pass, car_pin]):
        support.no_env_vars()
        return

    disconnected = "I wasn't able to connect your car sir! Please check the logs for more information."

    if 'start' in phrase or 'set' in phrase or 'turn on' in phrase:
        extras = ''
        if climate := support.extract_nos(input_=phrase):
            climate = int(climate)
        elif 'high' in phrase or 'highest' in phrase:
            climate = 83
        elif 'low' in phrase or 'lowest' in phrase:
            climate = 57
        else:
            climate = int(temperature.k2f(arg=json.loads(urlopen(
                url=f"https://api.openweathermap.org/data/2.5/onecall?lat={globals.current_location_['current_lat']}&"
                    f"lon={globals.current_location_['current_lon']}&exclude=minutely,hourly&appid={weather_api}"
            ).read())['current']['temp']))
            extras += f'The current temperature is {climate}°F, so '

        # Custom temperature that has to be set in the vehicle
        target_temp = 83 if climate < 45 else 57 if climate > 70 else 66
        extras += f"I've configured the climate setting to {target_temp}°F"

        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=car_email, car_pass=car_pass, car_pin=car_pin,
                               operation='START', temp=target_temp - 26):
            speak(text=f'Your {car_name} has been started sir. {extras}')
        else:
            speak(text=disconnected)
    elif 'turn off' in phrase or 'stop' in phrase:
        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=car_email, car_pass=car_pass, operation='STOP', car_pin=car_pin):
            speak(text=f'Your {car_name} has been turned off sir!')
        else:
            speak(text=disconnected)
    elif 'secure' in phrase:
        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=car_email, car_pass=car_pass, operation='SECURE', car_pin=car_pin):
            speak(text=f'Guardian mode has been enabled sir! Your {car_name} is now secure.')
        else:
            speak(text=disconnected)
    elif 'unlock' in phrase:
        if globals.called_by_offline['status']:
            speak(text='Cannot unlock the car via offline communicator due to security reasons.')
            return
        playsound(sound='indicators/exhaust.mp3', block=False)
        if car_name := vehicle(car_email=car_email, car_pass=car_pass, operation='UNLOCK', car_pin=car_pin):
            speak(text=f'Your {car_name} has been unlocked sir!')
        else:
            speak(text=disconnected)
    elif 'lock' in phrase:
        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=car_email, car_pass=car_pass, operation='LOCK', car_pin=car_pin):
            speak(text=f'Your {car_name} has been locked sir!')
        else:
            speak(text=disconnected)
    else:
        speak(text="I didn't quite get that sir! What do you want me to do to your car?")
        Thread(target=support.unrecognized_dumper, args=[{'CAR': phrase}])


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
        sensitivity = float(os.environ.get('sensitivity', 0.5))
        logger.info(f'Initiating model with sensitivity: {sensitivity}')
        keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in ['jarvis']]
        self.input_device_index = input_device_index

        self.py_audio = PyAudio()
        self.detector = pvporcupine.create(
            library_path=pvporcupine.LIBRARY_PATH,
            model_path=pvporcupine.MODEL_PATH,
            keyword_paths=keyword_paths,
            sensitivities=[sensitivity]
        )
        self.audio_stream = None

    def open_stream(self):
        """Initializes an audio stream."""
        self.audio_stream = self.py_audio.open(
            rate=self.detector.sample_rate,
            channels=1,
            format=paInt16,
            input=True,
            frames_per_buffer=self.detector.frame_length,
            input_device_index=self.input_device_index
        )

    def close_stream(self):
        """Closes audio stream so that other listeners can use microphone."""
        self.py_audio.close(stream=self.audio_stream)
        self.audio_stream = None

    def start(self) -> None:
        """Runs ``audio_stream`` in a forever loop and calls ``initiator`` when the phrase ``Jarvis`` is heard."""
        timeout = int(os.environ.get('timeout', 3))
        phrase_limit = int(os.environ.get('phrase_limit', 3))
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
                    initiator(key_original=listen(timeout=timeout, phrase_limit=phrase_limit, sound=False),
                              should_return=True)
                    speak(run=True)
                elif globals.STOPPER['status']:
                    self.stop()
                    revive.restart(quiet=True)
        except KeyboardInterrupt:
            self.stop()
            if not globals.called_by_offline['status']:
                exit_process()
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


def exit_process() -> None:
    """Function that holds the list of operations done upon exit."""
    globals.STOPPER['status'] = True
    logger.info('JARVIS::Stopping Now::STOPPER flag has been set to True')
    reminders = {}
    alarms = support.lock_files(alarm_files=True)
    if reminder_files := support.lock_files(reminder_files=True):
        for file in reminder_files:
            split_val = file.replace('.lock', '').split('-')
            reminders.update({split_val[0]: split_val[-1]})
    if reminders:
        logger.info(f'JARVIS::Deleting Reminders - {reminders}')
        if len(reminders) == 1:
            speak(text='You have a pending reminder sir!')
        else:
            speak(text=f'You have {len(reminders)} pending reminders sir!')
        for key, value in reminders.items():
            speak(text=f"{value.replace('_', ' ')} at "
                       f"{key.replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')}")
    if alarms:
        logger.info(f'JARVIS::Deleting Alarms - {alarms}')
        alarms = ', and '.join(alarms) if len(alarms) != 1 else ''.join(alarms)
        alarms = alarms.replace('.lock', '').replace('_', ':').replace(':PM', ' PM').replace(':AM', ' AM')
        speak(text=f'You have a pending alarm at {alarms} sir!')
    if reminders or alarms:
        speak(text='This will be removed while shutting down!')
    speak(text='Shutting down now sir!')
    try:
        speak(text=support.exit_message(), run=True)
    except RuntimeError:
        logger.fatal(f'Received a RuntimeError while self terminating.\n{format_exc()}')
    support.remove_files()
    sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                     f"\nTotal runtime: {support.time_converter(perf_counter())}")


def pc_sleep() -> None:
    """Locks the host device using osascript and reduces brightness to bare minimum."""
    Thread(target=decrease_brightness).start()
    # os.system("""osascript -e 'tell app "System Events" to sleep'""")  # requires restarting Jarvis manually
    os.system("""osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'""")
    if not (report.has_been_called or time_travel.has_been_called):
        speak(text=random.choice(conversation.acknowledgement))


def sleep_control(phrase: str) -> bool:
    """Controls whether to stop listening or to put the host device on sleep.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    if 'pc' in phrase or 'computer' in phrase or 'imac' in phrase or \
            'screen' in phrase:
        pc_sleep()
    else:
        speak(text="Activating sentry mode, enjoy yourself sir!")
        if greet_check:
            greet_check.pop('status')
    return True


def restart_control(phrase: str):
    """Controls the restart functions based on the user request.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    if 'pc' in phrase or 'computer' in phrase or 'imac' in phrase:
        logger.info(f'JARVIS::Restart for {globals.hosted_device.get("device")} has been requested.')
        revive.restart(target='PC')
    else:
        logger.info('JARVIS::Self reboot has been requested.')
        if 'quick' in phrase or 'fast' in phrase:
            revive.restart(quick=True)
        else:
            revive.restart()


def shutdown(proceed: bool = False) -> None:
    """Gets confirmation and turns off the machine.

    Args:
        proceed: Boolean value whether to get confirmation.

    Raises:
        KeyboardInterrupt: To stop Jarvis' PID.
    """
    if not proceed:
        speak(text=f"{random.choice(conversation.confirmation)} turn off the machine?", run=True)
        converted = listen(timeout=3, phrase_limit=3)
    else:
        converted = 'yes'
    if converted != 'SR_ERROR':
        if any(word in converted.lower() for word in keywords.ok):
            support.stop_terminal()
            subprocess.call(['osascript', '-e', 'tell app "System Events" to shut down'])
            raise KeyboardInterrupt
        else:
            speak(text="Machine state is left intact sir!")
            return


def clear_logs() -> None:
    """Deletes log files that were updated before 48 hours."""
    [os.remove(f"logs/{file}") for file in os.listdir('logs') if int(datetime.now().timestamp()) - int(
        os.stat(f'logs/{file}').st_mtime) > 172_800] if os.path.exists('logs') else None


def starter() -> None:
    """Initiates crucial functions which needs to be called during start up.

    Loads the ``.env`` file so that all the necessary credentials and api keys can be accessed as ``ENV vars``

    Methods:
        - volume_controller: To default the master volume 50%.
        - voice_default: To change the voice to default value.
        - clear_logs: To purge log files older than 48 hours.
    """
    volume(level=50)
    voice_default()
    clear_logs()
    meeting_app_launcher()

    if os.path.isfile('.env'):
        logger.info('Loading .env file.')
        load_dotenv(dotenv_path='.env', verbose=True, override=True)  # loads the .env file


def initiate_background_threads() -> None:
    """Initiate background threads.

    Methods
        - offline_communicator_initiate: Initiates ngrok tunnel and Jarvis API.
        - automator: Initiates automator that executes certain functions at said time.
        - playsound: Plays a start-up sound.
    """
    Timer(interval=globals.RESTART_INTERVAL, function=stopper).start()
    Thread(target=support.offline_communicator_initiate,
           kwargs={'offline_host': offline_host, 'offline_port': offline_port, 'home': home}).start()
    Thread(target=automator).start()
    playsound(sound='indicators/initialize.mp3', block=False)


def stopper() -> None:
    """Sets the key of ``STOPPER`` flag to True."""
    globals.STOPPER['status'] = True


if __name__ == '__main__':
    globals.hosted_device = support.hosted_device_info()
    if globals.hosted_device.get('os_name') != 'macOS':
        exit('Unsupported Operating System.\nWindows support was deprecated. '
             'Refer https://github.com/thevickypedia/Jarvis/commit/cf54b69363440d20e21ba406e4972eb058af98fc')

    logger.info('JARVIS::Starting Now')

    sys.stdout.write('\rVoice ID::Female: 1/17 Male: 0/7')  # Voice ID::reference
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 10)  # increases the recursion limit by 10 times
    home = os.path.expanduser('~')  # gets the path to current user profile

    starter()  # initiates crucial functions which needs to be called during start up

    weather_api = os.environ.get('weather_api')
    gmail_user = os.environ.get('gmail_user')
    gmail_pass = os.environ.get('gmail_pass')
    recipient = os.environ.get('recipient')
    offline_host = gethostbyname('localhost')
    offline_port = int(os.environ.get('offline_port', 4483))
    icloud_user = os.environ.get('icloud_user')
    icloud_pass = os.environ.get('icloud_pass')
    phone_number = os.environ.get('phone_number')

    if st := internet_checker():
        sys.stdout.write(f'\rINTERNET::Connected to {get_ssid()}. Scanning router for connected devices.')
    else:
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speak(text="I was unable to connect to the internet sir! Please check your connection settings and retry.",
              run=True)
        sys.stdout.write(f"\rMemory consumed: {support.size_converter(0)}"
                         f"\nTotal runtime: {support.time_converter(perf_counter())}")
        support.terminator()

    # warm_light is initiated with an empty dict and the key status is set to True when requested to switch to yellow
    # greet_check is used in initialize() to greet only for the first run
    # tv is set to an empty dict instead of TV() at the start to avoid turning on the TV unnecessarily
    tv, warm_light, greet_check = None, {}, {}

    globals.current_location_ = current_location()
    globals.smart_devices = support.scan_smart_devices()

    # {function_name}.has_been_called is used to denote which function has triggered the other
    report.has_been_called, locate_places.has_been_called, directions.has_been_called, google_maps.has_been_called, \
        time_travel.has_been_called = False, False, False, False, False
    for functions in [todo, add_todo]:
        functions.has_been_called = False

    sys.stdout.write(f"\rCurrent Process ID: {psutil.Process(os.getpid()).pid}\tCurrent Volume: 50%")

    initiate_background_threads()

    Activator().start()
