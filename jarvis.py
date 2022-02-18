import json
import os
import random
import re
import struct
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta
from email import message_from_bytes
from email.header import decode_header, make_header
from imaplib import IMAP4_SSL
from math import ceil
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from pathlib import PurePath
from string import punctuation
from threading import Thread, Timer
from time import perf_counter, sleep, time
from traceback import format_exc
from urllib.request import urlopen

import psutil
import pvporcupine
import requests
from geopy.distance import geodesic
from inflect import engine
from newsapi import NewsApiClient, newsapi_exception
from playsound import playsound
from pyaudio import PyAudio, paInt16

from api.controller import offline_compatible
from api.server import trigger_api
from executors import revive
from executors.alarm import alarm_executor, kill_alarm, set_alarm
from executors.automation import automation_handler
from executors.bluetooth import bluetooth
from executors.car import car
from executors.currenttime import current_time
from executors.custom_logger import logger
from executors.display_functions import brightness, decrease_brightness
from executors.face import face_detection
from executors.github import github
from executors.guard import guard_enable
from executors.internet import get_ssid, internet_checker, ip_info, speed_test
from executors.lights import lights
from executors.location import current_location, geo_locator, locate, location
from executors.meetings import (meeting_app_launcher, meeting_file_writer,
                                meeting_reader, meetings, meetings_gatherer)
from executors.others import (apps, facts, flip_a_coin, google_home, jokes,
                              meaning, music, notes, repeat)
from executors.remind import reminder, reminder_executor
from executors.robinhood import robinhood
from executors.sms import send_sms
from executors.system import hosted_device_info, system_info, system_vitals
from executors.tv import television
from executors.unconditional import alpha, google, google_maps, google_search
from executors.vpn_server import vpn_server
from executors.wiki import wikipedia_
from modules.audio.listener import listen
from modules.audio.speaker import audio_driver, speak
from modules.audio.voices import voice_changer, voice_default
from modules.audio.volume import switch_volumes, volume
from modules.conditions import conversation, keywords
from modules.database import database
from modules.personalcloud import pc_handler
from modules.temperature import temperature
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


def weather(phrase: str = None) -> None:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    Args:
        phrase: Takes the phrase as an optional argument.
    """
    if not env.weather_api:
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
                  f'hourly&appid={env.weather_api}'
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


def news(news_source: str = 'fox') -> None:
    """Says news around the user's location.

    Args:
        news_source: Source from where the news has to be fetched. Defaults to ``fox``.
    """
    if not env.news_api:
        support.no_env_vars()
        return

    sys.stdout.write(f'\rGetting news from {news_source} news.')
    news_client = NewsApiClient(api_key=env.news_api)
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


def gmail() -> None:
    """Reads unread emails from the gmail account for which the credentials are stored in env variables."""
    # todo: Update gmailconnector to yield instead of print and replace this function
    if not all([env.gmail_user, env.gmail_pass]):
        support.no_env_vars()
        return

    sys.stdout.write("\rFetching unread emails..")
    try:
        mail = IMAP4_SSL('imap.gmail.com')  # connects to imaplib
        mail.login(env.gmail_user, env.gmail_pass)
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
    except RuntimeError:
        if command and not response:
            with open('offline_request', 'w') as off_request:
                off_request.write(command)
        logger.fatal(f'Received a RuntimeError while executing offline request.\n{format_exc()}')
        revive.restart(quiet=True, quick=True)


def personal_cloud(phrase: str) -> None:
    """Enables or disables personal cloud.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    # todo: Get rid of this by making personal cloud a pypi package
    phrase = phrase.lower()
    if 'enable' in phrase or 'initiate' in phrase or 'kick off' in phrase or 'start' in phrase:
        Thread(target=pc_handler.enable,
               kwargs={"target_path": env.home, "username": env.gmail_user, "password": env.gmail_pass,
                       "phone_number": env.phone_number, "recipient": env.recipient}).start()
        speak(text="Personal Cloud has been triggered sir! I will send the login details to your phone number "
                   "once the server is up and running.")
    elif 'disable' in phrase or 'stop' in phrase:
        Thread(target=pc_handler.disable, args=[env.home]).start()
        speak(text=random.choice(conversation.acknowledgement))
    else:
        speak(text="I didn't quite get that sir! Please tell me if I should enable or disable your server.")
        Thread(target=support.unrecognized_dumper, args=[{'PERSONAL_CLOUD': phrase}])


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
        'phrase': env.offline_pass,
        'command': task
    }

    offline_endpoint = f"http://{env.offline_host}:{env.offline_port}/offline-communicator"
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


def initiate_background_threads() -> None:
    """Initiate background threads.

    Methods
        - stopper: Initiates stopper to restart after a set time using ``threading.Timer``
        - initiate_tunneling: Initiates ngrok tunnel to host Jarvis API through a public endpoint.
        - trigger_api: Initiates Jarvis API using uvicorn server in a thread.
        - automator: Initiates automator that executes certain functions at said time.
        - playsound: Plays a start-up sound.
    """
    Timer(interval=env.restart_interval, function=stopper).start()
    Thread(target=support.initiate_tunneling,
           kwargs={'offline_host': env.offline_host, 'offline_port': env.offline_port, 'home': env.home}).start()
    trigger_api()
    Thread(target=automator).start()
    playsound(sound='indicators/initialize.mp3', block=False)


def stopper() -> None:
    """Sets the key of ``STOPPER`` flag to True."""
    globals.STOPPER['status'] = True


if __name__ == '__main__':
    env = globals.ENV
    globals.hosted_device = hosted_device_info()
    if globals.hosted_device.get('os_name') != 'macOS':
        exit('Unsupported Operating System.\nWindows support was deprecated. '
             'Refer https://github.com/thevickypedia/Jarvis/commit/cf54b69363440d20e21ba406e4972eb058af98fc')

    logger.info('JARVIS::Starting Now')

    sys.stdout.write('\rVoice ID::Female: 1/17 Male: 0/7')  # Voice ID::reference
    limit = sys.getrecursionlimit()  # fetches current recursion limit
    sys.setrecursionlimit(limit * 10)  # increases the recursion limit by 10 times

    starter()  # initiates crucial functions which needs to be called during start up

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
    greet_check = {}

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
