# noinspection PyUnresolvedReferences
"""List of conversational keywords for each variable which is condition matched in main module.

>>> Conditions

"""

from modules.models import models

env = models.env

greeting = ["how are you", "how are you doing", "how have you been", "how do you do", "how's it going"]

capabilities = ["what can you do", "what all can you do", "what are your capabilities", "what's your capacity",
                "what are you capable of"]

languages = ["what languages do you speak", "what are all the languages you can speak",
             "what languages do you know", "can you speak in a different language",
             "how many languages can you speak", "what are you made of", "what languages can you speak",
             "what languages do you speak", "what are the languages you can speak"]

what = ["what are you"]

who = ["who are you", "what do I call you", "what's your name", "what is your name"]

form = ["where is your body", "where's your body"]

whats_up = ["what's up", "what is up", "what's going on", "sup"]

about_me = ["tell me about you", "tell me something about you", "i would like to get you know you",
            "tell me about yourself"]

wake_up1 = [f"For you {env.title}! Always!", f"At your service {env.title}!"]

wake_up2 = [f"Up and running {env.title}!", f"We are online and ready {env.title}!",
            f"I have indeed been uploaded {env.title}!",
            f"My listeners have been activated {env.title}!"]

wake_up3 = [f"I'm here {env.title}!"]

confirmation = [f"Requesting confirmation {env.title}! Did you mean", f"{env.title}, are you sure you want to"]

acknowledgement = ["Check", "Roger that!", f"Will do {env.title}!", f"You got it {env.title}!", f"Done {env.title}!",
                   f"By all means {env.title}!", f"Indeed {env.title}!", f"Gladly {env.title}!", f"Sure {env.title}!",
                   f"Without fail {env.title}!", f"Buttoned up {env.title}!", f"Executed {env.title}!"]
