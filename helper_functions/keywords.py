class Keywords:
    """List of keywords for each variable which is condition matched in the main module.

    >>> Keywords

    """

    date = ['date']

    time = ['time']

    weather = ['weather', 'temperature']

    system_info = ['configuration']

    ip_info = ['address']

    webpage = ['website', 'webpage', 'web page', '.']

    wikipedia = ['wikipedia', 'info', 'information']

    news = ['news']

    report = ['report']

    robinhood = ['robinhood', 'investment', 'portfolio', 'summary']

    apps = ['launch']

    repeat = ['repeat', 'train']

    chatbot = ['chat', 'chatbot', 'chatter']

    location = ['location', 'where am i']

    locate = ['locate', 'where is my', "where's my"]

    music = ['music', 'songs', 'play']

    gmail = ['email', 'mail', 'emails', 'mails']

    meaning = ['meaning', 'meanings', 'dictionary', 'definition']

    create_db = ['create a new database', 'create a new data base', 'create a database', 'create a data base']

    add_todo = ['add', 'update']

    delete_todo = ['remove', 'delete']

    delete_db = ['delete database', 'delete data base', 'delete my database', 'delete my data base']

    list_todo = ['plan']

    distance = ['far', 'distance', 'miles']

    avoid = ['sun', 'moon', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
             'a.m.', 'p.m.', 'update my to do list', 'launch', 'safari', 'body', 'human', 'centimeter', 'server',
             'cloud']

    geopy = ['where is', "where's", 'which city', 'which state', 'which country', 'which county']

    directions = ['take me', 'get directions']

    alarm = ['alarm', 'wake me']

    kill_alarm = ['stop alarm', 'stop my alarm', 'turn off my alarm', 'turn my alarm off', 'stop another alarm']

    reminder = ['remind', 'reminder']

    google_home = ['google home', 'googlehome']

    jokes = ['joke', 'jokes', 'make me laugh']

    notes = ['notes', 'note']

    github = ['git', 'github', 'clone', 'GitHub']

    txt_message = ['message', 'text', 'messages']

    google_search = ['google search']

    tv = ['tv', 'television']

    volume = ['volume', 'mute']

    face_detection = ['face', 'recognize', 'who am i', 'detect', 'facial', 'recognition', 'detection']

    speed_test = ['speed', 'fast']

    bluetooth = ['bluetooth']

    brightness = ['brightness', 'bright', 'dim']

    lights = ['light', 'hallway', 'kitchen', 'living room', 'bedroom']

    guard_enable = ['take care', 'heading out', 'keep an eye', 'turn on security mode', 'enable security mode']

    guard_disable = ["I'm back", 'I am back', 'turn off security mode', 'disable security mode']

    flip_a_coin = ['head', 'tail', 'flip']

    facts = ['fact', 'facts']

    meetings = ['meeting', 'appointment', 'schedule']

    voice_changer = ['voice', 'module', 'audio']

    system_vitals = ['vitals', 'statistics', 'readings', 'stats']

    vpn_server = ['vpn']

    personal_cloud = ['personal cloud', 'private cloud', 'personal server', 'private server']

    ok = ['yeah', 'yes', 'yep', 'go ahead', 'proceed', 'continue', 'carry on', 'please', 'keep going']

    restart = ['restart', 'reboot']

    exit = ['exit', 'quit', 'no', 'nope', 'thanks', 'thank you', 'Xzibit', 'bye', 'good bye', 'see you later',
            'talk to you later', 'activate sentry mode', "that's it", 'that is it']

    sleep = ['exit', 'quit', 'lock', 'sleep', 'Xzibit', 'activate sentry mode']

    kill = ['kill', 'terminate yourself', 'stop running']

    shutdown = ['shutdown', 'shut down', 'terminate']


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
