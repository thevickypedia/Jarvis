import json
import sys
import urllib.request
from datetime import datetime

import yaml
from inflect import engine

from executors.location import geo_locator
from modules.audio import speaker
from modules.models import models
from modules.temperature import temperature
from modules.utils import shared, support

env = models.env
fileio = models.fileio


def weather(phrase: str = None) -> None:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not env.weather_api:
        support.no_env_vars()
        return

    place = None
    if phrase:
        place = support.get_capitalized(phrase=phrase)
    sys.stdout.write('\rGetting your weather info')
    if place:
        desired_location = geo_locator.geocode(place)
        coordinates = desired_location.latitude, desired_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        address = located.raw['address']
        city = address.get('city')
        state = address.get('state')
        lat = located.latitude
        lon = located.longitude
    else:
        with open(fileio.location) as file:
            current_location = yaml.load(stream=file, Loader=yaml.FullLoader)

        city = current_location.get('address', {}).get('city', 'Unknown')
        state = current_location.get('address', {}).get('state', 'Unknown')
        lat = current_location['latitude']
        lon = current_location['longitude']
    weather_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,' \
                  f'hourly&appid={env.weather_api}'
    response = json.loads(urllib.request.urlopen(url=weather_url).read())  # loads the response in a json

    weather_location = f'{city} {state}'.replace('None', '') if city != state else city or state

    if phrase and any(match_word in phrase.lower() for match_word in ['tomorrow', 'day after', 'next week', 'tonight',
                                                                      'afternoon', 'evening']):
        if 'tonight' in phrase:
            key = 0
            tell = 'tonight'
        elif 'day after' in phrase:
            key = 2
            tell = 'day after tomorrow '
        elif 'tomorrow' in phrase:
            key = 1
            tell = 'tomorrow '
        elif 'next week' in phrase:
            key = -1
            next_week = datetime.fromtimestamp(response['daily'][-1]['dt']).strftime("%A, %B %d")
            tell = f"on {' '.join(next_week.split()[0:-1])} {engine().ordinal(next_week.split()[-1])}"
        else:
            key = 0
            tell = 'today '
        if 'morning' in phrase:
            when = 'morn'
            tell += 'morning'
        elif 'evening' in phrase:
            when = 'eve'
            tell += 'evening'
        elif 'tonight' in phrase:
            when = 'night'
        elif 'night' in phrase:
            when = 'night'
            tell += 'night'
        else:
            when = 'day'
            tell += ''
        if 'alerts' in response:
            alerts = response['alerts'][0]['event']
            start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
            end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
        else:
            alerts, start_alert, end_alert = None, None, None
        condition = response['daily'][key]['weather'][0]['description']
        high = int(temperature.k2f(response['daily'][key]['temp']['max']))
        low = int(temperature.k2f(response['daily'][1]['temp']['min']))
        temp_f = int(temperature.k2f(response['daily'][key]['temp'][when]))
        temp_feel_f = int(temperature.k2f(response['daily'][key]['feels_like'][when]))
        sunrise = datetime.fromtimestamp(response['daily'][key]['sunrise']).strftime("%I:%M %p")
        sunset = datetime.fromtimestamp(response['daily'][key]['sunset']).strftime("%I:%M %p")
        output = f"The weather in {weather_location} {tell} would be {temp_f}°F, with a high of {high}, and a low of " \
                 f"{low}. "
        if temp_feel_f != temp_f:
            output += f"But due to {condition} it will fee like it is {temp_feel_f}°F. "
        output += f"Sunrise at {sunrise}. Sunset at {sunset}. "
        if alerts and start_alert and end_alert:
            output += f'There is a weather alert for {alerts} between {start_alert} and {end_alert}'
        speaker.speak(text=output)
        return

    condition = response['current']['weather'][0]['description']
    high = int(temperature.k2f(arg=response['daily'][0]['temp']['max']))
    low = int(temperature.k2f(arg=response['daily'][0]['temp']['min']))
    temp_f = int(temperature.k2f(arg=response['current']['temp']))
    temp_feel_f = int(temperature.k2f(arg=response['current']['feels_like']))
    sunrise = datetime.fromtimestamp(response['daily'][0]['sunrise']).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(response['daily'][0]['sunset']).strftime("%I:%M %p")
    if shared.called['time_travel']:
        if 'rain' in condition or 'showers' in condition:
            feeling = 'rainy'
            weather_suggest = 'You might need an umbrella" if you plan to head out.'
        elif temp_feel_f <= 40:
            feeling = 'freezing'
            weather_suggest = 'Perhaps" it is time for winter clothing.'
        elif 41 <= temp_feel_f <= 60:
            feeling = 'cool'
            weather_suggest = 'I think a lighter jacket would suffice" if you plan to head out.'
        elif 61 <= temp_feel_f <= 75:
            feeling = 'optimal'
            weather_suggest = 'It might be a perfect weather for a hike, or perhaps a walk.'
        elif 76 <= temp_feel_f <= 85:
            feeling = 'warm'
            weather_suggest = 'It is a perfect weather for some outdoor entertainment.'
        elif temp_feel_f > 85:
            feeling = 'hot'
            weather_suggest = "I would not recommend thick clothes today."
        else:
            feeling, weather_suggest = '', ''
        wind_speed = response['current']['wind_speed']
        if wind_speed > 10:
            output = f'The weather in {city} is {feeling} {temp_f}°, but due to the current wind conditions ' \
                     f'(which is {wind_speed} miles per hour), it feels like {temp_feel_f}°. {weather_suggest}'
        else:
            output = f'The weather in {city} is {feeling} {temp_f}°, and it currently feels like {temp_feel_f}°. ' \
                     f'{weather_suggest}'
    elif place or not shared.called['report']:
        output = f'The weather in {weather_location} is {temp_f}°F, with a high of {high}, and a low of {low}. ' \
                 f'It currently feels like {temp_feel_f}°F, and the current condition is {condition}.'
    else:
        output = f'The weather in {weather_location} is {temp_f}°F, with a high of {high}, and a low of {low}. ' \
                 f'It currently feels Like {temp_feel_f}°F, and the current condition is {condition}. ' \
                 f'Sunrise at {sunrise}. Sunset at {sunset}.'
    if 'alerts' in response:
        alerts = response['alerts'][0]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
    else:
        alerts, start_alert, end_alert = None, None, None
    if alerts and start_alert and end_alert:
        output += f' You have a weather alert for {alerts} between {start_alert} and {end_alert}'
    speaker.speak(text=output)
