import string
from datetime import datetime
from typing import Any, Dict, NoReturn, Optional, Tuple, Union

import inflect
import requests
from requests.models import PreparedRequest

from jarvis.executors import files, location, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support


def make_request(request: PreparedRequest) -> Union[Dict, NoReturn]:
    """Get weather information from OpenWeatherMap API.

    Args:
        request: Prepared request with URL and query params wrapped.

    Returns:
        dict:
        JSON response from api.
    """
    try:
        response = requests.get(url=request.url)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()
    except EgressErrors + (requests.JSONDecodeError,) as error:
        logger.error(error)


def weather_responder(coordinates: Dict[str, float]) -> 'make_request':
    """Get weather information via api call.

    Args:
        coordinates: GEO coordinates to prepare query params.

    Returns:
        'make_request':
        Returns the response from 'make_request'
    """
    # todo: preparing request has increased latency, work on alternate
    prepared_request = PreparedRequest()
    params = dict(**coordinates, **dict(exclude="minutely,hourly", appid=models.env.weather_api,
                                        units=models.env.temperature_unit))
    prepared_request.prepare_url(url="https://api.openweathermap.org/data/2.5/onecall", params=params)
    return make_request(request=prepared_request)
    # todo: investigate why `weather` endpoint doesn't return daily data
    # logger.info("Retrying with 'weather' endpoint")
    # prepared_request.prepare_url(url="https://api.openweathermap.org/data/2.5/weather", params=params)
    # return make_request(request=prepared_request)


def weather(phrase: str = None, monitor: bool = False) -> Union[Tuple[Any, int, int, int, Optional[str]], None]:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    References:
        - https://www.weather.gov/mlb/seasonal_wind_threat

    Args:
        phrase: Takes the phrase spoken as an argument.
        monitor: Takes a boolean value to simply return the weather response.
    """
    if not models.env.weather_api:
        logger.warning("Weather apikey not found.")
        support.no_env_vars()
        return

    place = None
    if phrase:
        # ignore days in week and the keywords for weather as they are guaranteed to not be places
        place = support.get_capitalized(phrase=phrase,
                                        ignore=support.days_in_week +
                                        tuple(string.capwords(w) for w in keywords.keywords.weather))
        phrase = phrase.lower()
    if place:
        logger.info("Identified place: %s", place)
        desired_location = location.geo_locator.geocode(place)
        if not desired_location:
            logger.error("Failed to get coordinates for the place: '%s'", place)
            speaker.speak(text=f"I'm sorry {models.env.title}! "
                               f"I wasn't able to get the weather information at {place}!")
            return
        coordinates = desired_location.latitude, desired_location.longitude
        located = location.geo_locator.reverse(coordinates, language='en')
        address = located.raw['address']
        city = address.get('city') or address.get('town') or address.get('hamlet') or 'Unknown'
        state = address.get('state', 'Unknown')
        lat = located.latitude
        lon = located.longitude
    else:
        current_location = files.get_location()
        address = current_location.get('address', {})
        city = address.get('city') or address.get('town') or address.get('hamlet') or 'Unknown'
        state = address.get('state', 'Unknown')
        lat = current_location['latitude']
        lon = current_location['longitude']
    if not (response := weather_responder(dict(lat=lat, lon=lon))):
        speaker.speak(text=f"I'm sorry {models.env.title}! I ran into an exception. Please check your logs.")
        return

    weather_location = f'{city} {state}'.replace('None', '') if city != state else city or state

    if phrase and word_match.word_match(phrase=phrase, match_list=('tomorrow', 'day after', 'next week',
                                                                   'tonight', 'afternoon', 'evening')):
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
        high = int(during_key['temp']['max'])
        low = int(during_key['temp']['min'])
        temp_f = int(during_key['temp'][when])
        temp_feel_f = int(during_key['feels_like'][when])
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
        output = f"The weather in {weather_location} {tell} would be " \
                 f"{temp_f}\N{DEGREE SIGN}{models.temperature_symbol}, " \
                 f"with a high of {high}, and a low of {low}. "
        if temp_feel_f != temp_f and condition not in ("clear sky", "broken clouds", "fog", "few clouds"):
            output += f"But due to {condition} it will fee like it is " \
                      f"{temp_feel_f}\N{DEGREE SIGN}{models.temperature_symbol}. "
        output += f"Sunrise at {sunrise}. Sunset at {sunset}. "
        if alerts and start_alert and end_alert:
            output += f'There is a weather alert for {alerts} between {start_alert} and {end_alert}'
        speaker.speak(text=output)
        return

    condition = response['current']['weather'][0]['description']
    high = int(response['daily'][0]['temp']['max'])
    low = int(response['daily'][0]['temp']['min'])
    temp_f = int(response['current']['temp'])
    temp_feel_f = int(response['current']['feels_like'])
    sunrise = datetime.fromtimestamp(response['daily'][0]['sunrise']).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(response['daily'][0]['sunset']).strftime("%I:%M %p")
    if monitor:
        if 'alerts' in response:
            alerts = response['alerts'][0]['event']
            start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%m-%d %H:%M")
            end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%m-%d %H:%M")
            alert = f'{string.capwords(alerts)} from {start_alert} to {end_alert}'
        else:
            alert = None
        return condition, high, low, temp_f, alert
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
        # open weather map returns wind speed as miles/hour if temperature is set to imperial, otherwise in metre/second
        # how is threshold determined? Refer: https://www.weather.gov/mlb/seasonal_wind_threat
        if models.env.temperature_unit == models.TemperatureUnits.IMPERIAL:
            wind_speed = response['current']['wind_speed']
            threshold = 25  # ~ equivalent for 40 kms
        else:
            wind_speed = response['current']['wind_speed'] * 3.6
            threshold = 40  # ~ equivalent for 25 miles
        if wind_speed > threshold:
            output = f'The weather in {city} is {feeling} {temp_f}\N{DEGREE SIGN}, but due to the current wind ' \
                     f'conditions (which is {wind_speed} {models.env.distance_unit} per hour), it feels like ' \
                     f'{temp_feel_f}\N{DEGREE SIGN}. {weather_suggest}'
        else:
            output = f'The weather in {city} is {feeling} {temp_f}\N{DEGREE SIGN}, and it currently feels like ' \
                     f'{temp_feel_f}\N{DEGREE SIGN}. {weather_suggest}'
    else:
        output = f'The weather in {weather_location} is ' \
                 f'{temp_f}\N{DEGREE SIGN}{models.temperature_symbol}, with a high of {high}, ' \
                 f'and a low of {low}. It currently feels like ' \
                 f'{temp_feel_f}\N{DEGREE SIGN}{models.temperature_symbol}, ' \
                 f'and the current condition is {condition}. Sunrise at {sunrise}. Sunset at {sunset}.'
    if 'alerts' in response:
        alerts = response['alerts'][0]['event']
        start_alert = datetime.fromtimestamp(response['alerts'][0]['start']).strftime("%I:%M %p")
        end_alert = datetime.fromtimestamp(response['alerts'][0]['end']).strftime("%I:%M %p")
        output += f' You have a weather alert for {alerts} between {start_alert} and {end_alert}'
    speaker.speak(text=output)
