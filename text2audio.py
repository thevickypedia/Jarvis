import pyttsx3 as audio

speaker = audio.init()

speaker.say("Hi, I'm Jarvis. How can I be of service to you?")
speaker.runAndWait()
