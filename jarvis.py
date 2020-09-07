import logging
import webbrowser

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
    return None


def date():
    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%B %d, %Y")

    with sr.Microphone() as sourcew:
        speaker.say(f'Today is :{dt_string}, Is there anything else I can do for you?')
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
            renew()


def time():
    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%I:%M %p")

    with sr.Microphone() as sourcew:
        speaker.say(f'The current time is: {dt_string}, Is there anything else I can do for you?"')
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
            renew()


def webpage():
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

        speaker.say(f"I have opened {recognized_text1}, Is there anything else I can do for you?")
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
                speaker.say(f"I heard {recognized_text3} but I'm not configured to do it yet.")
                speaker.runAndWait()
            except sr.UnknownValueError as u3:
                logger.error(u3)
            except sr.RequestError as e3:
                logger.error(e3)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(' Jarvis')

    speaker = audio.init()
    recognizer = sr.Recognizer()

    volume = speaker.getProperty("volume")
    logger.info(f' Current volume is: {volume}')

    voices = speaker.getProperty("voices")
    speaker.setProperty("voice", voices[7].id)

    recognized_text = initialize()
    exit_msg = "Thank you for using Vicky's virtual assistant. Good bye."

    web_page_kw = ['website', '.com', '.in', 'webpage', 'web page', '.co.uk']

    if 'date' in recognized_text:
        date()

    elif 'time' in recognized_text:
        time()

    elif any(recognized_text) == any(web_page_kw):
        webpage()
