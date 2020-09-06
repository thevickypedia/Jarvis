import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    listener = r.listen(source)
    recognized_text = r.recognize_google(listener)
    print(recognized_text)
