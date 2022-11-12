import random
from datetime import datetime
from threading import Thread

from dateutil.relativedelta import relativedelta

from executors import controls
from executors.alarm import kill_alarm, set_alarm
from executors.automation import automation_handler
from executors.car import car
from executors.communicator import read_gmail, send_sms
from executors.date_time import current_date, current_time
from executors.display_functions import brightness
from executors.face import faces
from executors.github import github
from executors.guard import guard_disable, guard_enable
from executors.internet import ip_info, speed_test
from executors.lights import lights
from executors.location import (directions, distance, locate, locate_places,
                                location)
from executors.myq_controller import garage
from executors.others import (abusive, apps, facts, flip_a_coin, google_home,
                              jokes, meaning, music, news, notes, photo,
                              repeat, report, sprint_name, version)
from executors.remind import reminder
from executors.robinhood import robinhood
from executors.system import system_info, system_vitals
from executors.todo_list import add_todo, delete_todo, delete_todo_items, todo
from executors.tv import television
from executors.unconditional import alpha, google_maps
from executors.volume import volume
from executors.vpn_server import vpn_server
from executors.weather import weather
from executors.wiki import wikipedia_
from executors.word_match import word_match
from modules.audio.speaker import speak
from modules.audio.voices import voice_changer
from modules.conditions import conversation
from modules.conditions import keywords as keywords_mod
from modules.exceptions import StopSignal
from modules.logger.custom_logger import logger
from modules.meetings.events import events
from modules.meetings.icalendar import meetings
from modules.models.models import settings
from modules.utils import support


def conditions(phrase: str, should_return: bool = False) -> bool:
    """Conditions function is used to check the message processed.

    Uses the keywords to match pre-defined conditions and trigger the appropriate function which has dedicated task.

    Args:
        phrase: Takes the voice recognized statement as argument.
        should_return: A boolean flag sent by ``Activator`` to indicate that the ``else`` part shouldn't be executed.

    Returns:
        bool:
        Boolean True only when asked to sleep for conditioned sleep message.
    """
    keywords = keywords_mod.keywords
    todo_checks = ['to do', 'to-do', 'todo']

    if "*" in phrase:
        abusive(phrase)

    elif word_match(phrase=phrase, match_list=keywords.lights):
        lights(phrase)

    elif word_match(phrase=phrase, match_list=keywords.television):
        television(phrase)

    elif word_match(phrase=phrase, match_list=keywords.volume):
        volume(phrase)

    elif word_match(phrase=phrase, match_list=keywords.car):
        car(phrase.lower())

    elif word_match(phrase=phrase, match_list=keywords.garage):
        garage(phrase.lower())

    elif word_match(phrase=phrase, match_list=keywords.weather):
        weather(phrase)

    # ORDER OF THE ABOVE SHOULD BE RETAINED

    elif word_match(phrase=phrase, match_list=keywords.meetings):
        meetings()

    elif word_match(phrase=phrase, match_list=keywords.current_date) and \
            not word_match(phrase=phrase, match_list=keywords.avoid):
        current_date()

    elif word_match(phrase=phrase, match_list=keywords.current_time) and \
            not word_match(phrase=phrase, match_list=keywords.avoid):
        current_time(phrase)

    elif word_match(phrase=phrase, match_list=keywords.system_info):
        system_info()

    elif word_match(phrase=phrase, match_list=keywords.ip_info) or 'IP' in phrase.split():
        ip_info(phrase)

    elif word_match(phrase=phrase, match_list=keywords.wikipedia_):
        wikipedia_()

    elif word_match(phrase=phrase, match_list=keywords.news):
        news()

    elif word_match(phrase=phrase, match_list=keywords.report):
        report()

    elif word_match(phrase=phrase, match_list=keywords.robinhood):
        robinhood()

    elif word_match(phrase=phrase, match_list=keywords.repeat):
        repeat()

    elif word_match(phrase=phrase, match_list=keywords.location):
        location()

    elif word_match(phrase=phrase, match_list=keywords.locate):
        locate(phrase)

    elif word_match(phrase=phrase, match_list=keywords.read_gmail):
        read_gmail()

    elif word_match(phrase=phrase, match_list=keywords.meaning):
        meaning(phrase)

    elif word_match(phrase=phrase, match_list=keywords.delete_todo) and 'items' in phrase.lower() and \
            word_match(phrase=phrase, match_list=todo_checks):
        delete_todo_items()

    elif word_match(phrase=phrase, match_list=keywords.todo):
        todo()

    elif word_match(phrase=phrase, match_list=keywords.add_todo) and \
            word_match(phrase=phrase, match_list=todo_checks):
        add_todo()

    elif word_match(phrase=phrase, match_list=keywords.delete_todo) and \
            word_match(phrase=phrase, match_list=todo_checks):
        delete_todo()

    elif word_match(phrase=phrase, match_list=keywords.distance) and \
            not word_match(phrase=phrase, match_list=keywords.avoid):
        distance(phrase)

    elif word_match(phrase=phrase, match_list=conversation.form):
        speak(text="I am a program, I'm without form.")

    elif word_match(phrase=phrase, match_list=keywords.locate_places):
        locate_places(phrase)

    elif word_match(phrase=phrase, match_list=keywords.directions):
        directions(phrase)

    elif word_match(phrase=phrase, match_list=keywords.kill_alarm):
        kill_alarm(phrase)

    elif word_match(phrase=phrase, match_list=keywords.set_alarm):
        set_alarm(phrase)

    elif word_match(phrase=phrase, match_list=keywords.google_home):
        google_home()

    elif word_match(phrase=phrase, match_list=keywords.jokes):
        jokes()

    elif word_match(phrase=phrase, match_list=keywords.reminder):
        reminder(phrase)

    elif word_match(phrase=phrase, match_list=keywords.notes):
        notes()

    elif word_match(phrase=phrase, match_list=keywords.github):
        github(phrase)

    elif word_match(phrase=phrase, match_list=keywords.send_sms):
        send_sms(phrase)

    elif word_match(phrase=phrase, match_list=keywords.apps):
        apps(phrase)

    elif word_match(phrase=phrase, match_list=keywords.music):
        music(phrase)

    elif word_match(phrase=phrase, match_list=keywords.faces):
        faces(phrase)

    elif word_match(phrase=phrase, match_list=keywords.speed_test) and \
            ('internet' in phrase.lower() or 'connection' in phrase.lower() or 'run' in phrase.lower()):
        speed_test()

    elif word_match(phrase=phrase, match_list=keywords.brightness):
        brightness(phrase)

    elif word_match(phrase=phrase, match_list=keywords.guard_enable):
        guard_enable()

    elif word_match(phrase=phrase, match_list=keywords.guard_disable):
        guard_disable()

    elif word_match(phrase=phrase, match_list=keywords.flip_a_coin):
        flip_a_coin()

    elif word_match(phrase=phrase, match_list=keywords.facts):
        facts()

    elif word_match(phrase=phrase, match_list=keywords.events):
        events()

    elif word_match(phrase=phrase, match_list=keywords.voice_changer):
        voice_changer(phrase)

    elif word_match(phrase=phrase, match_list=keywords.system_vitals):
        system_vitals()

    elif word_match(phrase=phrase, match_list=keywords.vpn_server):
        vpn_server(phrase)

    elif word_match(phrase=phrase, match_list=keywords.automation):
        automation_handler(phrase.lower())

    elif word_match(phrase=phrase, match_list=keywords.sprint):
        sprint_name()

    elif word_match(phrase=phrase, match_list=keywords.photo):
        photo()

    elif word_match(phrase=phrase, match_list=keywords.version):
        version()

    elif word_match(phrase=phrase, match_list=conversation.greeting):
        speak(text=random.choice(['I am spectacular. I hope you are doing fine too.', 'I am doing well. Thank you.',
                                  'I am great. Thank you.']))

    elif word_match(phrase=phrase, match_list=conversation.capabilities):
        speak(text='There is a lot I can do. For example: I can get you the weather at any location, news around '
                   'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
                   'system configuration, tell your investment details, locate your phone, find distance between '
                   'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
                   ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')

    elif word_match(phrase=phrase, match_list=conversation.languages):
        speak(text="Tricky question!. I'm configured in python, and I can speak English.")

    elif word_match(phrase=phrase, match_list=conversation.whats_up):
        speak(text="My listeners are up. There is nothing I cannot process. So ask me anything..")

    elif word_match(phrase=phrase, match_list=conversation.what):
        speak(text=f"The name is {settings.bot}. I'm just a pre-programmed virtual assistant.")

    elif word_match(phrase=phrase, match_list=conversation.who):
        speak(text=f"I am {settings.bot}. A virtual assistant designed by Mr.Raauv.")

    elif word_match(phrase=phrase, match_list=conversation.age):
        relative_date = relativedelta(dt1=datetime.strptime(datetime.strftime(datetime.now(), "%Y-%m-%d"), "%Y-%m-%d"),
                                      dt2=datetime.strptime("2020-09-06", "%Y-%m-%d"))
        statement = f"{relative_date.years} years, {relative_date.months} months and {relative_date.days} days."
        if not relative_date.years:
            statement = statement.replace(f"{relative_date.years} years, ", "")
        elif relative_date.years == 1:
            statement = statement.replace("years", "year")
        if not relative_date.months:
            statement = statement.replace(f"{relative_date.months} months", "")
        elif relative_date.months == 1:
            statement = statement.replace("months", "month")
        if not relative_date.days:
            statement = statement.replace(f"{relative_date.days} days", "")
        elif relative_date.days == 1:
            statement = statement.replace("days", "day")
        speak(text=f"I'm {statement} old.")

    elif word_match(phrase=phrase, match_list=conversation.about_me):
        speak(text=f"I am {settings.bot}. A virtual assistant designed by Mr.Raauv. "
                   "I'm just a pre-programmed virtual assistant, trying to become a natural language UI. "
                   "I can seamlessly take care of your daily tasks, and also help with most of your work!")

    elif word_match(phrase=phrase, match_list=keywords.sleep_control):
        return controls.sleep_control()

    elif word_match(phrase=phrase, match_list=keywords.sentry):
        return controls.sentry()

    elif word_match(phrase=phrase, match_list=keywords.restart_control):
        controls.restart_control(phrase)

    elif word_match(phrase=phrase, match_list=keywords.kill) and \
            not word_match(phrase=phrase, match_list=keywords.avoid):
        raise StopSignal

    elif word_match(phrase=phrase, match_list=keywords.shutdown):
        controls.shutdown()

    elif should_return:
        Thread(target=support.unrecognized_dumper, args=[{'ACTIVATOR': phrase}]).start()
        return False

    else:
        logger.info(f'Received unrecognized lookup parameter: {phrase}')
        Thread(target=support.unrecognized_dumper, args=[{'CONDITIONS': phrase}]).start()
        if not alpha(text=phrase):
            google_maps(query=phrase)
