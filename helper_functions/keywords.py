class Keywords:
    """list of keywords for each function which is condition matched in jarvis.py"""

    @staticmethod
    def date():
        return ['date']

    @staticmethod
    def time():
        return ['time']

    @staticmethod
    def weather():
        return ['weather', 'temperature']

    @staticmethod
    def system_info():
        return ['configuration']

    @staticmethod
    def ip_info():
        return ['address']

    @staticmethod
    def webpage():
        return ['website', 'webpage', 'web page', '.']

    @staticmethod
    def wikipedia():
        return ['wikipedia', 'info', 'information']

    @staticmethod
    def news():
        return ['news']

    @staticmethod
    def report():
        return ['report']

    @staticmethod
    def robinhood():
        return ['robinhood', 'investment', 'portfolio', 'summary']

    @staticmethod
    def apps():
        return ['launch']

    @staticmethod
    def repeat():
        return ['repeat', 'train']

    @staticmethod
    def chatbot():
        return ['chat', 'chatbot', 'chatter']

    @staticmethod
    def location():
        return ['location', 'where am i']

    @staticmethod
    def locate():
        return ['locate', 'where is my', "where's my"]

    @staticmethod
    def music():
        return ['music', 'songs', 'play']

    @staticmethod
    def gmail():
        return ['email', 'mail', 'emails', 'mails']

    @staticmethod
    def meaning():
        return ['meaning', 'meanings', 'dictionary', 'definition']

    @staticmethod
    def create_db():
        return ['create a new database', 'create a new data base', 'create a database', 'create a data base']

    @staticmethod
    def add_todo():
        return ['update my to do list', 'add tasks', 'add items to my to do list', 'new task', 'add new task',
                'add a new task']

    @staticmethod
    def delete_todo():
        return ['remove items', 'delete items', 'remove some items']

    @staticmethod
    def delete_db():
        return ['delete database', 'delete data base', 'delete my database', 'delete my data base']

    @staticmethod
    def list_todo():
        return ['plan']

    @staticmethod
    def distance():
        return ['far', 'distance', 'miles']

    @staticmethod
    def avoid():
        return ['sun', 'moon', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
                'a.m.', 'p.m.', 'update my to do list', 'launch', 'safari', 'body', 'human', 'centimeter']

    @staticmethod
    def geopy():
        return ['where is', "where's", 'which city', 'which state', 'which country', 'which county']

    @staticmethod
    def directions():
        return ['take me', 'get directions']

    @staticmethod
    def alarm():
        return ['alarm', 'wake me']

    @staticmethod
    def kill_alarm():
        return ['stop alarm', 'stop my alarm', 'turn off my alarm', 'turn my alarm off', 'stop another alarm']

    @staticmethod
    def reminder():
        return ['remind', 'reminder']

    @staticmethod
    def google_home():
        return ['google home', 'googlehome']

    @staticmethod
    def jokes():
        return ['joke', 'jokes', 'make me laugh']

    @staticmethod
    def notes():
        return ['notes', 'note']

    @staticmethod
    def github():
        return ['git', 'github', 'clone', 'GitHub']

    @staticmethod
    def txt_message():
        return ['message', 'text', 'messages']

    @staticmethod
    def google_search():
        return ['google search']

    @staticmethod
    def tv():
        return ['tv', 'television']

    @staticmethod
    def volume():
        return ['volume', 'mute']

    @staticmethod
    def face_detection():
        return ['face', 'recognize', 'who am i', 'detect', 'facial', 'recognition', 'detection']

    @staticmethod
    def speed_test():
        return ['speed', 'fast']

    @staticmethod
    def bluetooth():
        return ['connect', 'disconnect', 'bluetooth']

    @staticmethod
    def brightness():
        return ['brightness', 'bright', 'dim']

    @staticmethod
    def lights():
        return ['lights', 'hallway', 'kitchen', 'living room', 'bedroom']

    @staticmethod
    def guard_enable():
        return ['take care', 'heading out', 'keep an eye', 'turn on security mode', 'enable security mode']

    @staticmethod
    def guard_disable():
        return ["I'm back", 'I am back', 'turn off security mode', 'disable security mode']

    @staticmethod
    def flip_a_coin():
        return ['head', 'tail', 'flip']

    @staticmethod
    def facts():
        return ['fact', 'facts']

    @staticmethod
    def meetings():
        return ['meeting', 'appointment', 'schedule']

    @staticmethod
    def voice_changer():
        return ['voice', 'module', 'audio']

    @staticmethod
    def system_vitals():
        return ['vitals', 'statistics', 'readings', 'stats']

    @staticmethod
    def ok():
        return ['yeah', 'yes', 'yep', 'go ahead', 'proceed', 'continue', 'carry on', 'please', 'keep going']

    @staticmethod
    def restart():
        return ['restart', 'reboot']

    @staticmethod
    def exit():
        return ['exit', 'quit', 'no', 'nope', 'thanks', 'thank you', 'Xzibit', 'bye', 'good bye',
                'see you later', 'talk to you later', 'activate sentry mode', "that's it", 'that is it']

    @staticmethod
    def sleep():
        return ['exit', 'quit', 'lock', 'sleep', 'Xzibit', 'activate sentry mode']

    @staticmethod
    def kill():
        return ['kill', 'terminate yourself', 'stop running', 'stop']

    @staticmethod
    def shutdown():
        return ['shutdown', 'shut down', 'terminate']


if __name__ == '__main__':
    # TODO: begin diagnostics to use dictionaries instead of long nested if statements in conditions() in jarvis.py
    """Since Python stores the methods and other attributes of a class in a dictionary, which is unordered, 
    looping through and executing all of the functions in python is impossible.
    Since we don't care about order, we can use the class's __dict__ and iter through it's items"""
    funcs = 0
    for method_name, return_value in Keywords.__dict__.items():
        if type(return_value) == staticmethod:
            funcs += 1
    print(funcs)
    # prove time complexity
    from timeit import timeit

    print(f"Accessing the class directly for {funcs} times:")
    print(timeit(f"""
from helper_functions.keywords import Keywords
for _ in range({funcs}):
    Keywords.__dict__.items()"""))
    print(f"Assigning the class to a variable and then access it {funcs} times:")
    print(timeit(f"""
from helper_functions.keywords import Keywords
keywords = Keywords()
for _ in range({funcs}):
    keywords.__dict__.items()"""))
