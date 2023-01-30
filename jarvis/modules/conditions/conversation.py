# noinspection PyUnresolvedReferences
"""List of conversational keywords for each variable which is condition matched in main module.

>>> Conversation

"""

from jarvis.modules.models import models

greeting = ["how are you", "how are you doing", "how have you been", "how do you do", "how's it going", "hows it going"]

capabilities = ["what can you do", "what all can you do", "what are your capabilities", "what's your capacity",
                "what are you capable of", "whats your capacity"]

languages = ["what languages do you speak", "what are all the languages you can speak",
             "what languages do you know", "can you speak in a different language",
             "how many languages can you speak", "what are you made of", "what languages can you speak",
             "what languages do you speak", "what are the languages you can speak"]

what = ["what are you"]

who = ["who are you", "what do I call you", "what's your name", "what is your name", "whats your name"]

age = ["how old are you", "what is your age", "what's your age", "whats your age"]

form = ["where is your body", "where's your body", "wheres your body"]

whats_up = ["what's up", "what is up", "what's going on", "sup", "whats up"]

about_me = ["tell me about you", "tell me something about you", "i would like to get you know you",
            "tell me about yourself"]

wake_up1 = [f"For you {models.env.title}! Always!", f"At your service {models.env.title}!"]

wake_up2 = [f"Up and running {models.env.title}!", f"We are online and ready {models.env.title}!",
            f"I have indeed been uploaded {models.env.title}!",
            f"My listeners have been activated {models.env.title}!"]

wake_up3 = [f"I'm here {models.env.title}!"]

confirmation = [f"Requesting confirmation {models.env.title}! Did you mean",
                f"{models.env.title}, are you sure you want to"]

acknowledgement = ["Check", "Roger that!", f"Will do {models.env.title}!", f"You got it {models.env.title}!",
                   f"Done {models.env.title}!", f"By all means {models.env.title}!", f"Indeed {models.env.title}!",
                   f"Gladly {models.env.title}!", f"Sure {models.env.title}!", f"Without fail {models.env.title}!",
                   f"Buttoned up {models.env.title}!", f"Executed {models.env.title}!"]
