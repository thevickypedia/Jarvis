import json
import urllib.error
import urllib.request
from datetime import datetime

import inflect
import yaml

from jarvis.executors.location import geo_locator
from jarvis.executors.word_match import word_match
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.temperature import temperature
from jarvis.modules.utils import shared, support


def weather(phrase: str = None) -> None:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not models.env.weather_api:
        logger.warning("Weather apikey not found.")
        support.no_env_vars()
        return

    place = None
    if phrase:
        place = support.get_capitalized(phrase=phrase, ignore=('Sunday', 'Monday', 'Tuesday',
                                                               'Wednesday', 'Thursday', 'Friday', 'Saturday'))
        phrase = phrase.lower()
    if place:
        logger.info(f'Identified place: {place}')
        desired_location = geo_locator.geocode(place)
        if not desired_location:
            logger.error(f"Failed to get coordinates for the place: {place!r}")
            speaker.speak(text=f"I'm sorry {models.env.title}! "
                               f"I wasn't able to get the weather information at {place}!")
            return
        coordinates = desired_location.latitude, desired_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        address = located.raw['address']
        city = address.get('city') or address.get('town') or address.get('hamlet') or 'Unknown'
        state = address.get('state', 'Unknown')
        lat = located.latitude
        lon = located.longitude
    else:
        try:
            with open(models.fileio.location) as file:
                current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
        except yaml.YAMLError as error:
            logger.error(error)
            speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to read your location.")
            return

        address = current_location.get('address', {})
        city = address.get('city') or address.get('town') or address.get('hamlet') or 'Unknown'
        state = address.get('state', 'Unknown')
        lat = current_location['latitude']
        lon = current_location['longitude']
    weather_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,' \
                  f'hourly&appid={models.env.weather_api}'
    try:
        response = json.loads(urllib.request.urlopen(url=weather_url).read())  # loads the response in a json
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I ran into an exception. Please check your logs.")
        return

    weather_location = f'{city} {state}'.replace('None', '') if city != state else city or state

    if phrase and word_match(phrase=phrase,
                             match_list=['tomorrow', 'day after', 'next week', 'tonight', 'afternoon', 'evening']):
        # when the weather info was requested
        if 'tonight' in phrase:
            key = 0
            tell = 'tonight'
        elif 'day after' in phrase:
            key = 2
            tell = 'day after tomorrow'
        elif 'tomorrow' in phrase:
            key = 1
            tell = 'tomorrow'
        elif 'next week' in phrase:
            key = -1
            next_week = datetime.fromtimestamp(response['daily'][-1]['dt']).strftime("%A, %B %d")
            tell = f"on {' '.join(next_week.split()[:-1])} {inflect.engine().ordinal(next_week.split()[-1])}"
        else:
            key = 0
            tell = 'today'

        # which part of the day (after noon or noon is considered as full day as midday values range same as full day)
        if 'morning' in phrase:
            when = 'morn'
            tell += ' morning'
        elif 'evening' in phrase:
            when = 'eve'
            tell += ' evening'
        elif 'tonight' in phrase:
            when = 'night'
        elif 'night' in phrase:
            when = 'night'
            tell += ' night'
        else:
            when = 'day'
            tell += ''

        if 'alerts' in response:
            alerts = response['alerts'][0]['event']
            start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
            end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
        else:
            alerts, start_alert, end_alert = None, None, None
        during_key = response['daily'][key]
        condition = during_key['weather'][0]['description']
        high = int(temperature.k2f(during_key['temp']['max']))
        low = int(temperature.k2f(during_key['temp']['min']))
        temp_f = int(temperature.k2f(during_key['temp'][when]))
        temp_feel_f = int(temperature.k2f(during_key['feels_like'][when]))
        sunrise = datetime.fromtimestamp(during_key['sunrise']).strftime("%I:%M %p")
        sunset = datetime.fromtimestamp(during_key['sunset']).strftime("%I:%M %p")
        if 'sunrise' in phrase or 'sun rise' in phrase or ('sun' in phrase and 'rise' in phrase):
            if datetime.strptime(datetime.today().strftime("%I:%M %p"), "%I:%M %p") >= \
                    datetime.strptime(sunrise, "%I:%M %p"):
                tense = "will be"
            else:
                tense = "was"
            speaker.speak(text=f"{tell} in {weather_location}, sunrise {tense} at {sunrise}.")
            return
        if 'sunset' in phrase or 'sun set' in phrase or ('sun' in phrase and 'set' in phrase):
            if datetime.strptime(datetime.today().strftime("%I:%M %p"), "%I:%M %p") >= \
                    datetime.strptime(sunset, "%I:%M %p"):
                tense = "will be"
            else:
                tense = "was"
            speaker.speak(text=f"{tell} in {weather_location}, sunset {tense} at {sunset}")
            return
        output = f"The weather in {weather_location} {tell} would be {temp_f}\N{DEGREE SIGN}F, with a high of " \
                 f"{high}, and a low of {low}. "
        if temp_feel_f != temp_f:
            output += f"But due to {condition} it will fee like it is {temp_feel_f}\N{DEGREE SIGN}F. "
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
    if phrase:
        if 'sunrise' in phrase or 'sun rise' in phrase or ('sun' in phrase and 'rise' in phrase):
            if datetime.strptime(datetime.today().strftime("%I:%M %p"), "%I:%M %p") >= \
                    datetime.strptime(sunrise, "%I:%M %p"):
                tense = "will be"
            else:
                tense = "was"
            speaker.speak(text=f"In {weather_location}, sunrise {tense} at {sunrise}.")
            return
        if 'sunset' in phrase or 'sun set' in phrase or ('sun' in phrase and 'set' in phrase):
            if datetime.strptime(datetime.today().strftime("%I:%M %p"), "%I:%M %p") >= \
                    datetime.strptime(sunset, "%I:%M %p"):
                tense = "will be"
            else:
                tense = "was"
            speaker.speak(text=f"In {weather_location}, sunset {tense} at {sunset}")
            return
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
            output = f'The weather in {city} is {feeling} {temp_f}\N{DEGREE SIGN}, but due to the current wind ' \
                     f'conditions (which is {wind_speed} miles per hour), it feels like {temp_feel_f}\N{DEGREE SIGN}.' \
                     f' {weather_suggest}'
        else:
            output = f'The weather in {city} is {feeling} {temp_f}\N{DEGREE SIGN}, and it currently feels like ' \
                     f'{temp_feel_f}\N{DEGREE SIGN}. {weather_suggest}'
    else:
        output = f'The weather in {weather_location} is {temp_f}\N{DEGREE SIGN}F, with a high of {high}, and a low ' \
                 f'of {low}. It currently feels like {temp_feel_f}\N{DEGREE SIGN}F, and the current condition is ' \
                 f'{condition}. Sunrise at {sunrise}. Sunset at {sunset}.'
    if 'alerts' in response:
        alerts = response['alerts'][0]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
    else:
        alerts, start_alert, end_alert = None, None, None
    if alerts and start_alert and end_alert:
        output += f' You have a weather alert for {alerts} between {start_alert} and {end_alert}'
    speaker.speak(text=output)
