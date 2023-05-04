# noinspection PyUnresolvedReferences
"""List of keywords for each variable which is condition matched in the main module.

>>> KeywordsBase

"""

from typing import Dict, List


def keyword_mapping() -> Dict[str, List[str]]:
    """Returns a dictionary of base keywords mapping.

    See Also:
        - Keywords should have both singular and plural forms wherever possible.
        - An alternate is to use

        .. code-block:: python

            import inflect
            engine = inflect.engine()
            engine.plural(phrase)
            engine.singular_noun(phrase)

        - But the approach is time taking and inconsistent.

    Returns:
        dict:
        Dictionary of keywords and in a mapping dictionary.
    """
    return dict(
        current_date=["today's date", "current date", "what is the date", "what's the date", "todays date",
                      "whats the date"],
        current_time=["current time", "time now", "time in", "what is the time", "what's the time",
                      "whats the time"],
        weather=["weather", "temperature", "sunrise", "sun rise", "sunset", "sun set"],
        system_info=["configuration"],
        ip_info=["address"],
        wikipedia_=["wikipedia", "info", "information"],
        news=["news"],
        report=["report"],
        robinhood=["robinhood", "investment", "portfolio", "summary"],
        apps=["launch"],
        listener_control=["listener"],
        secrets=["secret", "secrets", "param", "params", "parameter", "parameters"],
        repeat=["repeat"],
        location=["location", "where are you"],
        locate=["locate", "where is my", "where's my", "wheres my"],
        music=["music", "songs", "play", "song"],
        read_gmail=["email", "mail", "mails", "emails"],
        meaning=["meaning", "dictionary", "definition", "meanings", "definitions"],
        todo=["plan", "to do", "to-do", "todo", "plans"],
        distance=["far", "distance", "miles", "kilometers", "mile", "kilometer"],
        avoid=["sun", "moon", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune",
               "pluto", "a.m.", "p.m.", "update my to do list", "launch", "safari", "body", "human", "centimeter",
               "server", "cloud", "update"],
        locate_places=["where is", "where's", "which city", "which state", "which country", "which county", "wheres"],
        directions=["take me", "directions"],
        set_alarm=["alarm", "wake me", "timer"],
        kill_alarm=["stop alarm", "stop my alarm", "stop another alarm", "stop an alarm",
                    "stop timer", "stop my timer", "stop another timer", "stop an timer",
                    "turn off my alarm", "turn my alarm off", "stop another alarm", "turn off alarm",
                    "turn off my timer", "turn my timer off", "stop another timer", "turn off timer",
                    "delete alarm", "delete my alarm", "delete another alarm", "delete an alarm",
                    "delete timer", "delete my timer", "delete another timer", "delete an timer",
                    "stop all my alarms", "turn off all my alarms", "delete all my alarms"],
        reminder=["remind", "reminder", "reminders"],
        google_home=["google home", "googlehome"],
        ngrok=["ngrok", "public url"],
        jokes=["joke", "jokes", "make me laugh"],
        notes=["notes", "note"],
        github=["git", "github", "clone", "GitHub"],
        send_notification=["message", "text", "sms", "mail", "email", "messages", "mails", "emails"],
        television=["tv", "television"],
        volume=["volume", "mute"],
        faces=["face", "recognize", "who am i", "detect", "facial", "recognition", "detection", "faces"],
        speed_test=["speed", "fast"],
        brightness=["brightness", "bright", "dim"],
        lights=["light", "party mode", "lights"],
        guard_enable=["turn on security mode", "enable security mode",
                      "turn on guardian mode", "enable guardian mode"],
        guard_disable=["turn off security mode", "disable security mode",
                       "turn off guardian mode", "disable guardian mode"],
        flip_a_coin=["head", "tail", "flip", "heads", "tails"],
        facts=["fact", "facts"],
        meetings=["meeting", "meetings"],
        events=["event", "events"],
        voice_changer=["voice", "voices"],
        system_vitals=["vitals", "statistics", "readings", "stats"],
        vpn_server=["vpn"],
        car=["car", "vehicle"],
        garage=["garage"],
        automation=["automation"],
        background_tasks=["background"],
        photo=["picture", "snap", "photo", "pictures", "photos"],
        version=["version"],
        simulation=["simulator", "variation", "simulation", "variations"],
        ok=["yeah", "yes", "yep", "go ahead", "proceed", "continue", "carry on", "please", "keep going"],
        restart_control=["restart", "reboot"],
        exit_=["exit", "quit", "no", "nope", "thank you", "Xzibit", "bye", "good bye", "see you later",
               "talk to you later", "that's it", "that is it", "never mind", "nevermind", "thats it"],
        sleep_control=["lock", "screen", "pc", "computer"],
        sentry=["sleep", "activate sentry mode"],
        kill=["kill", "terminate yourself", "stop running"],
        shutdown=["shutdown", "shut down", "terminate"]
    )
