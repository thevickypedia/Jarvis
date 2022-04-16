import webbrowser
from threading import Thread

from executors import controls
from executors.alarm import kill_alarm, set_alarm
from executors.automation import automation_handler
from executors.bluetooth import bluetooth
from executors.car import car
from executors.communicator import read_gmail, send_sms
from executors.date_time import current_date, current_time
from executors.display_functions import brightness
from executors.face import face_detection
from executors.github import github
from executors.guard import guard_enable
from executors.internet import ip_info, speed_test
from executors.lights import lights
from executors.location import (directions, distance, locate, locate_places,
                                location)
from executors.logger import logger
from executors.others import (apps, facts, flip_a_coin, google_home, jokes,
                              meaning, music, news, notes, repeat, report,
                              sprint_name)
from executors.remind import reminder
from executors.robinhood import robinhood
from executors.system import system_info, system_vitals
from executors.todo_list import add_todo, delete_todo, delete_todo_items, todo
from executors.tv import television
from executors.unconditional import alpha, google, google_maps, google_search
from executors.vpn_server import vpn_server
from executors.weather import weather
from executors.wiki import wikipedia_
from modules.audio.speaker import speak
from modules.audio.voices import voice_changer
from modules.audio.volume import volume
from modules.conditions import conversation, keywords
from modules.exceptions import StopSignal
from modules.meetings.events import events
from modules.meetings.icalendar import meetings
from modules.utils import support


def conditions(converted: str, should_return: bool = False) -> bool:
    """Conditions function is used to check the message processed.

    Uses the keywords to match pre-defined conditions and trigger the appropriate function which has dedicated task.

    Args:
        converted: Takes the voice recognized statement as argument.
        should_return: A boolean flag sent by ``Activator`` to indicate that the ``else`` part shouldn't be executed.

    Returns:
        bool:
        Boolean True only when asked to sleep for conditioned sleep message.
    """
    converted_lower = converted.lower()
    todo_checks = ['to do', 'to-do', 'todo']

    if any(word in converted_lower for word in keywords.lights):
        lights(converted)

    elif any(word in converted_lower for word in keywords.volume):
        volume(converted)

    elif any(word in converted_lower for word in keywords.television):
        television(converted)

    elif any(word in converted_lower for word in keywords.weather):
        weather(converted)

    elif any(word in converted_lower for word in keywords.car):
        car(converted_lower)

    elif any(word in converted_lower for word in keywords.meetings):
        meetings()

    elif any(word in converted_lower for word in keywords.current_date) and \
            not any(word in converted_lower for word in keywords.avoid):
        current_date()

    elif any(word in converted_lower for word in keywords.current_time) and \
            not any(word in converted_lower for word in keywords.avoid):
        current_time(converted)

    elif any(word in converted_lower for word in keywords.system_info):
        system_info()

    elif any(word in converted_lower for word in keywords.ip_info) or 'IP' in converted.split():
        ip_info(converted)

    elif any(word in converted_lower for word in keywords.wikipedia_):
        wikipedia_()

    elif any(word in converted_lower for word in keywords.news):
        news()

    elif any(word in converted_lower for word in keywords.report):
        report()

    elif any(word in converted_lower for word in keywords.robinhood):
        robinhood()

    elif any(word in converted_lower for word in keywords.repeat):
        repeat()

    elif any(word in converted_lower for word in keywords.location):
        location()

    elif any(word in converted_lower for word in keywords.locate):
        locate(converted)

    elif any(word in converted_lower for word in keywords.read_gmail):
        read_gmail()

    elif any(word in converted_lower for word in keywords.meaning):
        meaning(converted)

    elif any(word in converted_lower for word in keywords.delete_todo) and 'items' in converted_lower and \
            any(word in converted_lower for word in todo_checks):
        delete_todo_items()

    elif any(word in converted_lower for word in keywords.todo):
        todo()

    elif any(word in converted_lower for word in keywords.add_todo) and \
            any(word in converted_lower for word in todo_checks):
        add_todo()

    elif any(word in converted_lower for word in keywords.delete_todo) and \
            any(word in converted_lower for word in todo_checks):
        delete_todo()

    elif any(word in converted_lower for word in keywords.distance) and \
            not any(word in converted_lower for word in keywords.avoid):
        distance(converted)

    elif any(word in converted_lower for word in conversation.form):
        speak(text="I am a program, I'm without form.")

    elif any(word in converted_lower for word in keywords.locate_places):
        locate_places(converted)

    elif any(word in converted_lower for word in keywords.directions):
        directions(converted)

    elif any(word in converted_lower for word in keywords.kill_alarm):
        kill_alarm()

    elif any(word in converted_lower for word in keywords.set_alarm):
        set_alarm(converted)

    elif any(word in converted_lower for word in keywords.google_home):
        google_home()

    elif any(word in converted_lower for word in keywords.jokes):
        jokes()

    elif any(word in converted_lower for word in keywords.reminder):
        reminder(converted)

    elif any(word in converted_lower for word in keywords.notes):
        notes()

    elif any(word in converted_lower for word in keywords.github):
        github(converted)

    elif any(word in converted_lower for word in keywords.send_sms):
        send_sms(converted)

    elif any(word in converted_lower for word in keywords.google_search):
        google_search(converted)

    elif any(word in converted_lower for word in keywords.apps):
        apps(converted)

    elif any(word in converted_lower for word in keywords.music):
        music(converted)

    elif any(word in converted_lower for word in keywords.face_detection):
        face_detection()

    elif any(word in converted_lower for word in keywords.speed_test):
        speed_test()

    elif any(word in converted_lower for word in keywords.bluetooth):
        bluetooth(converted)

    elif any(word in converted_lower for word in keywords.brightness):
        brightness(converted)

    elif any(word in converted_lower for word in keywords.guard_enable):
        guard_enable()

    elif any(word in converted_lower for word in keywords.flip_a_coin):
        flip_a_coin()

    elif any(word in converted_lower for word in keywords.facts):
        facts()

    elif any(word in converted_lower for word in keywords.events):
        events()

    elif any(word in converted_lower for word in keywords.voice_changer):
        voice_changer(converted)

    elif any(word in converted_lower for word in keywords.system_vitals):
        system_vitals()

    elif any(word in converted_lower for word in keywords.vpn_server):
        vpn_server(converted)

    elif any(word in converted_lower for word in keywords.automation):
        automation_handler(converted_lower)

    elif any(word in converted_lower for word in keywords.sprint):
        sprint_name()

    elif any(word in converted_lower for word in conversation.greeting):
        if not alpha(text=converted):
            speak(text='I am spectacular. I hope you are doing fine too.')

    elif any(word in converted_lower for word in conversation.capabilities):
        speak(text='There is a lot I can do. For example: I can get you the weather at any location, news around '
                   'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                   'system configuration, tell your investment details, locate your phone, find distance between '
                   'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
                   ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')

    elif any(word in converted_lower for word in conversation.languages):
        speak(text="Tricky question!. I'm configured in python, and I can speak English.")

    elif any(word in converted_lower for word in conversation.whats_up):
        speak(text="My listeners are up. There is nothing I cannot process. So ask me anything..")

    elif any(word in converted_lower for word in conversation.what):
        speak(text="I'm just a pre-programmed virtual assistant.")

    elif any(word in converted_lower for word in conversation.who):
        speak(text="I am Jarvis. A virtual assistant designed by Mr.Raauv.")

    elif any(word in converted_lower for word in conversation.about_me):
        speak(text="I am Jarvis. A virtual assistant designed by Mr.Raauv. "
                   "I'm just a pre-programmed virtual assistant, trying to become a natural language UI. "
                   "I can seamlessly take care of your daily tasks, and also help with most of your work!")

    elif any(word in converted_lower for word in keywords.sleep_control):
        return controls.sleep_control(converted)

    elif any(word in converted_lower for word in keywords.restart_control):
        controls.restart_control(converted)

    elif any(word in converted_lower for word in keywords.kill) and \
            not any(word in converted_lower for word in keywords.avoid):
        raise StopSignal

    elif any(word in converted_lower for word in keywords.shutdown):
        controls.shutdown()

    elif should_return:
        Thread(target=support.unrecognized_dumper, args=[{'ACTIVATOR': converted}]).start()
        return False

    else:
        logger.info(f'Received unrecognized lookup parameter: {converted}')
        Thread(target=support.unrecognized_dumper, args=[{'CONDITIONS': converted}]).start()
        if not alpha(text=converted):
            if not google_maps(query=converted):
                if google(query=converted):
                    # if none of the conditions above are met, opens a Google search on default browser
                    search_query = str(converted).replace(' ', '+')
                    unknown_url = f"https://www.google.com/search?q={search_query}"
                    webbrowser.open(url=unknown_url)
