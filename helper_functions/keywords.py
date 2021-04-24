class Keywords:
    """list of keywords for each function which is condition matched in jarvis.py"""
    @staticmethod
    def date():
        key = ['date']
        return key

    @staticmethod
    def time():
        key = ['time']
        return key

    @staticmethod
    def weather():
        key = ['weather', 'temperature']
        return key

    @staticmethod
    def system_info():
        key = ['configuration']
        return key

    @staticmethod
    def ip_info():
        key = ['address']
        return key

    @staticmethod
    def webpage():
        key = ['website', 'webpage', 'web page', '.']
        return key

    @staticmethod
    def wikipedia():
        key = ['wikipedia', 'info', 'information']
        return key

    @staticmethod
    def news():
        key = ['news']
        return key

    @staticmethod
    def report():
        key = ['report']
        return key

    @staticmethod
    def robinhood():
        key = ['robinhood', 'investment', 'portfolio', 'summary']
        return key

    @staticmethod
    def apps():
        key = ['launch']
        return key

    @staticmethod
    def repeat():
        key = ['repeat', 'train']
        return key

    @staticmethod
    def chatbot():
        key = ['chat', 'chatbot', 'chatter']
        return key

    @staticmethod
    def location():
        key = ['location', 'where am i']
        return key

    @staticmethod
    def locate():
        key = ['locate', 'where is my', "where's my"]
        return key

    @staticmethod
    def music():
        key = ['music', 'songs', 'play']
        return key

    @staticmethod
    def gmail():
        key = ['email', 'mail', 'emails', 'mails']
        return key

    @staticmethod
    def meaning():
        key = ['meaning', 'meanings', 'dictionary', 'definition']
        return key

    @staticmethod
    def create_db():
        key = ['create a new database', 'create a new data base', 'create a database', 'create a data base']
        return key

    @staticmethod
    def add_todo():
        key = ['update my to do list', 'add tasks', 'add items to my to do list', 'new task', 'add new task',
               'add a new task']
        return key

    @staticmethod
    def delete_todo():
        key = ['remove items', 'delete items', 'remove some items']
        return key

    @staticmethod
    def delete_db():
        key = ['delete database', 'delete data base', 'delete my database', 'delete my data base']
        return key

    @staticmethod
    def list_todo():
        key = ['plan']
        return key

    @staticmethod
    def distance():
        key = ['far', 'distance', 'miles']
        return key

    @staticmethod
    def avoid():
        key = ['sun', 'moon', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
               'a.m.', 'p.m.', 'update my to do list', 'launch', 'safari', 'body', 'human', 'centimeter']
        return key

    @staticmethod
    def geopy():
        key = ['where is', "where's", 'which city', 'which state', 'which country', 'which county']
        return key

    @staticmethod
    def directions():
        key = ['take me', 'get directions']
        return key

    @staticmethod
    def alarm():
        key = ['alarm', 'wake me']
        return key

    @staticmethod
    def kill_alarm():
        key = ['stop alarm', 'stop my alarm', 'turn off my alarm', 'turn my alarm off', 'stop another alarm']
        return key

    @staticmethod
    def reminder():
        key = ['remind', 'reminder']
        return key

    @staticmethod
    def google_home():
        key = ['google home', 'googlehome']
        return key

    @staticmethod
    def jokes():
        key = ['joke', 'jokes', 'make me laugh']
        return key

    @staticmethod
    def notes():
        key = ['notes', 'note']
        return key

    @staticmethod
    def github():
        key = ['git', 'github', 'clone', 'GitHub']
        return key

    @staticmethod
    def txt_message():
        key = ['message', 'text', 'messages']
        return key

    @staticmethod
    def google_search():
        key = ['google search']
        return key

    @staticmethod
    def tv():
        key = ['tv', 'television']
        return key

    @staticmethod
    def volume():
        key = ['volume', 'mute']
        return key

    @staticmethod
    def face_detection():
        key = ['face', 'recognize', 'who am i', 'detect', 'facial', 'recognition', 'detection']
        return key

    @staticmethod
    def speed_test():
        key = ['speed', 'fast']
        return key

    @staticmethod
    def bluetooth():
        key = ['connect', 'disconnect', 'bluetooth']
        return key

    @staticmethod
    def brightness():
        key = ['brightness', 'bright', 'dim']
        return key

    @staticmethod
    def lights():
        key = ['lights', 'hallway', 'kitchen', 'living room', 'bedroom']
        return key

    @staticmethod
    def guard_enable():
        key = ['take care', 'heading out', 'keep an eye', 'turn on security mode', 'enable security mode']
        return key

    @staticmethod
    def guard_disable():
        key = ["I'm back", 'I am back', 'turn off security mode', 'disable security mode']
        return key

    @staticmethod
    def flip_a_coin():
        key = ['head', 'tail', 'flip']
        return key

    @staticmethod
    def facts():
        key = ['fact', 'facts']
        return key

    @staticmethod
    def meetings():
        key = ['meeting', 'appointment', 'schedule']
        return key

    @staticmethod
    def voice_changer():
        key = ['voice', 'module', 'audio']
        return key

    @staticmethod
    def system_vitals():
        key = ['vitals', 'statistics', 'readings', 'stats']
        return key

    @staticmethod
    def ok():
        key = ['yeah', 'yes', 'yep', 'go ahead', 'proceed', 'continue', 'carry on', 'please', 'keep going']
        return key

    @staticmethod
    def restart():
        key = ['restart', 'reboot']
        return key

    @staticmethod
    def exit():
        key = ['exit', 'quit', 'no', 'nope', 'thanks', 'thank you', 'Xzibit', 'bye', 'good bye',
               'see you later', 'talk to you later', 'activate sentry mode', "that's it", 'that is it']
        return key

    @staticmethod
    def sleep():
        key = ['exit', 'quit', 'lock', 'sleep', 'Xzibit', 'activate sentry mode']
        return key

    @staticmethod
    def kill():
        key = ['kill', 'terminate yourself', 'stop running', 'stop']
        return key

    @staticmethod
    def shutdown():
        key = ['shutdown', 'shut down', 'terminate']
        return key


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
