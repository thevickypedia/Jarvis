import logging
import os
from datetime import datetime

import pyttsx3 as audio
import speech_recognition as sr


def initialize():
    now = datetime.now()
    current = now.strftime("%p")
    clock = now.strftime("%I")
    speaker.say("Hi, I'm Jarvis. Vicky's virtual assistant. Whom am I speaking with?")
    speaker.runAndWait()
    logger.info(" Initialized: I'm listening...")
    with sr.Microphone() as source:
        listener = recognizer.listen(source)
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
            logger.info(" Name addressed: I'm listening...")
            listener_new = recognizer.listen(source_new)
            return recognizer.recognize_google(listener_new)
        except sr.UnknownValueError as u:
            logger.error(u)
        except sr.RequestError as e:
            logger.error(e)


def renew():
    with sr.Microphone() as sourcew:
        speaker.say("Is there anything else I can do for you?")
        speaker.runAndWait()

        logger.info(" Redo: I'm listening...")
        listener2 = recognizer.listen(sourcew)
        recognized_text2 = recognizer.recognize_google(listener2)

        if 'no' in recognized_text2 or "that's all" in recognized_text2 or 'that is all' in recognized_text2 or \
                "that's it" in recognized_text2 or 'that is it' in recognized_text2:
            speaker.say(exit_msg)
            speaker.runAndWait()
            exit()
        elif 'yes' in recognized_text2 or 's' in recognized_text2 or 'Yes' in recognized_text2 or 'yes' \
                in recognized_text2:
            speaker.say("Go ahead, I'm listening")
            speaker.runAndWait()

            logger.info(" Continue: I'm listening...")
            listener_redo_ = recognizer.listen(sourcew)
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
            else:
                speaker.say(f"I heard {recognized_redo_}, but I'm not configured to respond to it yet.")
                speaker.runAndWait()


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

    else:
        speaker.say(f"I heard {recognized_text}, but I'm not configured to respond to it yet.")
        speaker.runAndWait()


def report():
    logger.info(" Starting today's report")
    report.has_been_called = True
    date()
    time()
    weather()
    news()
    renew()


def date():
    now = datetime.now()
    dt_string = now.strftime("%A, %B %d, %Y")

    speaker.say(f'Today is :{dt_string}')
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
    with sr.Microphone() as sourcew:
        speaker.say("Which website shall I open? Just say the name of the webpage.")
        speaker.runAndWait()

        logger.info(" Webpage: I'm listening...")
        listener1 = recognizer.listen(sourcew)
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
    logger.info(' Getting your weather info')
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
    maxi = (response['daily'][0]['temp']['max'])
    high = float(round(pytemperature.k2f(maxi), 2))
    mini = (response['daily'][0]['temp']['min'])
    low = float(round(pytemperature.k2f(mini), 2))
    temp_f = float(round(pytemperature.k2f(temperature), 2))
    temp_feel_f = float(round(pytemperature.k2f(feels_like), 2))
    sunrise = (datetime.fromtimestamp(response['daily'][0]['sunrise']).strftime("%I:%M %p"))
    sunset = (datetime.fromtimestamp(response['daily'][0]['sunset']).strftime("%I:%M %p"))
    output = f'Current weather at {weather_location} is {temp_f}°F, with a high of {high}°F, and a low of {low}°F. ' \
             f'It currenly feels Like {temp_feel_f}°F, and the current ' \
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
        logger.info(" Wikipedia: I'm listening...")
        listener1 = recognizer.listen(sourcew)
        keyword = recognizer.recognize_google(listener1)

        logger.info(f' Getting your info from Wikipedia API for {keyword}')
        try:
            data = wikipedia.summary(keyword)
        except wikipedia.exceptions.DisambiguationError as e:
            print(e)
            speaker.say('Your search has multiple results. Pick one displayed on your screen.')
            speaker.runAndWait()
            logger.info(" Multiple Search: I'm listening...")
            listener1 = recognizer.listen(sourcew)
            keyword1 = recognizer.recognize_google(listener1)
            data = wikipedia.summary(keyword1)

        speaker.say(''.join(data.split('.')[0:2]))
        speaker.runAndWait()
        speaker.say("Do you want me to continue?")
        speaker.runAndWait()
        logger.info(" Continue Reading: I'm listening...")
        listener2 = recognizer.listen(sourcew)
        response = recognizer.recognize_google(listener2)

        if 'yes' in response or 'continue' in response or 'proceed' in response or 'please' in response or 'yeah' in \
                response:
            speaker.say(''.join(data.split('.')[3:-1]))
            speaker.runAndWait()
            renew()
        else:
            renew()


def news():
    logger.info(' Getting news from fox news.')
    from newsapi import NewsApiClient
    newsapi = NewsApiClient(api_key=os.getenv('news_api'))
    all_articles = newsapi.get_top_headlines(sources='fox-news')

    for article in all_articles['articles']:
        speaker.say(article['title'])
        speaker.runAndWait()

    if report.has_been_called:
        pass
    else:
        renew()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(' Jarvis')

    speaker = audio.init()
    recognizer = sr.Recognizer()
    report.has_been_called = False
    volume = speaker.getProperty("volume")
    logger.info(f' Current volume is: {volume}. Friday: 17. Jarvis: 7')

    voices = speaker.getProperty("voices")
    speaker.setProperty("voice", voices[7].id)

    recognized_text = initialize()
    exit_msg = "Thank you for using Vicky's virtual assistant. Good bye."

    conditions()
