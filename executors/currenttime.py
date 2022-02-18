from datetime import datetime

from pytz import timezone
from timezonefinder import TimezoneFinder

from executors.location import geo_locator
from modules.audio import speaker
from modules.utils import support


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
