import random
from datetime import datetime
from typing import NoReturn

from dateutil.relativedelta import relativedelta

from jarvis.modules.audio.speaker import speak
from jarvis.modules.models.models import settings


def form(*args) -> NoReturn:
    """Response for form."""
    speak(text="I am a program, I'm without form.")


def greeting(*args) -> NoReturn:
    """Response for greeting."""
    speak(text=random.choice(['I am spectacular. I hope you are doing fine too.', 'I am doing well. Thank you.',
                              'I am great. Thank you.']))


def capabilities(*args) -> NoReturn:
    """Response for capabilities."""
    speak(text='There is a lot I can do. For example: I can get you the weather at any location, news around '
               'you, meanings of words, launch applications, create a to-do list, check your emails, get your '
               'system configuration, tell your investment details, locate your phone, find distance between '
               'places, set an alarm, play music on smart devices around you, control your TV, tell a joke, send'
               ' a message, set reminders, scan and clone your GitHub repositories, and much more. Time to ask,.')


def languages(*args) -> NoReturn:
    """Response for languages."""
    speak(text="Tricky question!. I'm configured in python, and I can speak English.")


def whats_up(*args) -> NoReturn:
    """Response for what's up."""
    speak(text="My listeners are up. There is nothing I cannot process. So ask me anything..")


def what(*args) -> NoReturn:
    """Response for what."""
    speak(text=f"The name is {settings.bot}. I'm just a pre-programmed virtual assistant.")


def who(*args) -> NoReturn:
    """Response for whom."""
    speak(text=f"I am {settings.bot}. A virtual assistant designed by Mr.Raauv.")


def age(*args) -> NoReturn:
    """Response for age."""
    relative_date = relativedelta(dt1=datetime.strptime(datetime.strftime(datetime.now(), "%Y-%m-%d"), "%Y-%m-%d"),
                                  dt2=datetime.strptime("2020-09-06", "%Y-%m-%d"))
    statement = f"{relative_date.years} years, {relative_date.months} months and {relative_date.days} days"
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


def about_me(*args) -> NoReturn:
    """Response for about me."""
    speak(text=f"I am {settings.bot}. A virtual assistant designed by Mr.Raauv. "
               "I'm just a pre-programmed virtual assistant, trying to become a natural language UI. "
               "I can seamlessly take care of your daily tasks, and also help with most of your work!")
