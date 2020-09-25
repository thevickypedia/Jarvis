import os
import platform
import sys
import time
import webbrowser
from datetime import datetime

import pyttsx3 as audio
import speech_recognition as sr

now = datetime.now()
current = now.strftime("%p")
clock = now.strftime("%I")
today = now.strftime("%A")


# TODO: include phone location
# TODO: include face recognition
# TODO: include gmail reader


def initialize():
    if current == 'AM' and int(clock) < 10:
        speaker.say("Welcome back sir. Good Morning. What can I do for you?")
    elif current == 'AM' and int(clock) >= 10:
        speaker.say("Welcome back sir. Hope you're having a nice morning. What can I do for you?")
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 4):
        speaker.say("Welcome back sir. Good Afternoon. What can I do for you?")
    elif current == 'PM' and int(clock) < 7:
        speaker.say("Welcome back sir. Good Evening. What can I do for you?")
    else:
        speaker.say("Welcome back sir. Hope you're having a nice night. What can I do for you?")
    speaker.runAndWait()

    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener_new = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            return recognizer.recognize_google(listener_new)
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            dummy.has_been_called = True
        renew()


def renew():
    if dummy.has_been_called:
        speaker.say("Is there anything I can do for you?. You may simply answer yes or no")
    else:
        speaker.say("Is there anything else I can do for you?")
    speaker.runAndWait()
    dummy.has_been_called = False
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener2 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            recognized_text2 = recognizer.recognize_google(listener2)
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            renew()
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            dummy.has_been_called = True
            renew()
        if 'no' in recognized_text2 or "that's all" in recognized_text2 or 'that is all' in recognized_text2 or \
                "that's it" in recognized_text2 or 'that is it' in recognized_text2 or 'quit' in recognized_text2 \
                or 'exit' in recognized_text2:
            speaker.say(exit_msg)
            speaker.runAndWait()
            sys.stdout.write(f"Total runtime: {time_converter(time.perf_counter())}")
            exit()
        else:
            speaker.say("Go ahead, I'm listening")
            speaker.runAndWait()
            try:
                sys.stdout.write("\rListener activated..")
                listener_redo_ = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
                recognized_redo_ = recognizer.recognize_google(listener_redo_)
                conditions(recognized_redo_)
            except (sr.UnknownValueError, sr.RequestError):
                speaker.say("I didn't quite get that. Try again.")
                dummy.has_been_called = True
                renew()
            except sr.WaitTimeoutError:
                speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
                dummy.has_been_called = True
                renew()


def time_converter(seconds):
    seconds = round(seconds % (24 * 3600))
    hour = round(seconds // 3600)
    seconds %= 3600
    minutes = round(seconds // 60)
    seconds %= 60
    if hour:
        return f'{hour} hours {minutes} minutes {seconds} seconds'
    elif minutes:
        return f'{minutes} minutes {seconds} seconds'
    elif seconds:
        return f'{seconds} seconds'


def conditions(recognized_text):
    if "today's date" in recognized_text or 'current date' in recognized_text:
        date()

    elif 'current time' in recognized_text:
        current_time()

    elif 'weather' in recognized_text or 'temperature' in recognized_text:
        weather()

    elif 'system' in recognized_text or 'configuration' in recognized_text:
        system_info()

    elif 'website' in recognized_text or '.com' in recognized_text or 'webpage' in \
            recognized_text or 'web page' in recognized_text:
        webpage()

    elif 'fact' in recognized_text or 'info' in recognized_text or 'information' in \
            recognized_text or 'wikipedia' in recognized_text or 'facts' in recognized_text or 'Wikipedia' in \
            recognized_text:
        wiki_pedia()

    elif 'news' in recognized_text or 'latest' in recognized_text:
        news()

    elif 'report' in recognized_text or 'good morning' in recognized_text:
        report()

    elif 'investment' in recognized_text or 'stock' in recognized_text or 'share' in recognized_text or 'shares' in \
            recognized_text or 'portfolio' in recognized_text:
        robinhood()

    elif 'launch' in recognized_text:
        apps.has_been_called = False
        apps()

    elif 'repeat' in recognized_text:
        repeater()

    elif 'chat' in recognized_text or 'bot' in recognized_text:
        chatBot()

    elif 'exit' in recognized_text or 'quit' in recognized_text:
        speaker.say(exit_msg)
        speaker.runAndWait()
        sys.stdout.write(f"Total runtime: {time_converter(time.perf_counter())}")
        exit()

    else:
        sys.stdout.write(f"\r{recognized_text}")
        speaker.say(f"I heard {recognized_text}. Let me look that up.")
        speaker.runAndWait()

        search = str(recognized_text).replace(' ', '+')

        url = f"https://www.google.com/search?q={search}"

        webbrowser.open(url)

        speaker.say("I have opened a google search for your request.")
        renew()


def report():
    sys.stdout.write("\rStarting today's report")
    report.has_been_called = True
    date()
    current_time()
    weather()
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
    from datetime import datetime
    c_time = datetime.now()
    dt_string = c_time.strftime("%I:%M %p")
    speaker.say(f'The current time is: {dt_string}')
    if report.has_been_called:
        pass
    else:
        renew()


def webpage():
    speaker.say("Which website shall I open? Just say the name of the webpage.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            recognized_text1 = recognizer.recognize_google(listener1)
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            webpage()
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            webpage()

    if 'exit' in recognized_text1 or 'quit' in recognized_text1:
        renew()

    url = f"https://{recognized_text1}.com"

    webbrowser.open(url)
    speaker.say(f"I have opened {recognized_text1}")
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


def wiki_pedia():
    import wikipedia
    speaker.say("Please tell the keyword.")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            keyword = recognizer.recognize_google(listener1)
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            wiki_pedia()
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            wiki_pedia()

        if 'exit' in keyword or 'quit' in keyword:
            renew()

        sys.stdout.write(f'\rGetting your info from Wikipedia API for {keyword}')
        try:
            data = wikipedia.summary(keyword)
        except wikipedia.exceptions.DisambiguationError as e:
            sys.stdout.write(e)
            speaker.say('Your search has multiple results. Pick one displayed on your screen.')
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..")
            listener1 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            keyword1 = recognizer.recognize_google(listener1)
            data = wikipedia.summary(keyword1)
        speaker.say(''.join(data.split('.')[0:2]))
        speaker.runAndWait()
        speaker.say("Do you want me to continue?")
        speaker.runAndWait()
        try:
            sys.stdout.write("\rListener activated..")
            listener2 = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            response = recognizer.recognize_google(listener2)
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            renew()
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            dummy.has_been_called = True
            renew()
        if 'yes' in response or 'continue' in response or 'proceed' in response or 'yeah' in response:
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
    import subprocess
    import re
    global operating_system

    if operating_system == 'Windows':
        if not apps.has_been_called:
            speaker.say("Opening third party apps on a Windows machine is complicated. Please tell me a system app "
                        "that I could try opening.")
            speaker.runAndWait()
        apps.has_been_called = True
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
                keyword = recognizer.recognize_google(listener)
                if 'exit' in keyword or 'quit' in keyword:
                    renew()
                status = os.system(f'start {keyword}')
                if status == 0:
                    speaker.say(f'I have opened {keyword} application')
                    renew()
                else:
                    speaker.say(f"I wasn't able to find the app {keyword}. Try again. Please tell me an app name.")
                    speaker.runAndWait()
                    apps()
            except (sr.UnknownValueError, sr.RequestError):
                speaker.say("I didn't quite get that. Try again. Please tell me an app name.")
                speaker.runAndWait()
                apps()
            except sr.WaitTimeoutError:
                speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. "
                            "Or, please tell me an app name")
                speaker.runAndWait()
                apps()

    elif operating_system == 'Darwin':
        if apps.has_been_called:
            speaker.say("Please repeat the app name alone.")
        else:
            speaker.say("Which app shall I open? Please say the app name alone.")
        speaker.runAndWait()
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
                keyword = recognizer.recognize_google(listener)
            except (sr.UnknownValueError, sr.RequestError):
                speaker.say("I didn't quite get that. Try again.")
                apps()
            except sr.WaitTimeoutError:
                speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
                apps()

        if 'exit' in keyword:
            renew()

        v = (subprocess.check_output("ls /Applications/", shell=True))
        apps_ = (v.decode('utf-8').split('\n'))

        for app in apps_:
            if re.search(keyword, app, flags=re.IGNORECASE) is not None:
                keyword = app

        app_status = os.system(f"open /Applications/'{keyword}'")
        apps.has_been_called = True
        if app_status == 256:
            speaker.say(f"I did not find the app {keyword}.")
            apps()
        else:
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
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=15)
            sys.stdout.write("\r")
            keyword = recognizer.recognize_google(listener)
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            repeater()
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            repeater()
        if 'exit' in keyword or 'quit' in keyword:
            renew()
        speaker.say(f"I heard {keyword}")
        speaker.runAndWait()
    renew()


def chatBot():
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
        except (sr.UnknownValueError, sr.RequestError):
            speaker.say("I didn't quite get that. Try again.")
            chatBot()
        except sr.WaitTimeoutError:
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            chatBot()
        if 'exit' in keyword or 'quit' in keyword:
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


def dummy():
    return None


if __name__ == '__main__':
    speaker = audio.init()
    recognizer = sr.Recognizer()
    report.has_been_called, dummy.has_been_called = False, False
    # noinspection PyTypeChecker
    volume = int(speaker.getProperty("volume")) * 100
    sys.stdout.write(f'\rCurrent volume is: {volume}% Voice ID::Female: 1/17 Male: 7')

    operating_system = platform.system()

    voices = speaker.getProperty("voices")

    if operating_system == 'Darwin':
        # noinspection PyTypeChecker
        speaker.setProperty("voice", voices[7].id)
    elif operating_system == 'Windows':
        # noinspection PyTypeChecker
        speaker.setProperty("voice", voices[1].id)
        speaker.setProperty('rate', 190)

    weekend = ['Friday', 'Saturday']
    if current == 'AM' and int(clock) < 10:
        exit_msg = f"Thank you for using Vicky's virtual assistant. Have a nice day, and happy {today}. Good bye."
    elif current == 'AM' and int(clock) >= 10:
        exit_msg = f"Thank you for using Vicky's virtual assistant. Enjoy your {today}. Good bye."
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 4) and today in weekend:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice afternoon, and enjoy your weekend. Good bye."
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 4):
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice afternoon. Good bye."
    elif current == 'PM' and int(clock) < 7 and today in weekend:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice evening, and enjoy your weekend. Good bye."
    elif current == 'PM' and int(clock) < 7:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice evening. Good bye."
    elif today in weekend:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice night, and enjoy your weekend. Good bye."
    else:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice night. Good bye."

    conditions(initialize())
