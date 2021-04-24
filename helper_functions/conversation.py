class Conversation:
    """list of conversational keywords for each function which is condition matched in jarvis.py"""

    @staticmethod
    def greeting():
        return ['how are you', 'how are you doing', 'how have you been', 'how do you do']

    @staticmethod
    def capabilities():
        return ['what can you do', 'what all can you do', 'what are your capabilities', "what's your capacity",
                'what are you capable of']

    @staticmethod
    def languages():
        return ['what languages do you speak', 'what are all the languages you can speak', 'what languages do you know',
                'can you speak in a different language', 'how many languages can you speak', 'what are you made of',
                'what languages can you speak', 'what languages do you speak', 'what are the languages you can speak']

    @staticmethod
    def what():
        return ['what are you']

    @staticmethod
    def who():
        return ['who are you', 'what do I call you', "what's your name", 'what is your name']

    @staticmethod
    def form():
        return ['where is your body', "where's your body"]

    @staticmethod
    def whats_up():
        return ["what's up", 'what is up', "what's going on", 'sup']

    @staticmethod
    def about_me():
        return ['tell me about you', 'tell me something about you', 'i would like to get you know you',
                'tell me about yourself']


if __name__ == '__main__':
    # TODO: begin diagnostics to use dictionaries instead of long nested if statements in conditions() in jarvis.py
    """Since Python stores the methods and other attributes of a class in a dictionary, which is unordered, 
    looping through and executing all of the functions in python is impossible.
    Since we don't care about order, we can use the class's __dict__ and iter through it's items"""
    funcs = 0
    for method_name, return_value in Conversation.__dict__.items():
        if type(return_value) == staticmethod:
            funcs += 1
    print(funcs)
    # prove time complexity
    from timeit import timeit

    print(f"Accessing the class directly for {funcs} times:")
    print(timeit(f"""
from helper_functions.conversation import Conversation
for _ in range({funcs}):
    Conversation.__dict__.items()"""))
    print(f"Assigning the class to a variable and then access it {funcs} times:")
    print(timeit(f"""
from helper_functions.conversation import Conversation
conversation = Conversation()
for _ in range({funcs}):
    conversation.__dict__.items()"""))
