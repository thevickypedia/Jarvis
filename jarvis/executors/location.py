import math
import os
import re
import ssl
import time
import webbrowser
from typing import Dict, NoReturn, Tuple, Union

import certifi
import yaml
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from speedtest import ConfigRetrievalError, Speedtest
from timezonefinder import TimezoneFinder

from jarvis.executors import files, internet
from jarvis.modules.audio import listener, speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support, util

# stores necessary values for geolocation to receive the latitude, longitude and address
options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())
geo_locator = Nominatim(scheme="http", user_agent="test/1", timeout=3)


def get_coordinates_from_ip() -> Union[Tuple[float, float], Tuple[float, ...]]:
    """Uses public IP to retrieve latitude and longitude. If fails, uses ``Speedtest`` module.

    Returns:
        tuple:
        Returns latitude and longitude as a tuple.
    """
    if (info := internet.public_ip_info()) and info.get('lcc'):
        return tuple(map(float, info.get('loc').split(',')))
    try:
        if results := Speedtest().results:
            return float(results.client["lat"]), float(results.client["lon"])
    except ConfigRetrievalError as error:
        logger.error(error)
        util.write_screen(text="Failed to get location based on IP. Hand modify it at "
                               f"'{os.path.abspath(models.fileio.location)}'")
        time.sleep(5)
    return 37.230881, -93.3710393  # Default to SGF latitude and longitude


def get_location_from_coordinates(coordinates: tuple) -> Dict[str, str]:
    """Uses the latitude and longitude information to get the address information.

    Args:
        coordinates: Takes the latitude and longitude as a tuple.

    Returns:
        dict:
        Location address.
    """
    try:
        locator = geo_locator.reverse(coordinates, language="en")
        return locator.raw["address"]
    except (GeocoderUnavailable, GeopyError) as error:
        logger.error(error)
        return {}


def write_current_location() -> NoReturn:
    """Extracts location information from public IP address and writes it to a yaml file."""
    data = files.get_location()
    address = data.get("address")
    if address and data.get("reserved") and data.get("latitude") and data.get("longitude") and \
            address.get("city", address.get("hamlet")) and address.get("country") and \
            address.get("state", address.get("county")):
        logger.info("%s is reserved.", models.fileio.location)
        logger.warning("Automatic location detection has been disabled!")
        return
    current_lat, current_lon = get_coordinates_from_ip()
    location_info = get_location_from_coordinates(coordinates=(current_lat, current_lon))
    current_tz = TimezoneFinder().timezone_at(lat=current_lat, lng=current_lon)
    logger.info("Writing location info in %s", models.fileio.location)
    with open(models.fileio.location, 'w') as location_writer:
        yaml.dump(data={"timezone": current_tz, "latitude": current_lat, "longitude": current_lon,
                        "address": location_info},
                  stream=location_writer, default_flow_style=False)


def location() -> NoReturn:
    """Gets the user's current location."""
    current_location = files.get_location()
    speaker.speak(text=f"I'm at {current_location.get('address', {}).get('road', '')} - "
                       f"{current_location.get('address', {}).get('city', '')} "
                       f"{current_location.get('address', {}).get('state', '')} - "
                       f"in {current_location.get('address', {}).get('country', '')}")


def distance(phrase) -> NoReturn:
    """Extracts the start and end location to get the distance for it.

    Args:
        phrase:Takes the phrase spoken as an argument.
    """
    check = phrase.split()  # str to list
    places = []
    for word in check:
        if word[0].isupper() or "." in word:  # looks for words that start with uppercase
            try:
                next_word = check[check.index(word) + 1]  # looks if words after an uppercase word is also one
                if next_word[0].isupper():
                    places.append(f"{word + ' ' + check[check.index(word) + 1]}")
                else:
                    if word not in " ".join(places):
                        places.append(word)
            except IndexError:  # catches exception on lowercase word after an upper case word
                if word not in " ".join(places):
                    places.append(word)

    if len(places) >= 2:
        start = places[0]
        end = places[1]
    elif len(places) == 1:
        start = None
        end = places[0]
    else:
        start, end = None, None
    distance_controller(start, end)


def distance_controller(origin: str = None, destination: str = None) -> None:
    """Calculates distance between two locations.

    Args:
        origin: Takes the starting place name as an optional argument.
        destination: Takes the destination place name as optional argument.

    Notes:
        - If ``origin`` is None, Jarvis takes the current location as ``origin``.
        - If ``destination`` is None, Jarvis will ask for a destination from the user.
    """
    if not destination:
        speaker.speak(text="Destination please?")
        if shared.called_by_offline:
            return
        speaker.speak(run=True)
        if destination := listener.listen():
            if len(destination.split()) > 2:
                speaker.speak(text=f"I asked for a destination {models.env.title}, not a sentence. Try again.")
                distance_controller()
            if "exit" in destination or "quit" in destination or "Xzibit" in destination:
                return

    if origin:
        # if starting_point is received gets latitude and longitude of that location
        desired_start = geo_locator.geocode(origin)
        start = desired_start.latitude, desired_start.longitude
        start_check = None
    else:
        current_location = files.get_location()
        start = (current_location["latitude"], current_location["longitude"])
        start_check = "My Location"
    desired_location = geo_locator.geocode(destination)
    if desired_location:
        end = desired_location.latitude, desired_location.longitude
    else:
        end = destination[0], destination[1]
    if not all(isinstance(v, float) for v in start) or not all(isinstance(v, float) for v in end):
        speaker.speak(text=f"I don't think {destination} exists {models.env.title}!")
        return
    if models.env.distance_unit == models.DistanceUnits.MILES:
        dist = round(geodesic(start, end).miles)  # calculates miles from starting point to destination
    else:
        dist = round(geodesic(start, end).kilometers)
    if shared.called["directions"]:
        # calculates drive time using d = s/t and distance calculation is only if location is same country
        shared.called["directions"] = False
        avg_speed = 60
        t_taken = dist / avg_speed
        if dist < avg_speed:
            drive_time = int(t_taken * 60)
            speaker.speak(text=f"It might take you about {drive_time} minutes to get there {models.env.title}!")
        else:
            drive_time = math.ceil(t_taken)
            if drive_time == 1:
                speaker.speak(text=f"It might take you about {drive_time} hour to get there {models.env.title}!")
            else:
                speaker.speak(text=f"It might take you about {drive_time} hours to get there {models.env.title}!")
    elif start_check:
        text = f"{models.env.title}! You're {dist} {models.env.distance_unit} away from {destination}. "
        if not shared.called["locate_places"]:
            text += f"You may also ask where is {destination}"
        speaker.speak(text=text)
    else:
        speaker.speak(text=f"{origin} is {dist} {models.env.distance_unit} away from {destination}.")
    return


def locate_places(phrase: str = None) -> None:
    """Gets location details of a place.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    place = support.get_capitalized(phrase=phrase) if phrase else None
    # if no words found starting with an upper case letter, fetches word after the keyword 'is' eg: where is Chicago
    if not place:
        keyword = "is"
        before_keyword, keyword, after_keyword = phrase.partition(keyword)
        place = after_keyword.replace(" in", "").strip()
    if not place:
        if shared.called_by_offline:
            speaker.speak(text=f"I need a location to get you the details {models.env.title}!")
            return
        speaker.speak(text="Tell me the name of a place!", run=True)
        if not (converted := listener.listen()) or "exit" in converted or "quit" in converted \
                or "Xzibit" in converted:
            return
        place = support.get_capitalized(phrase=converted)
        if not place:
            keyword = "is"
            before_keyword, keyword, after_keyword = converted.partition(keyword)
            place = after_keyword.replace(" in", "").strip()

    if not (current_location := files.get_location()):
        current_location = {"address": {"country": "United States"}}
    try:
        destination_location = geo_locator.geocode(place)
        coordinates = destination_location.latitude, destination_location.longitude
        located = geo_locator.reverse(coordinates, language="en")
        data = located.raw
        address = data["address"]
        county = address["county"] if "county" in address else None
        city = address["city"] if "city" in address.keys() else None
        state = address["state"] if "state" in address.keys() else None
        country = address["country"] if "country" in address else None
        if place in country:
            speaker.speak(text=f"{place} is a country")
        elif place in (city or county):
            speaker.speak(
                text=f"{place} is in {state}" if country == current_location["address"]["country"] else
                f"{place} is in {state} in {country}")
        elif place in state:
            speaker.speak(text=f"{place} is a state in {country}")
        elif (city or county) and state and country:
            if country == current_location["address"]["country"]:
                speaker.speak(text=f"{place} is in {city or county}, {state}")
            else:
                speaker.speak(text=f"{place} is in {city or county}, {state}, in {country}")
        if shared.called_by_offline:
            return
        shared.called["locate_places"] = True
    except (TypeError, AttributeError):
        speaker.speak(text=f"{place} is not a real place on Earth {models.env.title}! Try again.")
        if shared.called_by_offline:
            return
        locate_places(phrase=None)
    distance_controller(origin=None, destination=place)


def directions(phrase: str = None, no_repeat: bool = False) -> None:
    """Opens Google Maps for a route between starting and destination.

    Uses reverse geocoding to calculate latitude and longitude for both start and destination.

    Args:
        phrase: Takes the phrase spoken as an argument.
        no_repeat: A placeholder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
    """
    place = support.get_capitalized(phrase=phrase, ignore=("I ",))
    if not place:
        speaker.speak(text="You might want to give a location.", run=True)
        if converted := listener.listen():
            place = support.get_capitalized(phrase=converted, ignore=("I ",))
            if not place:
                if no_repeat:
                    return
                speaker.speak(text=f"I can't take you to anywhere without a location {models.env.title}!")
                directions(phrase=None, no_repeat=True)
            if "exit" in place or "quit" in place or "Xzibit" in place:
                return
    destination_location = geo_locator.geocode(place)
    if not destination_location:
        return
    try:
        coordinates = destination_location.latitude, destination_location.longitude
    except AttributeError:
        return
    located = geo_locator.reverse(coordinates, language="en")
    address = located.raw["address"]
    end_country = address["country"] if "country" in address else None
    end = f"{located.latitude},{located.longitude}"
    current_location = files.get_location()
    if not all((current_location.get('address'), current_location.get('latitude'), current_location.get('longitude'))):
        return
    start_country = current_location["address"]["country"]
    start = current_location["latitude"], current_location["longitude"]
    maps_url = f"https://www.google.com/maps/dir/{start}/{end}/"
    webbrowser.open(maps_url)
    speaker.speak(text=f"Directions on your screen {models.env.title}!")
    if start_country and end_country:
        if re.match(start_country, end_country, flags=re.IGNORECASE):
            shared.called["directions"] = True
            distance_controller(origin=None, destination=place)
        else:
            speaker.speak(text="You might need a flight to get there!")
