import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    try:
        listener = r.listen(source)
        recognized_text = r.recognize_google(listener)
        print(recognized_text)
    except sr.UnknownValueError as u:
        print(u)
    except sr.RequestError as e:
        print(e)
