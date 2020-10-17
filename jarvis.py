import json
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
from urllib.request import urlopen

import certifi
import pyttsx3 as audio
import speech_recognition as sr
from geopy.geocoders import Nominatim, options
from psutil import Process, virtual_memory

from alarm import Alarm
from helper_functions.conversation import Conversation
from helper_functions.database import Database, file_name
from helper_functions.keywords import Keywords

database = Database()
now = datetime.now()
current = now.strftime("%p")
clock = now.strftime("%I")
today = now.strftime("%A")


# TODO: include face recognition


def initialize():
    global place_holder, greet_check
    greet_check = 'initialized'
    if dummy.has_been_called:
        speaker.say("What can I do for you?")
        dummy.has_been_called = False
    elif current == 'AM' and int(clock) < 10:
        speaker.say("Good Morning. What can I do for you?")
    elif current == 'AM' and int(clock) >= 10:
        speaker.say("Hope you're having a nice morning. What can I do for you?")
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 3):
        speaker.say("Good Afternoon. What can I do for you?")
    elif current == 'PM' and int(clock) < 6:
        speaker.say("Good Evening. What can I do for you?")
    else:
        speaker.say("Hope you're having a nice night. What can I do for you?")
    speaker.runAndWait()

    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            received = recognizer.recognize_google(listener)
            place_holder = None
            return conditions(received)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            place_holder = 0
        return initialize()


def renew():
    global waiter
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            converted = recognizer.recognize_google(listener)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if waiter == 12:  # waits for a minute and goes to sleep
                listen()
            waiter += 1
            renew()
        if any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.exit()):
            speaker.say(f"Activating sentry mode sir.")
            speaker.say(exit_msg)
            speaker.runAndWait()
            listen()
        else:
            conditions(converted)


def time_converter(seconds):
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
    if any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.date()):
        date()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.time()):
        current_time()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.weather()):
        weather()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.system_info()):
        system_info()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.webpage()):
        webpage()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.wikipedia()):
        wiki_pedia()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.news()):
        news()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.report()):
        report()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.robinhood()):
        robinhood()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.apps()):
        apps(converted.split()[-1])

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.repeat()):
        repeater()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.chatbot()):
        chatBot()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.location()):
        location()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.locate()):
        locate()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.music()):
        music()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.gmail()):
        gmail()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.meaning()):
        meaning(converted.split()[-1])

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.delete_todo()):
        delete_todo()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.list_todo()):
        todo()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.add_todo()):
        add_todo()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.delete_db()):
        delete_db()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.create_db()):
        create_db()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.distance()):
        check = converted.split()
        places = []
        for word in check:
            if word[0].isupper() or '.' in word:
                try:
                    next_word = check[check.index(word) + 1]
                    if next_word[0].isupper():
                        places.append(f"{word + ' ' + check[check.index(word) + 1]}")
                    else:
                        if word not in ' '.join(places):
                            places.append(word)
                except IndexError:
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
        distance(start, end)

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.geopy()):
        place = ''
        for word in converted.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word:
                place += word + ' '
        if not place:
            keyword = 'is'
            before_keyword, keyword, after_keyword = converted.partition(keyword)
            place = after_keyword.replace(' in', '').strip()
        locate_places(place.strip())

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.directions()):
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

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.kill_alarm()):
        kill_alarm()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.alarm()):
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
            hour, minute = f"{hour:02}", f"{minute:02}"
            alarm(hour, minute, am_pm)
        except IndexError:
            alarm(hour=None, minute=None, am_pm=None)

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.google_home()):
        google_home()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.jokes()):
        jokes()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in conversation.greeting()):
        speaker.say('I am spectacular. I hope you are doing fine too.')
        dummy.has_been_called = True
        initialize()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in conversation.capabilities()):
        speaker.say('There is a lot I can do sir. For example: I can get you the weather at your location, news around '
                    'you, meanings of words, launch applications, play music, create a to-do list, check your emails, '
                    'get your system configuration, locate your phone, find distance between places, and much more. '
                    'Time to ask,.')
        dummy.has_been_called = True
        initialize()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in conversation.languages()):
        speaker.say("Tricky question!. I'm configured in python, and a little bit of bash. I can speak English.")
        dummy.has_been_called = True
        initialize()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in conversation.form()):
        speaker.say("I am a program, I'm without form.")
        dummy.has_been_called = True
        initialize()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in conversation.whats_up()):
        speaker.say("My listeners are up. There is nothing I cannot process. So, tell me..")
        dummy.has_been_called = True
        initialize()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in conversation.about_me()):
        speaker.say("I am a program, I'm without form.")
        speaker.say('There is a lot I can do. For example: I can get you the weather at your location, news around '
                    'you, meanings of words, launch applications, play music, create a to-do list, check your emails, '
                    'get your system configuration, locate your phone, find distance between places, and much more. '
                    'Time to ask,.')
        dummy.has_been_called = True
        initialize()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.exit()):
        speaker.say(f"Activating sentry mode sir.")
        speaker.say(exit_msg)
        speaker.runAndWait()
        listen()

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.kill()):
        memory_consumed = size_converter()
        speaker.say(f"Shutting down sir!")
        speaker.say(exit_msg)
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {memory_consumed}\nTotal runtime: {time_converter(time.perf_counter())}")
        exit(0)

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.shutdown()):
        shutdown()

    else:
        sys.stdout.write(f"\r{converted}")
        speaker.say(f"I heard {converted}. Let me look that up.")
        speaker.runAndWait()

        search = str(converted).replace(' ', '+')

        unknown_url = f"https://www.google.com/search?q={search}"

        webbrowser.open(unknown_url)

        speaker.say("I have opened a google search for your request.")
        renew()


def report():
    sys.stdout.write("\rStarting today's report")
    report.has_been_called = True
    date()
    current_time()
    weather()
    todo()
    gmail()
    news()
    report.has_been_called = False
    renew()


def date():
    today_date = datetime.now()
    dt_string = today_date.strftime("%A, %B %d, %Y")
    speaker.say(f'Today is {dt_string}')
    speaker.runAndWait()
    if report.has_been_called:
        pass
    else:
        renew()


def current_time():
    c_time = datetime.now()
    dt_string = c_time.strftime("%I:%M %p")
    speaker.say(f'The current time is: {dt_string}')
    if report.has_been_called:
        pass
    else:
        renew()


def webpage():
    global place_holder
    speaker.say("Which website shall I open? Just say the name of the webpage.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            converted1 = recognizer.recognize_google(listener1)
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            if place_holder == 0:
                place_holder = None
                renew()
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            place_holder = 0
            webpage()
        place_holder = None

    if 'exit' in converted1 or 'quit' in converted1 or 'Xzibit' in converted1:
        renew()

    web_url = f"https://{converted1}.com"
    webbrowser.open(web_url)
    speaker.say(f"I have opened {converted1}")
    renew()


def weather():
    sys.stdout.write('\rGetting your weather info')
    import pytemperature
    api_key = os.getenv('api_key')

    city, state, coordinates = location_info['city'], location_info['region'], location_info['loc']
    lat = coordinates.split(',')[0]
    lon = coordinates.split(',')[1]
    api_endpoint = "http://api.openweathermap.org/data/2.5/"
    weather_url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}'
    r = urlopen(weather_url)  # sends request to the url created
    response = json.loads(r.read())  # loads the response in a json

    weather_location = f'{city} {state}'
    temperature = response['current']['temp']
    condition = response['current']['weather'][0]['description']
    feels_like = response['current']['feels_like']
    maxi = response['daily'][0]['temp']['max']
    high = int(round(pytemperature.k2f(maxi), 2))
    mini = response['daily'][0]['temp']['min']
    low = int(round(pytemperature.k2f(mini), 2))
    temp_f = int(round(pytemperature.k2f(temperature), 2))
    temp_feel_f = int(round(pytemperature.k2f(feels_like), 2))
    sunrise = (datetime.fromtimestamp(response['daily'][0]['sunrise']).strftime("%I:%M %p"))
    sunset = (datetime.fromtimestamp(response['daily'][0]['sunset']).strftime("%I:%M %p"))
    output = f'You are currently at {weather_location}. The weather at your location is {temp_f}°F, with a high of ' \
             f'{high}, and a low of {low}. It currenly feels Like {temp_feel_f}°F, and the current ' \
             f'condition is {condition}. Sunrise at {sunrise}. Sunset at {sunset}'
    speaker.say(output)
    speaker.runAndWait()
    if report.has_been_called:
        pass
    else:
        renew()


def system_info():
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
    global place_holder
    import wikipedia
    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
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
        except wikipedia.exceptions.DisambiguationError as e:
            sys.stdout.write(f'\r{e}')
            speaker.say('Your keyword has multiple results sir. Please pick any one displayed on your screen.')
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..")
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            keyword1 = recognizer.recognize_google(listener1)
            summary = wikipedia.summary(keyword1)
        speaker.say(''.join(summary.split('.')[0:2]))
        speaker.runAndWait()
        speaker.say("Do you want me to continue?")
        speaker.runAndWait()
        try:
            sys.stdout.write("\rListener activated..")
            listener2 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
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
    source = 'fox'
    sys.stdout.write(f'\rGetting news from {source} news.')
    speaker.say("News around you!")
    from newsapi import NewsApiClient
    newsapi = NewsApiClient(api_key=os.getenv('news_api'))
    all_articles = newsapi.get_top_headlines(sources=f'{source}-news')

    for article in all_articles['articles']:
        speaker.say(article['title'])
        speaker.runAndWait()

    if report.has_been_called:
        pass
    else:
        renew()


def apps(keyword):
    global place_holder
    ignore = ['app', 'application']
    if (keyword in ignore or keyword is None) and operating_system == 'Windows':
        speaker.say("Please say the app name.")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
    sys.stdout.write('\rGetting your investment details.')
    from pyrh import Robinhood
    u = os.getenv('user')
    p = os.getenv('pass')
    q = os.getenv('qr')
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
    global place_holder
    speaker.say("Please tell me what to repeat.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            sys.stdout.write("\r")
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
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            sys.stdout.write("\r")
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
    city, state, country = location_info['city'], location_info['region'], location_info['country']
    speaker.say(f"You're at {city} {state}, in {country}")
    speaker.runAndWait()
    renew()


def locate():
    global place_holder
    from pyicloud import PyiCloudService

    u = os.getenv('icloud_user')
    p = os.getenv('icloud_pass')
    api = PyiCloudService(u, p)

    if dummy.has_been_called:
        speaker.say("Would you like to ring it?")
    else:
        stat = api.iphone.status()
        bat_percent = round(stat['batteryLevel'] * 100)
        device_model = stat['deviceDisplayName']
        phone_name = stat['name']
        raw_location = (api.iphone.location())
        raw_lat = raw_location['latitude']
        raw_long = raw_location['longitude']
        locator = geo_locator.reverse(f'{raw_lat}, {raw_long}')
        current_location = locator.address
        speaker.say(f"Your iPhone is at {current_location}.")
        speaker.say(f"Some more details. Battery: {bat_percent}%, Name: {phone_name}, Model: {device_model}")
        speaker.say("Would you like to ring it?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
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
            api.iphone.play_sound()
            speaker.say("I can also enable lost mode. Would you like to do it?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            phrase = recognizer.recognize_google(listener)
            if any(re.search(line, phrase, flags=re.IGNORECASE) for line in keywords.ok()):
                recovery = os.getenv('recovery')
                message = 'Return my phone immediately.'
                api.iphone.lost_device(recovery, message)
                speaker.say("I've enabled lost mode on your phone.")
                speaker.runAndWait()
            else:
                renew()
        else:
            renew()


def music():
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

    if operating_system == 'Darwin':
        subprocess.call(["open", chosen])
    elif operating_system == 'Windows':
        os.system(f'start wmplayer "{chosen}"')

    sys.stdout.write('\r')
    speaker.say("Enjoy your music sir!")
    speaker.runAndWait()
    listen()


def gmail():
    global place_holder
    sys.stdout.write("\rFetching new emails..")
    import email
    import imaplib
    from email.header import decode_header, make_header

    u = os.getenv('gmail_user')
    p = os.getenv('gmail_pass')

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(u, p)
    mail.list()
    mail.select('inbox')

    n = 0
    return_code, messages = mail.search(None, 'UNSEEN')
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
        speaker.say(f'You have {n} unread emails sir. Do you want me to check it?')
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                response = recognizer.recognize_google(listener)
                sys.stdout.write("\r")
                if any(re.search(line, response, flags=re.IGNORECASE) for line in keywords.ok()):
                    for nm in messages[0].split():
                        ignore, mail_data = mail.fetch(nm, '(RFC822)')
                        for response_part in mail_data:
                            if isinstance(response_part, tuple):
                                original_email = email.message_from_bytes(response_part[1])
                                raw_receive = (original_email['Received'].split(';')[-1]).strip()
                                datetime_obj = datetime.strptime(raw_receive, "%a, %d %b %Y %H:%M:%S -0700 (PDT)") \
                                               + timedelta(hours=2)
                                received_date = datetime_obj.strftime("%Y-%m-%d")
                                current_date = datetime.today().date()
                                yesterday = current_date - timedelta(days=1)
                                if received_date == str(current_date):
                                    receive = (datetime_obj.strftime("today, at %I:%M %p"))
                                elif received_date == str(yesterday):
                                    receive = (datetime_obj.strftime("yesterday, at %I:%M %p"))
                                else:
                                    receive = (datetime_obj.strftime("on %A, %B %d, at %I:%M %p"))
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
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                response = recognizer.recognize_google(listener)
                sys.stdout.write("\r")
                if 'no' in response.lower().split() or 'nope' in response.lower().split() or 'thank you' in \
                        response.lower().split() or "that's it" in response.lower().split():
                    renew()
                definition = dictionary.meaning(response)
                if definition:
                    for key in definition.keys():
                        speaker.say(f'{response}: {key, "".join(definition[key])}')
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
            for key in definition.keys():
                speaker.say(f'{keyword}: {key, "".join(definition[key])}')
    renew()


def create_db():
    speaker.say(database.create_db())
    if todo.has_been_called:
        todo.has_been_called = False
        todo()
    elif add_todo.has_been_called:
        add_todo.has_been_called = False
        add_todo()
    renew()


def todo():
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name) and report.has_been_called:
        speaker.say("You don't have a database created for your to-do list sir.")
    elif not os.path.isfile(file_name):
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                sys.stdout.write("\r")
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
            if category not in result:
                result.update({category: item})
            else:
                result[category] = result[category] + ', ' + item
        sys.stdout.write("\r")
        if result:
            for category, item in result.items():
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
    global place_holder
    sys.stdout.write("\rLooking for to-do database..")
    if not os.path.isfile(file_name):
        sys.stdout.write("\r")
        speaker.say("You don't have a database created for your to-do list sir.")
        speaker.say("Would you like to spin up one now?")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                sys.stdout.write("\r")
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
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            item = recognizer.recognize_google(listener)
            if 'exit' in item or 'quit' in item or 'Xzibit' in item:
                speaker.say('Your to-do list has been left intact sir.')
                renew()
            sys.stdout.write(f"Item: {item}")
            speaker.say(f"I heard {item}. Which category you want me to add it to?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..")
            listener_ = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r")
            category = recognizer.recognize_google(listener_)
            if 'exit' in category or 'quit' in category or 'Xzibit' in category:
                speaker.say('Your to-do list has been left intact sir.')
                renew()
            sys.stdout.write(f"Category: {category}")
            response = database.uploader(category, item)
            speaker.say(response)
            speaker.say("Do you want to add anything else to your to-do list?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..")
            listener_continue = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r")
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
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r")
            item = recognizer.recognize_google(listener)
            if any(re.search(line, item, flags=re.IGNORECASE) for line in keywords.exit()):
                renew()
            response = database.deleter(item)
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
    global place_holder
    if os.path.isfile(file_name):
        speaker.say('Are you sure you want to delete your database?')
        speaker.runAndWait()
    else:
        speaker.say(f'I did not find any database sir.')
        renew()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            sys.stdout.write("\r")
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
    global place_holder
    if not destination:
        speaker.say("Destination please?")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
    from haversine import haversine, Unit

    if starting_point:
        desired_start = geo_locator.geocode(starting_point)
        sys.stdout.write(f"{desired_start.address} **")
        start = desired_start.latitude, desired_start.longitude
        start_check = None
    else:
        start = tuple(map(float, location_info['loc'].split(',')))
        start_check = 'My Location'
    sys.stdout.write("::TO::")
    desired_location = geo_locator.geocode(destination)
    sys.stdout.write(f"** {desired_location.address}")
    end = desired_location.latitude, desired_location.longitude
    miles = round(haversine(start, end, unit=Unit.MILES))
    if directions.has_been_called:
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
        if not locate_places.has_been_called:
            speaker.say(f"You may also ask where is {destination}")
    else:
        speaker.say(f"{starting_point} is {miles} miles away from {destination}.")
    renew()


def locate_places(place):
    global place_holder
    if not place:
        speaker.say("Tell me the name of a place!")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
        desired_start = geo_locator.geocode(place)
        coordinates = desired_start.latitude, desired_start.longitude
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
            speaker.say(f"{place} is in {state} in {country}")
        elif place in state:
            speaker.say(f"{place} is a state in {country}")
        elif (city or county) and state and country:
            speaker.say(f"{place} is in {city or county}, {state}" if country == 'United States of America'
                        else f"{place} is in {city or county}, {state}, in {country}")
        locate_places.has_been_called = True
    except:
        speaker.say(f"{place} is not a real place on Earth sir! Try again.")
        locate_places(place=None)
    distance(starting_point=None, destination=place)


def directions(place):
    global place_holder
    if not place:
        speaker.say("You might want to give a location.")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
    desired_start = geo_locator.geocode(place)
    coordinates = desired_start.latitude, desired_start.longitude
    located = geo_locator.reverse(coordinates, language='en')
    data = located.raw
    address = data['address']
    start_country = address['country_code'] if 'country_code' in address else None
    end = f"{located.latitude},{located.longitude}"
    end_country = location_info['country']
    start = location_info['loc']
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
    global place_holder, alarm_state
    if hour and minute and am_pm:
        appender = [hour, minute, am_pm]
        alarm_state.append(appender)
        f_name = f"{hour}_{minute}_{am_pm}"
        open(f'lock_files/{f_name}.lock', 'a')
        Alarm(hour, minute, am_pm).start() if am_pm == 'PM' else Alarm(hour, minute, am_pm).start()
    else:
        speaker.say('Please tell me a time sir!')
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
    speaker.say(f"Alarm has been set for {hour}:{minute} {am_pm} sir!")
    sys.stdout.write(f"Alarm has been set for {hour}:{minute} {am_pm} sir!")
    renew()


def kill_alarm():
    global alarm_state, place_holder
    if not alarm_state:
        speaker.say("You have no alarms set sir!")
    elif len(alarm_state) == 1:
        hour, minute, am_pm = alarm_state[0][0], alarm_state[0][1], alarm_state[0][-1]
        try:
            os.remove(f"lock_files/{hour}_{minute}_{am_pm}.lock")
        except FileNotFoundError:
            pass
        speaker.say(f"Your alarm at {hour}:{minute} {am_pm} has been silenced sir!")
    else:
        files = os.listdir('lock_files')
        if operating_system == 'Darwin':
            files.remove('.DS_Store')
        sys.stdout.write(f"{', '.join(files).replace('.lock', '')}")
        speaker.say("Please let me know which alarm you want to remove. Current alarms on your screen sir!")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("    Listener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
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
                    os.remove(f"lock_files/{hour}_{minute}_{am_pm}.lock")
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
                kill_alarm()
                place_holder = 0
            except FileNotFoundError as file_error:
                sys.stdout.write(f"{file_error}")
                speaker.say(f"Unable to find a lock file for {hour} {minute} {am_pm} sir! Try again!")
                kill_alarm()
    renew()


def google_home():
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
    sys.stdout.write('\r')
    number = 0
    for device, ip in devices.items():
        number += 1
        sys.stdout.write(f"{device},  ")
    speaker.say(f"You have {number} devices in your IP range. Devices list on your screen sir!")
    speaker.runAndWait()
    renew()


def jokes():
    global place_holder
    from joke.jokes import geek, icanhazdad, chucknorris, icndb
    speaker.say(random.choice([geek, icanhazdad, chucknorris, icndb])())
    speaker.runAndWait()
    speaker.say("Do you want to hear another one sir?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            converted = recognizer.recognize_google(listener)
            place_holder = None
            if any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.ok()):
                jokes()
            else:
                renew()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            renew()


def listen():
    global waiter
    waiter = 0
    if greet_check == 'initialized':
        dummy.has_been_called = True
    try:
        sys.stdout.write("\rSentry Mode")
        listener = recognizer.listen(source_for_sentry_mode, timeout=5, phrase_time_limit=5)
        sys.stdout.write("\r")
        key = recognizer.recognize_google(listener)
        if 'look alive' in key in key or 'wake up' in key or 'wakeup' in key or 'show time' in key or 'Showtime' in key:
            speaker.say(f'{random.choice(wake_up1)}')
            initialize()
        elif 'you there' in key or 'buddy' in key or 'are you there' in key or 'time to work' in key:
            speaker.say(f'{random.choice(wake_up2)}')
            initialize()
        elif 'Jarvis' in key or 'jarvis' in key:
            speaker.say(f'{random.choice(wake_up3)}')
            initialize()
        else:
            listen()
    except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
        listen()
    except KeyboardInterrupt:
        memory_consumed = size_converter()
        speaker.say(f"Shutting down sir!")
        speaker.say(exit_msg)
        speaker.runAndWait()
        sys.stdout.write(f"\rMemory consumed: {memory_consumed}\nTotal runtime: {time_converter(time.perf_counter())}")
        exit(0)


def size_converter():
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
    global place_holder
    speaker.say("Are you sure you want to turn off the machine sir?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("Listener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            converted = recognizer.recognize_google(listener)
            place_holder = None
            if any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.ok()):
                memory_consumed = size_converter()
                speaker.say(f"Shutting down sir!")
                speaker.say(exit_msg)
                speaker.runAndWait()
                sys.stdout.write(
                    f"\rMemory consumed: {memory_consumed}\nTotal runtime: {time_converter(time.perf_counter())}")
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
    return None


if __name__ == '__main__':
    speaker = audio.init()
    recognizer = sr.Recognizer()
    keywords = Keywords()
    conversation = Conversation()
    operating_system = platform.system()
    place_holder, greet_check, alarm_state = None, None, []
    waiter = 0

    options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())
    geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)
    url = 'http://ipinfo.io/json'
    resp = urlopen(url)
    location_info = json.load(resp)

    wake_up1 = ['Up and running sir.']
    wake_up2 = ['For you sir!, Always!', 'At your service sir.']
    wake_up3 = ["I'm here sir!."]

    report.has_been_called, locate_places.has_been_called, directions.has_been_called = False, False, False
    for functions in [dummy, delete_todo, todo, add_todo]:
        functions.has_been_called = False

    # noinspection PyTypeChecker
    volume = int(speaker.getProperty("volume")) * 100
    sys.stdout.write(f'\rCurrent volume is: {volume}% Voice ID::Female: 1/17 Male: 0/7')

    voices = speaker.getProperty("voices")

    if operating_system == 'Darwin':
        # noinspection PyTypeChecker,PyUnresolvedReferences
        speaker.setProperty("voice", voices[7].id)
    elif operating_system == 'Windows':
        # noinspection PyTypeChecker,PyUnresolvedReferences
        speaker.setProperty("voice", voices[0].id)
        speaker.setProperty('rate', 190)
    else:
        operating_system = None
        exit(0)

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

    with sr.Microphone() as source_for_sentry_mode:
        recognizer.adjust_for_ambient_noise(source_for_sentry_mode)
        listen()
