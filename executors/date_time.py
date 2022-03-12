from datetime import datetime

from inflect import engine
from pytz import timezone
from timezonefinder import TimezoneFinder

from executors.location import geo_locator
from modules.audio import speaker
from modules.models import models
from modules.utils import globals, support

env = models.env


def current_time(converted: str = None) -> None:
    """Says current time at the requested location if any, else with respect to the current timezone.

    Args:
        converted: Takes the phrase as an argument.
    """
    place = support.get_capitalized(phrase=converted) if converted else None
    if place and len(place) > 3:
        tf = TimezoneFinder()
        place_tz = geo_locator.geocode(place)
        coordinates = place_tz.latitude, place_tz.longitude
        located = geo_locator.reverse(coordinates, language='en')
        data = located.raw
        address = data['address']
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        time_location = f'{city} {state}'.replace('None', '') if city or state else place
        zone = tf.timezone_at(lat=place_tz.latitude, lng=place_tz.longitude)
        datetime_zone = datetime.now(timezone(zone))
        date_tz = datetime_zone.strftime("%A, %B %d, %Y")
        time_tz = datetime_zone.strftime("%I:%M %p")
        dt_string = datetime.now().strftime("%A, %B %d, %Y")
        if date_tz != dt_string:
            date_tz = datetime_zone.strftime("%A, %B %d")
            speaker.speak(text=f'The current time in {time_location} is {time_tz}, on {date_tz}.')
        else:
            speaker.speak(text=f'The current time in {time_location} is {time_tz}.')
    else:
        c_time = datetime.now().strftime("%I:%M %p")
        speaker.speak(text=f'{c_time}.')


def current_date() -> None:
    """Says today's date and adds the current time in speaker queue if report or time_travel function was called."""
    dt_string = datetime.now().strftime("%A, %B")
    date_ = engine().ordinal(datetime.now().strftime("%d"))
    year = str(datetime.now().year)
    event = support.celebrate()
    if globals.called['time_travel']:
        dt_string = f'{dt_string} {date_}'
    else:
        dt_string = f'{dt_string} {date_}, {year}'
    speaker.speak(text=f"It's {dt_string}")
    if event and event == 'Birthday':
        speaker.speak(text=f"It's also your {event} {env.title}!")
    elif event:
        speaker.speak(text=f"It's also {event} {env.title}!")
    if globals.called['report'] or globals.called['time_travel']:
        speaker.speak(text='The current time is, ')
