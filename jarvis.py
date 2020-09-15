import logging
import os
import sys
from datetime import datetime

import pyttsx3 as audio
import speech_recognition as sr


def initialize():
    now = datetime.now()
    current = now.strftime("%p")
    clock = now.strftime("%I")
    speaker.say("Hi, I'm Jarvis. Vicky's virtual assistant. Whom am I speaking with?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        sys.stdout.write("Initialized: I'm listening...")
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=3)
        name = recognizer.recognize_google(listener)
        if str(os.getenv('key')) in str(name):
            if current == 'AM' and int(clock) <= 10:
                speaker.say("Welcome back sire. Good Morning. What can I do for you?")
                speaker.runAndWait()
            elif current == 'AM' and int(clock) > 10:
                speaker.say("Welcome back sire. Hope you're having a nice morning. What can I do for you?")
                speaker.runAndWait()
            elif current == 'PM' and (int(clock) == 12 or int(clock) < 4):
                speaker.say("Welcome back sire. Good Afternoon. What can I do for you?")
                speaker.runAndWait()
            elif current == 'PM' and int(clock) < 7:
                speaker.say("Welcome back sire. Good Evening. What can I do for you?")
                speaker.runAndWait()
            else:
                speaker.say("Welcome back sire. Hope you're having a nice night. What can I do for you?")
                speaker.runAndWait()
        else:
            if current == 'AM' and int(clock) <= 10:
                speaker.say(f"Hi {name}. Good Morning. What can I do for you?")
                speaker.runAndWait()
            elif current == 'AM' and int(clock) > 10:
                speaker.say(f"Hi {name}. Hope you're having a nice morning. What can I do for you?")
                speaker.runAndWait()
            elif current == 'PM' and (int(clock) == 12 or int(clock) < 4):
                speaker.say(f"Hi {name}. Good Afternoon. What can I do for you?")
                speaker.runAndWait()
            elif current == 'PM' and int(clock) < 7:
                speaker.say(f"Hi {name}. Good Evening. What can I do for you?")
                speaker.runAndWait()
            else:
                speaker.say(f"Hi {name}. Hope you're having a nice night. What can I do for you?")
                speaker.runAndWait()
    with sr.Microphone() as source_new:
        try:
            sys.stdout.write("\rName addressed: I'm listening...")
            listener_new = recognizer.listen(source_new, timeout=3, phrase_time_limit=5)
            return recognizer.recognize_google(listener_new)
        except sr.UnknownValueError as u:
            logger.error(u)
        except sr.RequestError as e:
            logger.error(e)


def renew():
    speaker.say("Is there anything else I can do for you?")
    speaker.runAndWait()
    with sr.Microphone() as sourcew:
        sys.stdout.write("\rRedo: I'm listening...")
        listener2 = recognizer.listen(sourcew, timeout=5, phrase_time_limit=5)
        recognized_text2 = recognizer.recognize_google(listener2)

        if 'no' in recognized_text2 or "that's all" in recognized_text2 or 'that is all' in recognized_text2 or \
                "that's it" in recognized_text2 or 'that is it' in recognized_text2:
            speaker.say(exit_msg)
            speaker.runAndWait()
            exit()
        else:
            speaker.say("Go ahead, I'm listening")
            speaker.runAndWait()

            sys.stdout.write("\rContinue: I'm listening...")
            listener_redo_ = recognizer.listen(sourcew, timeout=3, phrase_time_limit=5)
            recognized_redo_ = recognizer.recognize_google(listener_redo_)
            if 'date' in recognized_redo_:
                date()
            elif 'time' in recognized_redo_:
                time()
            elif 'weather' in recognized_redo_ or 'temperature' in recognized_redo_:
                weather()
            elif 'system' in recognized_redo_ or 'configuration' in recognized_redo_:
                system_info()
            elif 'website' in recognized_redo_ or '.com' in recognized_redo_ or '.in' in recognized_redo_ or \
                    'webpage' in recognized_redo_ or 'web page' in recognized_redo_ or '.co.uk' in recognized_redo_:
                webpage()
            elif 'fact' in recognized_redo_ or 'info' in recognized_redo_ or \
                    'information' in recognized_redo_ or 'wikipedia' in recognized_redo_ or 'facts' in \
                    recognized_redo_ or 'Wikipedia' in recognized_redo_:
                wikipedia()
            elif 'news' in recognized_redo_ or 'latest' in recognized_redo_:
                news()
            elif 'report' in recognized_redo_:
                report()
            elif 'investment' in recognized_redo_ or 'stock' in recognized_redo_ or 'share' in recognized_redo_ or \
                    'shares' in recognized_redo_ or 'portfolio' in recognized_redo_:
                robinhood()
            elif 'repeat' in recognized_redo_:
                repeater()
            elif 'open' in recognized_redo_ or 'apps' in recognized_redo_ or 'app' in recognized_redo_:
                apps()
            else:
                speaker.say(f"I heard {recognized_redo_}, but I'm not configured to respond to it yet.")
                speaker.runAndWait()
                renew()


def conditions():
    if 'date' in recognized_text:
        date()

    elif 'time' in recognized_text:
        time()

    elif 'weather' in recognized_text or 'temperature' in recognized_text:
        weather()

    elif 'system' in recognized_text or 'configuration' in recognized_text:
        system_info()

    elif 'website' in recognized_text or '.com' in recognized_text or '.in' in recognized_text or 'webpage' in \
            recognized_text or 'web page' in recognized_text or '.co.uk' in recognized_text:
        webpage()

    elif 'fact' in recognized_text or 'info' in recognized_text or 'information' in \
            recognized_text or 'wikipedia' in recognized_text or 'facts' in recognized_text or 'Wikipedia' in \
            recognized_text:
        wikipedia()

    elif 'news' in recognized_text or 'latest' in recognized_text:
        news()

    elif 'report' in recognized_text or 'good morning' in recognized_text or 'good' in recognized_text or 'morning' in \
            recognized_text:
        report()

    elif 'investment' in recognized_text or 'stock' in recognized_text or 'share' in recognized_text or 'shares' in \
            recognized_text or 'portfolio' in recognized_text:
        robinhood()

    elif 'open' in recognized_text or 'apps' in recognized_text or 'app' in recognized_text:
        apps()

    elif 'repeat' in recognized_text:
        repeater()

    else:
        speaker.say(f"I heard {recognized_text}, but I'm not configured to respond to it yet.")
        speaker.runAndWait()
        renew()


def report():
    sys.stdout.write("\rStarting today's report")
    report.has_been_called = True
    date()
    time()
    weather()
    news()
    renew()


def date():
    now = datetime.now()
    dt_string = now.strftime("%A, %B %d, %Y")

    speaker.say(f'Today is {dt_string}')
    speaker.runAndWait()
    if report.has_been_called:
        pass
    else:
        renew()


def time():
    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%I:%M %p")

    speaker.say(f'The current time is: {dt_string}')
    if report.has_been_called:
        pass
    else:
        renew()


def webpage():
    import webbrowser

    speaker.say("Which website shall I open? Just say the name of the webpage.")
    speaker.runAndWait()
    with sr.Microphone() as sourcew:
        sys.stdout.write("\rWebpage: I'm listening...")
        listener1 = recognizer.listen(sourcew, timeout=3, phrase_time_limit=5)
        recognized_text1 = recognizer.recognize_google(listener1)

        url = f"https://{recognized_text1}.com"

        chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
        webbrowser.get(chrome_path).open(url)

        speaker.say(f"I have opened {recognized_text1}")
    if report.has_been_called:
        pass
    else:
        renew()


def weather():
    sys.stdout.write('\rGetting your weather info')
    from urllib.request import urlopen
    import pytemperature
    import json
    api_key = os.getenv('api_key')

    url = 'http://ipinfo.io/json'
    resp = urlopen(url)
    data = json.load(resp)
    city, state, country, coordinates = data['city'], data['region'], data['country'], data['loc']
    lat = coordinates.split(',')[0]
    lon = coordinates.split(',')[1]
    api_endpoint = "http://api.openweathermap.org/data/2.5/"
    url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}'
    r = urlopen(url)  # sends request to the url created
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
    from psutil import virtual_memory
    import platform

    total, used, free = shutil.disk_usage("/")
    total = f"{(total // (2 ** 30))} GB"
    used = f"{(used // (2 ** 30))} GB"
    free = f"{(free // (2 ** 30))} GB"

    mem = virtual_memory()
    ram = f"{mem.total // (2 ** 30)} GB"

    cpu = str(os.cpu_count())
    release = str(platform.release())
    speaker.say(f"You're running {(platform.platform()).split('.')[0]}, with {cpu} cores. "
                f"The release version is {release}. Your physical drive capacity is {total}. "
                f"You have used up {used} of space. Your free space is {free}. Your RAM capacity is {ram}")
    speaker.runAndWait()
    renew()


def wikipedia():
    import wikipedia

    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
    with sr.Microphone() as sourcew:
        sys.stdout.write("\rWikipedia: I'm listening...")
        listener1 = recognizer.listen(sourcew, timeout=3, phrase_time_limit=5)
        keyword = recognizer.recognize_google(listener1)

        sys.stdout.write(f'\rGetting your info from Wikipedia API for {keyword}')
        try:
            data = wikipedia.summary(keyword)
        except wikipedia.exceptions.DisambiguationError as e:
            print(e)
            speaker.say('Your search has multiple results. Pick one displayed on your screen.')
            speaker.runAndWait()
            sys.stdout.write("\rMultiple Search: I'm listening...")
            listener1 = recognizer.listen(sourcew, timeout=3, phrase_time_limit=5)
            keyword1 = recognizer.recognize_google(listener1)
            data = wikipedia.summary(keyword1)

        speaker.say(''.join(data.split('.')[0:2]))
        speaker.runAndWait()
        speaker.say("Do you want me to continue?")
        speaker.runAndWait()
        sys.stdout.write("\rContinue Reading: I'm listening...")
        listener2 = recognizer.listen(sourcew, timeout=3, phrase_time_limit=5)
        response = recognizer.recognize_google(listener2)

        if 'yes' in response or 'continue' in response or 'proceed' in response or 'please' in response or 'yeah' in \
                response:
            speaker.say(''.join(data.split('.')[3:-1]))
            speaker.runAndWait()
            renew()
        else:
            renew()


def news():
    source = 'fox'
    sys.stdout.write(f'\rGetting news from {source} news.')
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


def apps():
    speaker.say("Which app shall I open? Please say the app name alone.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        sys.stdout.write("\rApps: I'm listening...")
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        keyword = recognizer.recognize_google(listener)
        os.system(f"open /Applications/{keyword}.app")
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
    from robinhood import watcher
    stock_value = watcher(rh, result)
    speaker.say(stock_value)
    speaker.runAndWait()
    renew()


def repeater():
    speaker.say("Please tell me what to repeat.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        sys.stdout.write("\rRepeater: I'm listening...")
        listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        keyword = recognizer.recognize_google(listener)
        speaker.say(f"I heard {keyword}")
        speaker.runAndWait()
    renew()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(' Jarvis')

    speaker = audio.init()
    recognizer = sr.Recognizer()
    report.has_been_called = False
    # noinspection PyTypeChecker
    volume = int(speaker.getProperty("volume")) * 100
    logger.info(f' Current volume is: {volume}% Voice ID::Friday: 17 Jarvis: 7')

    voices = speaker.getProperty("voices")
    # noinspection PyTypeChecker
    speaker.setProperty("voice", voices[7].id)

    recognized_text = initialize()
    exit_msg = "Thank you for using Vicky's virtual assistant. Good bye."

    conditions()
