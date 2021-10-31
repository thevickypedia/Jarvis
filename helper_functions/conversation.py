from os import environ


class Conversation:
    """list of conversational keywords for each variable which is condition matched in main module.

    >>> Conversation

    """

    if not environ.get('COMMIT'):
        greeting = ['how are you', 'how are you doing', 'how have you been', 'how do you do']

        capabilities = ['what can you do', 'what all can you do', 'what are your capabilities', "what's your capacity",
                        'what are you capable of']

        languages = ['what languages do you speak', 'what are all the languages you can speak',
                     'what languages do you know', 'can you speak in a different language',
                     'how many languages can you speak', 'what are you made of', 'what languages can you speak',
                     'what languages do you speak', 'what are the languages you can speak']

        what = ['what are you']

        who = ['who are you', 'what do I call you', "what's your name", 'what is your name']

        form = ['where is your body', "where's your body"]

        whats_up = ["what's up", 'what is up', "what's going on", 'sup']

        about_me = ['tell me about you', 'tell me something about you', 'i would like to get you know you',
                    'tell me about yourself']


if __name__ == '__main__':
    from pprint import pprint
    all_vars = {}
    conversation = vars(Conversation)
    for class_var in conversation:
        if not class_var.startswith('_'):
            all_vars.update({class_var: conversation[class_var]})
    pprint(all_vars)
