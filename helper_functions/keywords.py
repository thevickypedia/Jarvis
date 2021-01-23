class Keywords:
    """list of keywords for each function which is condition matched in jarvis.py"""
    def date(self):
        key = ['date']
        return key

    def time(self):
        key = ['time']
        return key

    def weather(self):
        key = ['weather', 'temperature']
        return key

    def system_info(self):
        key = ['system', 'configuration']
        return key

    def webpage(self):
        key = ['website', 'webpage', 'web page', '.']
        return key

    def wikipedia(self):
        key = ['wikipedia', 'info', 'information']
        return key

    def news(self):
        key = ['news']
        return key

    def report(self):
        key = ['report']
        return key

    def robinhood(self):
        key = ['robinhood', 'investment', 'portfolio', 'summary']
        return key

    def apps(self):
        key = ['launch']
        return key

    def repeat(self):
        key = ['repeat', 'train']
        return key

    def chatbot(self):
        key = ['chat', 'chatbot', 'chatter']
        return key

    def location(self):
        key = ['location', 'where am i']
        return key

    def locate(self):
        key = ['locate', 'where is my', "where's my"]
        return key

    def music(self):
        key = ['music', 'songs', 'play']
        return key

    def gmail(self):
        key = ['email', 'mail', 'emails', 'mails']
        return key

    def meaning(self):
        key = ['meaning', 'meanings', 'dictionary', 'definition']
        return key

    def create_db(self):
        key = ['create a new database', 'create a new data base', 'create a database', 'create a data base']
        return key

    def add_todo(self):
        key = ['update my to do list', 'add tasks', 'add items to my to do list', 'new task', 'add new task',
               'add a new task']
        return key

    def delete_todo(self):
        key = ['remove items', 'delete items', 'remove some items']
        return key

    def delete_db(self):
        key = ['delete database', 'delete data base', 'delete my database', 'delete my data base']
        return key

    def list_todo(self):
        key = ['plan']
        return key

    def distance(self):
        key = ['far', 'distance', 'miles']
        return key

    def avoid(self):
        key = ['sun', 'moon', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
               'a.m.', 'p.m.', 'update my to do list', 'launch', 'safari']
        return key

    def geopy(self):
        key = ['where is', "where's", 'which city', 'which state', 'which country', 'which county']
        return key

    def directions(self):
        key = ['take me', 'get directions']
        return key

    def alarm(self):
        key = ['alarm', 'wake me']
        return key

    def kill_alarm(self):
        key = ['stop alarm', 'stop my alarm', 'turn off my alarm', 'turn my alarm off', 'stop another alarm']
        return key

    def reminder(self):
        key = ['remind', 'reminder']
        return key

    def google_home(self):
        key = ['google home', 'googlehome']
        return key

    def jokes(self):
        key = ['joke', 'jokes', 'make me laugh']
        return key

    def notes(self):
        key = ['notes', 'note']
        return key

    def github(self):
        key = ['git', 'github', 'clone', 'GitHub']
        return key

    def txt_message(self):
        key = ['message', 'text', 'messages']
        return key

    def google_search(self):
        key = ['google search']
        return key

    def tv(self):
        key = ['tv', 'television']
        return key

    def volume(self):
        key = ['volume', 'mute']
        return key

    def face_detection(self):
        key = ['face', 'recognize', 'who am i', 'detect', 'facial', 'recognition', 'detection']
        return key

    def speed_test(self):
        key = ['speed', 'fast']
        return key

    def bluetooth(self):
        key = ['connect', 'disconnect', 'bluetooth']
        return key

    def brightness(self):
        key = ['brightness', 'bright', 'dim', 'screen']
        return key

    def lights(self):
        key = ['lights', 'hallway', 'kitchen', 'living room', 'bedroom']
        return key

    def guard_enable(self):
        key = ['take care', 'heading out', 'keep an eye', 'turn on security mode', 'enable security mode']
        return key

    def guard_disable(self):
        key = ["I'm back", 'I am back', 'turn off security mode', 'disable security mode']
        return key

    def ok(self):
        key = ['yeah', 'yes', 'yep', 'go ahead', 'proceed', 'continue', 'carry on', 'please', 'keep going']
        return key

    def restart(self):
        key = ['restart', 'reboot']
        return key

    def exit(self):
        key = ['exit', 'quit', 'sleep', 'no', 'nope', 'thanks', 'thank you', 'Xzibit', 'bye', 'good bye',
               'see you later', 'talk to you later', 'activate sentry mode', "that's it", 'that is it']
        return key

    def sleep(self):
        key = ['exit', 'quit', 'sleep', 'Xzibit', 'see you later', 'talk to you later', 'activate sentry mode']
        return key

    def kill(self):
        key = ['kill', 'terminate yourself', 'stop running', 'stop']
        return key

    def shutdown(self):
        key = ['shutdown', 'shut down', 'terminate']
        return key
    
    def screenshot(self):
        key = ['picture', 'screenshot']
        return key
    
    def headsortails(self):
        key = ['heads or tails']
        return key
    
    def facts(self):
        key = ['fact', 'facts']
        return key
    
    def quotes(self):
        key = ['saying', 'quote']
        return key


if __name__ == '__main__':
    # TODO: begin diagnostics to use dictionaries instead of long nested if statements in conditions() in jarvis.py
    """Since Python stores the methods and other attributes of a class in a dictionary, which is unordered, 
    looping through and executing all of the functions in python is impossible.
    Since we don't care about order, we can use the class's __dict__ and iter through it's items"""
    for _, method in Keywords.__dict__.items():
        if callable(method):
            print(method(None))
