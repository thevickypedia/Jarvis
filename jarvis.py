import logging

import pyttsx3 as audio
import speech_recognition as sr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(' Jarvis')

speaker = audio.init()

volume = speaker.getProperty("volume")
logger.info(f' Current volume is: {volume}')

voices = speaker.getProperty("voices")
speaker.setProperty("voice", voices[7].id)

speaker.say("Hi, I'm Jarvis. How are you doing?")
speaker.runAndWait()

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    try:
        logger.info(" I'm listening...")
        listener = recognizer.listen(source)
        recognized_text = recognizer.recognize_google(listener)
    except sr.UnknownValueError as u:
        logger.error(u)
    except sr.RequestError as e:
        logger.error(e)

    speaker.say(f"I heard {recognized_text}, How can I be of service to you?")
    speaker.runAndWait()
    try:
        logger.info(" I'm listening...")
        listener = recognizer.listen(source)
        recognized_text = recognizer.recognize_google(listener)
    except sr.UnknownValueError as u:
        logger.error(u)
    except sr.RequestError as e:
        logger.error(e)
