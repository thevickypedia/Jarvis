import pyttsx3 as audio

speaker = audio.init()
voices = speaker.getProperty("voices")
speaker.setProperty("voice", voices[7].id)
volume = speaker.getProperty("volume")
print(f'Current volume is: {volume}')

speaker.say("Hi, I'm Jarvis. How can I be of service to you?")
speaker.runAndWait()
