import pyttsx3 as audio
import speech_recognition as sr

speaker = audio.init()

volume = speaker.getProperty("volume")
print(f'Current volume is: {volume}')

voices = speaker.getProperty("voices")
speaker.setProperty("voice", voices[7].id)

speaker.say("Hi, I'm Jarvis. How are you doing?")
speaker.runAndWait()

r = sr.Recognizer()

with sr.Microphone() as source:
    try:
        print('Speak Now')
        listener = r.listen(source)
        recognized_text = r.recognize_google(listener)
        print(recognized_text)
    except sr.UnknownValueError as u:
        print(u)
    except sr.RequestError as e:
        print(e)

    speaker.say("How can I be of service to you?")
    speaker.runAndWait()
    try:
        print('Speak Now')
        listener = r.listen(source)
        recognized_text = r.recognize_google(listener)
        print(recognized_text)
    except sr.UnknownValueError as u:
        print(u)
    except sr.RequestError as e:
        print(e)
