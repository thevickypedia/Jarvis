import os
import platform
import random
import re
import subprocess
import sys
import time
import webbrowser
from datetime import datetime

import pyttsx3 as audio
import speech_recognition as sr

from keywords import Keywords

now = datetime.now()
current = now.strftime("%p")
clock = now.strftime("%I")
today = now.strftime("%A")


# TODO: include face recognition
# TODO: include gmail reader


def initialize():
    if dummy.has_been_called:
        speaker.say("What can I do for you?")
        dummy.has_been_called = False
    elif current == 'AM' and int(clock) < 10:
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
            listener_new = recognizer.listen(source, timeout=3, phrase_time_limit=7)
            sys.stdout.write("\r")
            return recognizer.recognize_google(listener_new)
        except (sr.UnknownValueError, sr.RequestError):
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            dummy.has_been_called = True
        return initialize()


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
            converted2 = recognizer.recognize_google(listener2)
        except (sr.UnknownValueError, sr.RequestError):
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            renew()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            dummy.has_been_called = True
            renew()
        if any(re.search(line, converted2, flags=re.IGNORECASE) for line in keywords.exit()):
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
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again.")
                dummy.has_been_called = True
                renew()
            except sr.WaitTimeoutError:
                sys.stdout.write("\r")
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
    elif minutes == 1:
        return f'{minutes} minute {seconds} seconds'
    elif minutes:
        return f'{minutes} minutes {seconds} seconds'
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
        apps.has_been_called = False
        apps()

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

    elif any(re.search(line, converted, flags=re.IGNORECASE) for line in keywords.exit()):
        speaker.say(exit_msg)
        speaker.runAndWait()
        sys.stdout.write(f"Total runtime: {time_converter(time.perf_counter())}")
        exit()

    else:
        sys.stdout.write(f"\r{converted}")
        speaker.say(f"I heard {converted}. Let me look that up.")
        speaker.runAndWait()

        search = str(converted).replace(' ', '+')

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
            converted1 = recognizer.recognize_google(listener1)
        except (sr.UnknownValueError, sr.RequestError):
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            webpage()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            webpage()

    if 'exit' in converted1 or 'quit' in converted1:
        renew()

    url = f"https://{converted1}.com"

    webbrowser.open(url)
    speaker.say(f"I have opened {converted1}")
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
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            wiki_pedia()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
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
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            renew()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
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
    import re
    global operating_system

    if operating_system == 'Windows':
        if not apps.has_been_called:
            speaker.say("Which app shall I open? Please say the app name alone.")
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
                    speaker.say(f'I have opened {keyword}')
                    renew()
                else:
                    speaker.say(f"I wasn't able to find the app {keyword}. Try again. Please tell me an app name.")
                    apps()
            except (sr.UnknownValueError, sr.RequestError):
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again. Please tell me an app name.")
                apps()
            except sr.WaitTimeoutError:
                sys.stdout.write("\r")
                speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. "
                            "Or, please tell me an app name")
                apps()

    elif operating_system == 'Darwin':
        if not apps.has_been_called:
            speaker.say("Which app shall I open? Please say the app name alone.")
        speaker.runAndWait()
        apps.has_been_called = True
        with sr.Microphone() as source:
            try:
                sys.stdout.write("\rListener activated..")
                listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                sys.stdout.write("\r")
                keyword = recognizer.recognize_google(listener)
            except (sr.UnknownValueError, sr.RequestError):
                sys.stdout.write("\r")
                speaker.say("I didn't quite get that. Try again. Please tell me an app name.")
                apps()
            except sr.WaitTimeoutError:
                sys.stdout.write("\r")
                speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. "
                            "Or, Please tell me an app name.")
                apps()

        if 'exit' in keyword or 'quit' in keyword:
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
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            repeater()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
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
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            chatBot()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
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


def location():
    from urllib.request import urlopen
    import json
    url = 'http://ipinfo.io/json'
    resp = urlopen(url)
    data = json.load(resp)
    city, state, country = data['city'], data['region'], data['country']
    speaker.say(f"You're at {city} {state}, in {country}")
    speaker.runAndWait()
    renew()


def locate():
    import ssl
    import certifi
    from geopy.geocoders import Nominatim, options
    from pyicloud import PyiCloudService

    options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())

    u = os.getenv('icloud_user')
    p = os.getenv('icloud_pass')
    api = PyiCloudService(u, p)

    if dummy.has_been_called:
        speaker.say("Would you like to ring it?")
    else:
        raw_location = (api.iphone.location())
        raw_lat = raw_location['latitude']
        raw_long = raw_location['longitude']
        geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)
        locator = geo_locator.reverse(f'{raw_lat}, {raw_long}')
        current_location = locator.address
        speaker.say(f"Your iPhone is at {current_location}.")
        speaker.say("Would you like to ring it?")
    speaker.runAndWait()
    with sr.Microphone() as source:
        try:
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            phrase = recognizer.recognize_google(listener)
        except (sr.UnknownValueError, sr.RequestError):
            sys.stdout.write("\r")
            speaker.say("I didn't quite get that. Try again.")
            dummy.has_been_called = True
            locate()
        except sr.WaitTimeoutError:
            sys.stdout.write("\r")
            speaker.say("You're quite slower than I thought. Make quick responses, or go have a coffee. Or,")
            dummy.has_been_called = True
            locate()
        if 'yes' in phrase or 'please' in phrase:
            speaker.say("Ringing your iPhone now.")
            speaker.runAndWait()
            api.iphone.play_sound()
            speaker.say("I can also enable lost mode. Would you like to do it?")
            speaker.runAndWait()
            sys.stdout.write("\rListener activated..")
            listener = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            sys.stdout.write("\r")
            phrase = recognizer.recognize_google(listener)
            if 'yes' in phrase or 'please' in phrase:
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
    global path
    sys.stdout.write("\rScanning music files...")

    if operating_system == 'Darwin':
        path = os.walk("/Users")
    elif operating_system == 'Windows':
        user_profile = os.path.expanduser('~')
        path = os.walk(f"{user_profile}\\Music")

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
    sys.stdout.write(f"Total runtime: {time_converter(time.perf_counter())}")
    exit(0)


def dummy():
    return None


if __name__ == '__main__':
    speaker = audio.init()
    recognizer = sr.Recognizer()
    keywords = Keywords()
    operating_system = platform.system()

    report.has_been_called, dummy.has_been_called = False, False

    # noinspection PyTypeChecker
    volume = int(speaker.getProperty("volume")) * 100
    sys.stdout.write(f'\rCurrent volume is: {volume}% Voice ID::Female: 1/17 Male: 7')

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
        exit_msg = f"Thank you for using Vicky's virtual assistant. Have a nice day, and happy {today}."
    elif current == 'AM' and int(clock) >= 10:
        exit_msg = f"Thank you for using Vicky's virtual assistant. Enjoy your {today}."
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 4) and today in weekend:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice afternoon, and enjoy your weekend."
    elif current == 'PM' and (int(clock) == 12 or int(clock) < 4):
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice afternoon. Good bye."
    elif current == 'PM' and int(clock) < 7 and today in weekend:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice evening, and enjoy your weekend."
    elif current == 'PM' and int(clock) < 7:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice evening."
    elif today in weekend:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice night, and enjoy your weekend."
    else:
        exit_msg = "Thank you for using Vicky's virtual assistant. Have a nice night."

    conditions(initialize())
