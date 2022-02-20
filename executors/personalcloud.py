import random
from threading import Thread

from modules.audio import speaker
from modules.conditions import conversation
from modules.personalcloud import pc_handler
from modules.utils import globals, support

env = globals.ENV


def personal_cloud(phrase: str) -> None:
    """Enables or disables personal cloud.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    phrase = phrase.lower()
    if 'enable' in phrase or 'initiate' in phrase or 'kick off' in phrase or 'start' in phrase:
        Thread(target=pc_handler.enable,
               kwargs={"target_path": env.home, "username": env.gmail_user, "password": env.gmail_pass,
                       "phone_number": env.phone_number, "recipient": env.recipient}).start()
        speaker.speak(text="Personal Cloud has been triggered sir! I will send the login details to your phone number "
                           "once the server is up and running.")
    elif 'disable' in phrase or 'stop' in phrase:
        Thread(target=pc_handler.disable, args=[env.home]).start()
        speaker.speak(text=random.choice(conversation.acknowledgement))
    else:
        speaker.speak(text="I didn't quite get that sir! Please tell me if I should enable or disable your server.")
        Thread(target=support.unrecognized_dumper, args=[{'PERSONAL_CLOUD': phrase}])
