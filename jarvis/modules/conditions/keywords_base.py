# noinspection PyUnresolvedReferences
"""List of keywords for each variable which is condition matched in the main module.

>>> KeywordsBase

"""

from typing import Dict, List


def keyword_mapping() -> Dict[str, List[str]]:
    """Returns a dictionary of base keywords mapping.

    Returns:
        Dict:
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
        repeat=["repeat", "train"],
        location=["location", "where are you"],
        locate=["locate", "where is my", "where's my", "wheres my"],
        music=["music", "songs", "play"],
        read_gmail=["email", "mail"],
        meaning=["meaning", "dictionary", "definition"],
        todo=["plan", "to do", "to-do", "todo"],
        distance=["far", "distance", "miles"],
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
                    "delete timer", "delete my timer", "delete another timer", "delete an timer"],
        reminder=["remind", "reminder"],
        google_home=["google home", "googlehome"],
        ngrok=["ngrok", "public url"],
        jokes=["joke", "jokes", "make me laugh"],
        notes=["notes", "note"],
        github=["git", "github", "clone", "GitHub", "update yourself", "update your self"],
        send_notification=["message", "text", "sms", "mail"],
        television=["tv", "television"],
        volume=["volume", "mute"],
        faces=["face", "recognize", "who am i", "detect", "facial", "recognition", "detection"],
        speed_test=["speed", "fast"],
        brightness=["brightness", "bright", "dim"],
        lights=["light", "party mode"],
        guard_enable=["turn on security mode", "enable security mode"],
        guard_disable=["turn off security mode", "disable security mode"],
        flip_a_coin=["head", "tail", "flip"],
        facts=["fact", "facts"],
        meetings=["meeting"],
        events=["event"],
        voice_changer=["voice", "module", "audio"],
        system_vitals=["vitals", "statistics", "readings", "stats"],
        vpn_server=["vpn"],
        car=["car", "vehicle", "guard"],
        garage=["garage"],
        automation=["automation"],
        background_tasks=["background"],
        photo=["picture", "snap", "photo"],
        version=["version"],
        simulation=["simulator", "variation", "simulation"],
        ok=["yeah", "yes", "yep", "go ahead", "proceed", "continue", "carry on", "please", "keep going"],
        restart_control=["restart", "reboot"],
        exit_=["exit", "quit", "no", "nope", "thank you", "Xzibit", "bye", "good bye", "see you later",
               "talk to you later", "that's it", "that is it", "never mind", "nevermind", "thats it"],
        sleep_control=["lock", "screen", "pc", "computer"],
        sentry=["sleep", "activate sentry mode"],
        kill=["kill", "terminate yourself", "stop running"],
        shutdown=["shutdown", "shut down", "terminate"]
    )
