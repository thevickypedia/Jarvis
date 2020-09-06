import logging
import webbrowser

import pyttsx3 as audio
import speech_recognition as sr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(' Jarvis')

speaker = audio.init()

volume = speaker.getProperty("volume")
logger.info(f' Current volume is: {volume}')

voices = speaker.getProperty("voices")
speaker.setProperty("voice", voices[7].id)

speaker.say("Hi, I'm Jarvis. Vicky's virtual assistant. Currently I can only open websites for you.")
speaker.runAndWait()

recognizer = sr.Recognizer()


def main():
    with sr.Microphone() as source:
        speaker.say("Which website shall I open?")
        speaker.runAndWait()
        try:
            logger.info(" I'm listening...")
            listener = recognizer.listen(source)
            recognized_text = recognizer.recognize_google(listener)
        except sr.UnknownValueError as u:
            logger.error(u)
        except sr.RequestError as e:
            logger.error(e)

        url = f"https://{recognized_text}.com"

        chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
        webbrowser.get(chrome_path).open(url)

        speaker.say(f"I have opened {recognized_text}.com, Is there anything else I can do for you?")
        speaker.runAndWait()
        try:
            logger.info(" I'm listening...")
            listener = recognizer.listen(source)
            recognized_text = recognizer.recognize_google(listener)
        except sr.UnknownValueError as u:
            logger.error(u)
        except sr.RequestError as e:
            logger.error(e)
        if 'no' in recognized_text:
            speaker.say("Thank you for using Vicky's virtual assistant. Good bye.")
            speaker.runAndWait()
            exit()
        elif 'yes' in recognized_text:
            speaker.setProperty("voice", voices[10].id)
            speaker.say("Go ahead, I'm listening")
            speaker.runAndWait()


if __name__ == '__main__':
    main()
