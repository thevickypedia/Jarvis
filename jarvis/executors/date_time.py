from datetime import datetime

import inflect
import pytz
from timezonefinder import TimezoneFinder

from jarvis.executors import location
from jarvis.modules.audio import speaker
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support


def current_time(converted: str = None) -> None:
    """Says current time at the requested location if any, else with respect to the current timezone.

    Args:
        converted: Takes the phrase as an argument.
    """
    place = support.get_capitalized(phrase=converted) if converted else None
    if place and len(place) > 3:
        place_tz = location.geo_locator.geocode(place)
        coordinates = place_tz.latitude, place_tz.longitude
        located = location.geo_locator.reverse(coordinates, language='en')
        address = located.raw.get('address', {})
        city, state = address.get('city'), address.get('state')
        time_location = f'{city} {state}'.replace('None', '') if city or state else place
        zone = TimezoneFinder().timezone_at(lat=place_tz.latitude, lng=place_tz.longitude)
        datetime_zone = datetime.now(pytz.timezone(zone))
        date_tz = datetime_zone.strftime("%A, %B %d, %Y")
        time_tz = datetime_zone.strftime("%I:%M %p")
        dt_string = datetime.now().strftime("%A, %B %d, %Y")
        if date_tz != dt_string:
            date_tz = datetime_zone.strftime("%A, %B %d")
            speaker.speak(text=f'The current time in {time_location} is {time_tz}, on {date_tz}.')
        else:
            speaker.speak(text=f'The current time in {time_location} is {time_tz}.')
    else:
        if shared.called['report'] or shared.called['time_travel']:
            speaker.speak(text=f"The current time is, {datetime.now().strftime('%I:%M %p')}.")
            return
        speaker.speak(text=f"{datetime.now().strftime('%I:%M %p')}.")


def current_date() -> None:
    """Says today's date and adds the current time in speaker queue if report or time_travel function was called."""
    dt_string = datetime.now().strftime("%A, %B")
    date_ = inflect.engine().ordinal(datetime.now().strftime("%d"))
    year = str(datetime.now().year)
    event = support.celebrate()
    if shared.called['time_travel']:
        dt_string = f'{dt_string} {date_}'
    else:
        dt_string = f'{dt_string} {date_}, {year}'
    text = f"It's {dt_string}."
    if event and event == 'Birthday':
        text += f" It's also your {event} {models.env.title}!"
    elif event:
        text += f" It's also {event} {models.env.title}!"
    speaker.speak(text=text)
