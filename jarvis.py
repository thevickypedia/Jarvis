import logging
import os

import pyttsx3 as audio
import speech_recognition as sr


def initialize():
    speaker.say("Hi, I'm Jarvis. Vicky's virtual assistant. What can I do for you?")
    speaker.runAndWait()

    with sr.Microphone() as source:
        try:
            logger.info(" I'm listening...")
            listener = recognizer.listen(source)
            return recognizer.recognize_google(listener)
        except sr.UnknownValueError as u:
            logger.error(u)
        except sr.RequestError as e:
            logger.error(e)


def renew():
    with sr.Microphone() as sourcew:
        speaker.say("Is there anything else I can do for you?")
        speaker.runAndWait()
        try:
            logger.info(" I'm listening...")
            listener2 = recognizer.listen(sourcew)
            recognized_text2 = recognizer.recognize_google(listener2)
        except sr.UnknownValueError as u2:
            logger.error(u2)
        except sr.RequestError as e2:
            logger.error(e2)
        if 'no' in recognized_text2:
            speaker.say(exit_msg)
            speaker.runAndWait()
            exit()
        elif 'yes' in recognized_text2:
            speaker.say("Go ahead, I'm listening")
            speaker.runAndWait()
            try:
                logger.info(" I'm listening...")
                listener3 = recognizer.listen(sourcew)
                recognized_text3 = recognizer.recognize_google(listener3)
                speaker.say(f"I heard {recognized_text3}, but I'm not configured to respond to it yet.")
                speaker.runAndWait()
            except sr.UnknownValueError as u3:
                logger.error(u3)
            except sr.RequestError as e3:
                logger.error(e3)


def date():
    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%B %d, %Y")

    speaker.say(f'Today is :{dt_string}')
    speaker.runAndWait()
    renew()


def time():
    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%I:%M %p")

    speaker.say(f'The current time is: {dt_string}')
    renew()


def webpage():
    import webbrowser
    with sr.Microphone() as sourcew:
        speaker.say("Which website shall I open? Just say the name of the webpage.")
        speaker.runAndWait()
        try:
            logger.info(" I'm listening...")
            listener1 = recognizer.listen(sourcew)
            recognized_text1 = recognizer.recognize_google(listener1)
        except sr.UnknownValueError as u1:
            logger.error(u1)
        except sr.RequestError as e1:
            logger.error(e1)

        url = f"https://{recognized_text1}.com"

        chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
        webbrowser.get(chrome_path).open(url)

        speaker.say(f"I have opened {recognized_text1}")
    renew()


def weather():
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
    url = f'{api_endpoint}onecall?lat={lat}&lon={lon}&exclude=daily,minutely&appid={api_key}'
    r = urlopen(url)  # sends request to the url created
    response = json.loads(r.read())  # loads the response in a json

    weather_location = f'{city} {state}'
    temperature = response['current']['temp']
    condition = response['current']['weather'][0]['description']
    feels_like = response['current']['feels_like']
    temp_f = float(round(pytemperature.k2f(temperature), 2))
    temp_feel_f = float(round(pytemperature.k2f(feels_like), 2))
    output = f'Current weather at {weather_location} is {temp_f}°F. Feels Like {temp_feel_f}°F, and the current ' \
             f'condition is {condition} '
    speaker.say(output)
    speaker.runAndWait()
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(' Jarvis')

    speaker = audio.init()
    recognizer = sr.Recognizer()

    volume = speaker.getProperty("volume")
    logger.info(f' Current volume is: {volume}. Friday: 17. Jarvis: 7')

    voices = speaker.getProperty("voices")
    speaker.setProperty("voice", voices[7].id)

    recognized_text = initialize()
    exit_msg = "Thank you for using Vicky's virtual assistant. Good bye."

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
