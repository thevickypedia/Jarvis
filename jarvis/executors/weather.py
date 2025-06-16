import string
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

from jarvis.executors import files, location, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support


def make_request(lat: float, lon: float) -> Dict | None:
    """Get weather information from OpenWeatherMap API.

    Args:
        lat: Latitude of location to get weather info.
        lon: Longitude of location to get weather info.

    Returns:
        dict:
        JSON response from api.
    """
    query_string = urlencode(
        OrderedDict(
            lat=lat,
            lon=lon,
            exclude="minutely,hourly",
            appid=models.env.weather_apikey,
            units=models.env.temperature_unit.value,
        )
    )
    url = str(models.env.weather_endpoint) + "?" + query_string
    try:
        response = requests.get(url=url)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()
    except (EgressErrors, requests.JSONDecodeError) as error:
        logger.error(error)


def weather_with_specifics(
    phrase: str, response: Dict[str, Any], weather_location: str
) -> None:
    """Parses the weather information in depth when requested for a specific timeline.

    Args:
        phrase: Takes the phrase spoken as an argument.
        response: Response payload from openweather API.
        weather_location: Weather location parsed from the phrase.
    """
    if "tonight" in phrase:
        idx = 0
        tell = "tonight"
    elif "day after" in phrase:
        idx = 2
        tell = "day after tomorrow"
    elif "tomorrow" in phrase:
        idx = 1
        tell = "tomorrow"
    elif "next week" in phrase:
        idx = -1
        next_week = datetime.fromtimestamp(response["daily"][-1]["dt"]).strftime(
            "%A, %B %d"
        )
        tell = f"on {' '.join(next_week.split()[:-1])} {support.ENGINE.ordinal(next_week.split()[-1])}"
    else:
        idx = 0
        tell = "today"

    # which part of the day (after noon or noon is considered as full day as midday values range same as full day)
    if "morning" in phrase:
        when = "morn"
        tell += " morning"
    elif "evening" in phrase:
        when = "eve"
        tell += " evening"
    elif "tonight" in phrase:
        when = "night"
    elif "night" in phrase:
        when = "night"
        tell += " night"
    else:
        when = "day"
        tell += ""

    if "alerts" in response:
        alerts = response["alerts"][0]["event"]
        start_alert = datetime.fromtimestamp(response["alerts"][0]["start"]).strftime(
            "%I:%M %p"
        )
        end_alert = datetime.fromtimestamp(response["alerts"][0]["end"]).strftime(
            "%I:%M %p"
        )
    else:
        alerts, start_alert, end_alert = None, None, None
    indexed_response = response["daily"][idx]
    condition = indexed_response["weather"][0]["description"]
    high = int(indexed_response["temp"]["max"])
    low = int(indexed_response["temp"]["min"])
    temp_f = int(indexed_response["temp"][when])
    temp_feel_f = int(indexed_response["feels_like"][when])
    sunrise = datetime.fromtimestamp(indexed_response["sunrise"]).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(indexed_response["sunset"]).strftime("%I:%M %p")
    if (
        "sunrise" in phrase
        or "sun rise" in phrase
        or ("sun" in phrase and "rise" in phrase)
    ):
        if datetime.strptime(
            datetime.today().strftime("%I:%M %p"), "%I:%M %p"
        ) >= datetime.strptime(sunrise, "%I:%M %p"):
            tense = "will be"
        else:
            tense = "was"
        speaker.speak(
            text=f"{tell} in {weather_location}, sunrise {tense} at {sunrise}."
        )
        return
    if (
        "sunset" in phrase
        or "sun set" in phrase
        or ("sun" in phrase and "set" in phrase)
    ):
        if datetime.strptime(
            datetime.today().strftime("%I:%M %p"), "%I:%M %p"
        ) >= datetime.strptime(sunset, "%I:%M %p"):
            tense = "will be"
        else:
            tense = "was"
        speaker.speak(text=f"{tell} in {weather_location}, sunset {tense} at {sunset}")
        return
    output = (
        f"The weather in {weather_location} {tell} would be "
        f"{temp_f}\N{DEGREE SIGN}{models.temperature_symbol}, "
        f"with a high of {high}, and a low of {low}. "
    )
    if temp_feel_f != temp_f and condition not in (
        "clear sky",
        "broken clouds",
        "fog",
        "few clouds",
    ):
        output += (
            f"But due to {condition} it will fee like it is "
            f"{temp_feel_f}\N{DEGREE SIGN}{models.temperature_symbol}. "
        )
    output += f"Sunrise at {sunrise}. Sunset at {sunset}. "
    if alerts and start_alert and end_alert:
        output += f"There is a weather alert for {alerts} between {start_alert} and {end_alert}"
    speaker.speak(text=output)


def weather(
    phrase: str = None, monitor: bool = False
) -> Tuple[Any, int, int, int, Optional[str]] | None:
    """Says weather at any location if a specific location is mentioned.

    Says weather at current location by getting IP using reverse geocoding if no place is received.

    References:
        - https://www.weather.gov/mlb/seasonal_wind_threat

    Args:
        phrase: Takes the phrase spoken as an argument.
        monitor: Takes a boolean value to simply return the weather response.
    """
    if not models.env.weather_apikey:
        logger.warning("Weather apikey not found.")
        support.no_env_vars()
        return

    place = None
    if phrase:
        # ignore days in week and the keywords for weather as they are guaranteed to not be places
        place = support.get_capitalized(
            phrase=phrase,
            ignore=support.days_in_week
            + tuple(string.capwords(w) for w in keywords.keywords["weather"]),
        )
        phrase = phrase.lower()
    if place:
        logger.info("Identified place: %s", place)
        desired_location = location.geo_locator.geocode(place)
        if not desired_location:
            logger.error("Failed to get coordinates for the place: '%s'", place)
            speaker.speak(
                text=f"I'm sorry {models.env.title}! "
                f"I wasn't able to get the weather information at {place}!"
            )
            return
        coordinates = desired_location.latitude, desired_location.longitude
        located = location.geo_locator.reverse(coordinates, language="en")
        address = located.raw["address"]
        city = (
            address.get("city")
            or address.get("town")
            or address.get("hamlet")
            or "Unknown"
        )
        state = address.get("state", "Unknown")
        lat = located.latitude
        lon = located.longitude
    else:
        current_location = files.get_location()
        address = current_location.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("hamlet")
            or "Unknown"
        )
        state = address.get("state", "Unknown")
        lat = current_location["latitude"]
        lon = current_location["longitude"]
    if not (response := make_request(lat=lat, lon=lon)):
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I ran into an exception. Please check your logs."
        )
        return

    weather_location = (
        f"{city} {state}".replace("None", "") if city != state else city or state
    )

    not_current = word_match.word_match(
        phrase=phrase,
        match_list=(
            "tomorrow",
            "day after",
            "next week",
            "tonight",
            "afternoon",
            "evening",
        ),
    )
    if not_current and models.settings.weather_onecall:
        weather_with_specifics(phrase, response, weather_location)
        return
    elif not_current:
        speaker.speak(
            f"I'm sorry {models.env.title}! The API endpoint is only set to retrieve the current weather."
        )
        return

    # todo: the onecall endpoint is untested
    if models.settings.weather_onecall:
        condition = response["current"]["weather"][0]["description"]
        high = int(response["daily"][0]["temp"]["max"])
        low = int(response["daily"][0]["temp"]["min"])
        temp_f = int(response["current"]["temp"])
        temp_feel_f = int(response["current"]["feels_like"])
        sunrise = datetime.fromtimestamp(response["daily"][0]["sunrise"]).strftime(
            "%I:%M %p"
        )
    else:
        condition = response["weather"][0]["description"]
        high = int(response["main"]["temp_max"])
        low = int(response["main"]["temp_min"])
        temp_f = int(response["main"]["temp"])
        temp_feel_f = int(response["main"]["feels_like"])
        sunrise = datetime.fromtimestamp(response["sys"]["sunrise"]).strftime(
            "%I:%M %p"
        )
    sunset = datetime.fromtimestamp(response["sys"]["sunset"]).strftime("%I:%M %p")
    if monitor:
        if "alerts" in response:
            alerts = response["alerts"][0]["event"]
            start_alert = datetime.fromtimestamp(
                response["alerts"][0]["start"]
            ).strftime("%m-%d %H:%M")
            end_alert = datetime.fromtimestamp(response["alerts"][0]["end"]).strftime(
                "%m-%d %H:%M"
            )
            alert = f"{string.capwords(alerts)} from {start_alert} to {end_alert}"
        else:
            alert = None
        return condition, high, low, temp_f, alert
    if phrase:
        if (
            "sunrise" in phrase
            or "sun rise" in phrase
            or ("sun" in phrase and "rise" in phrase)
        ):
            if datetime.strptime(
                datetime.today().strftime("%I:%M %p"), "%I:%M %p"
            ) >= datetime.strptime(sunrise, "%I:%M %p"):
                tense = "will be"
            else:
                tense = "was"
            speaker.speak(text=f"In {weather_location}, sunrise {tense} at {sunrise}.")
            return
        if (
            "sunset" in phrase
            or "sun set" in phrase
            or ("sun" in phrase and "set" in phrase)
        ):
            if datetime.strptime(
                datetime.today().strftime("%I:%M %p"), "%I:%M %p"
            ) >= datetime.strptime(sunset, "%I:%M %p"):
                tense = "will be"
            else:
                tense = "was"
            speaker.speak(text=f"In {weather_location}, sunset {tense} at {sunset}")
            return
    output = (
        f"The weather in {weather_location} is "
        f"{temp_f}\N{DEGREE SIGN}{models.temperature_symbol}, with a high of {high}, "
        f"and a low of {low}. It currently feels like "
        f"{temp_feel_f}\N{DEGREE SIGN}{models.temperature_symbol}, "
        f"and the current condition is {condition}. Sunrise at {sunrise}. Sunset at {sunset}."
    )
    if "alerts" in response:
        alerts = response["alerts"][0]["event"]
        start_alert = datetime.fromtimestamp(response["alerts"][0]["start"]).strftime(
            "%I:%M %p"
        )
        end_alert = datetime.fromtimestamp(response["alerts"][0]["end"]).strftime(
            "%I:%M %p"
        )
        output += f" You have a weather alert for {alerts} between {start_alert} and {end_alert}"
    speaker.speak(text=output)
