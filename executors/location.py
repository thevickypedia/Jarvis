import json
import math
import os
import pathlib
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from difflib import SequenceMatcher
from typing import NoReturn, Tuple, Union

import certifi
import yaml
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from pyicloud import PyiCloudService
from pyicloud.exceptions import (PyiCloudAPIResponseException,
                                 PyiCloudFailedLoginException)
from pyicloud.services.findmyiphone import AppleDevice
from speedtest import Speedtest
from timezonefinder import TimezoneFinder

from executors import controls
from executors.logger import logger
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.models import models
from modules.utils import shared, support

env = models.env
fileio = models.fileio

# stores necessary values for geolocation to receive the latitude, longitude and address
options.default_ssl_context = ssl.create_default_context(cafile=certifi.where())
geo_locator = Nominatim(scheme="http", user_agent="test/1", timeout=3)


def device_selector(phrase: str = None) -> Union[AppleDevice, None]:
    """Selects a device using the received input string.

    See Also:
        - Opens a html table with the index value and name of device.
        - When chosen an index value, the device name will be returned.

    Args:
        phrase: Takes the voice recognized statement as argument.

    Returns:
        AppleDevice:
        Returns the selected device from the class ``AppleDevice``
    """
    if not all([env.icloud_user, env.icloud_pass]):
        return
    icloud_api = PyiCloudService(env.icloud_user, env.icloud_pass)
    devices = [device for device in icloud_api.devices]
    if phrase:
        devices_str = [{str(device).split(":")[0].strip(): str(device).split(":")[1].strip()} for device in devices]
        closest_match = [
            (SequenceMatcher(a=phrase, b=key).ratio() + SequenceMatcher(a=phrase, b=val).ratio()) / 2
            for device in devices_str for key, val in device.items()
        ]
        index = closest_match.index(max(closest_match))
        target_device = icloud_api.devices[index]
    else:
        base_list = [device for device in devices if device.get("name") == socket.gethostname() or
                     socket.gethostname() == device.get("name") + ".local"] or devices
        target_device = base_list[0]
    return target_device if target_device else icloud_api.iphone


def get_coordinates_from_ip() -> Tuple[float, float]:
    """Uses public IP to retrieve latitude and longitude. If fails, uses ``Speedtest`` module.

    Returns:
        tuple:
        Returns latitude and longitude as a tuple.
    """
    try:
        info = json.load(urllib.request.urlopen(url="https://ipinfo.io/json"))
        coordinates = tuple(map(float, info.get('loc', '0,0').split(',')))
    except urllib.error.HTTPError as error:
        logger.error(error)
        coordinates = (0.0, 0.0)
    if coordinates == (0.0, 0.0):
        st = Speedtest()
        return float(st.results.client["lat"]), float(st.results.client["lon"])
    else:
        return coordinates


def get_location_from_coordinates(coordinates: tuple) -> Tuple[float, float, dict]:
    """Uses the latitude and longitude information to get the address information.

    Args:
        coordinates: Takes the latitude and longitude as a tuple.

    Returns:
        tuple:
        Latitude, Longitude, and Address.
    """
    try:
        locator = geo_locator.reverse(coordinates, language="en")
        return coordinates[0], coordinates[1], locator.raw["address"]
    except (GeocoderUnavailable, GeopyError) as error:
        logger.error(error)
        return coordinates[0], coordinates[1], {}


def location_services(device: AppleDevice) -> Union[NoReturn,
                                                    Tuple[str or float or None, str or float or None, str or None]]:
    """Gets the current location of an Apple device.

    Args:
        device: Passed when locating a particular Apple device.

    Returns:
        None or Tuple[str or float, str or float, str or float]:
        - On success, returns ``current latitude``, ``current longitude`` and ``location`` information as a ``dict``.
        - On failure, calls the ``restart()`` or ``terminator()`` function depending on the error.

    Raises:
        PyiCloudFailedLoginException: Restarts if occurs once. Uses location by IP, if occurs once again.
    """
    try:
        # tries with icloud api to get your device's location for precise location services
        if not device:
            if not (device := device_selector()):
                raise PyiCloudFailedLoginException
        raw_location = device.location()
        if not raw_location and sys._getframe(1).f_code.co_name == "locate":  # noqa
            return None, None, None
        elif not raw_location:
            raise PyiCloudAPIResponseException(reason=f"Unable to retrieve location for {device}")
        else:
            coordinates = raw_location["latitude"], raw_location["longitude"]
        os.remove("pyicloud_error") if os.path.isfile("pyicloud_error") else None
    except (PyiCloudAPIResponseException, PyiCloudFailedLoginException) as error:
        if device:
            logger.error(f"Unable to retrieve location::{error}")  # traceback
            caller = sys._getframe(1).f_code.co_name  # noqa
            if caller == "<module>":
                if os.path.isfile("pyicloud_error"):
                    logger.error(f"Exception raised by {caller} once again. Proceeding...")
                    os.remove("pyicloud_error")
                else:
                    logger.error(f"Exception raised by {caller}. Restarting.")
                    pathlib.Path("pyicloud_error").touch()
                    controls.restart_control(quiet=True)
        coordinates = get_coordinates_from_ip()
    except ConnectionError:
        coordinates = None, None
        sys.stdout.write("\rBUMMER::Unable to connect to the Internet")
        speaker.speak(text="I was unable to connect to the internet. Please check your connection settings and retry.",
                      run=True)
        sys.stdout.write(f"\rMemory consumed: {support.size_converter(byte_size=0)}"
                         f"\nTotal runtime: {support.time_converter(seconds=time.perf_counter())}")
        controls.terminator()

    if location_info := get_location_from_coordinates(coordinates=coordinates):
        return location_info
    else:
        logger.error("Error retrieving address from latitude and longitude information. Initiating self reboot.")
        speaker.speak(text=f"Received an error while retrieving your address {env.title}! "
                           "I think a restart should fix this.")
        controls.restart_control(quiet=True)


def write_current_location() -> NoReturn:
    """Extracts location information from public IP address and writes it to a yaml file."""
    current_lat, current_lon, location_info = get_location_from_coordinates(coordinates=get_coordinates_from_ip())
    current_tz = TimezoneFinder().timezone_at(lat=current_lat, lng=current_lon)
    logger.info(f"Writing location info in {fileio.location}")
    with open(fileio.location, 'w') as location_writer:
        yaml.dump(data={"timezone": current_tz, "latitude": current_lat, "longitude": current_lon,
                        "address": location_info},
                  stream=location_writer, default_flow_style=False)


def location() -> NoReturn:
    """Gets the user's current location."""
    with open(fileio.location) as file:
        current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
    speaker.speak(text=f"I'm at {current_location.get('address', {}).get('road', '')} - "
                       f"{current_location.get('address', {}).get('city', '')} "
                       f"{current_location.get('address', {}).get('state', '')} - "
                       f"in {current_location.get('address', {}).get('country', '')}")


def locate_device(target_device: AppleDevice) -> NoReturn:
    """Speaks the location information of the target device.

    Args:
        target_device: Takes the target device as an argument.
    """
    ignore_lat, ignore_lon, location_info_ = location_services(device=target_device)
    lookup = str(target_device).split(":")[0].strip()
    if not location_info_:
        speaker.speak(text=f"I wasn't able to locate your {lookup} {env.title}! It is probably offline.")
    else:
        if shared.called_by_offline:
            post_code = location_info_["postcode"].split("-")[0]
        else:
            post_code = '"'.join(list(location_info_["postcode"].split("-")[0]))
        iphone_location = f"Your {lookup} is near {location_info_['road']}, {location_info_['city']} " \
                          f"{location_info_['state']}. Zipcode: {post_code}, {location_info_['country']}"
        stat = target_device.status()
        bat_percent = f"Battery: {round(stat['batteryLevel'] * 100)} %, " if stat["batteryLevel"] else ""
        device_model = stat["deviceDisplayName"]
        phone_name = stat["name"]
        speaker.speak(text=f"{iphone_location}. Some more details. {bat_percent} Name: {phone_name}, "
                           f"Model: {device_model}")


def locate(phrase: str) -> None:
    """Locates an Apple device using icloud api for python.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts device name from it.
    """
    if not (target_device := device_selector(phrase=phrase)):
        support.no_env_vars()
        return
    if shared.called_by_offline:
        locate_device(target_device=target_device)
        return
    sys.stdout.write(f"\rLocating your {target_device}")
    target_device.play_sound()
    before_keyword, keyword, after_keyword = str(target_device).partition(":")  # partitions the hostname info
    if before_keyword == "Accessory":
        after_keyword = after_keyword.replace(f"{env.name}’s", "").replace(f"{env.name}'s", "").strip()
        speaker.speak(text=f"I've located your {after_keyword} {env.title}!")
    else:
        speaker.speak(text=f"Your {before_keyword} should be ringing now {env.title}!")
    speaker.speak(text="Would you like to get the location details?", run=True)
    phrase_location = listener.listen(timeout=3, phrase_limit=3)

    if phrase_location == "SR_ERROR":
        return
    elif not any(word in phrase_location.lower() for word in keywords.ok):
        return

    locate_device(target_device=target_device)
    if env.icloud_recovery:
        speaker.speak(text="I can also enable lost mode. Would you like to do it?", run=True)
        phrase_lost = listener.listen(timeout=3, phrase_limit=3)
        if any(word in phrase_lost.lower() for word in keywords.ok):
            target_device.lost_device(number=env.icloud_recovery, text="Return my phone immediately.")
            speaker.speak(text="I've enabled lost mode on your phone.")
        else:
            speaker.speak(text=f"No action taken {env.title}!")


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
        destination = listener.listen(timeout=3, phrase_limit=4)
        if destination != "SR_ERROR":
            if len(destination.split()) > 2:
                speaker.speak(text=f"I asked for a destination {env.title}, not a sentence. Try again.")
                distance_controller()
            if "exit" in destination or "quit" in destination or "Xzibit" in destination:
                return

    if origin:
        # if starting_point is received gets latitude and longitude of that location
        desired_start = geo_locator.geocode(origin)
        sys.stdout.write(f"\r{desired_start.address} **")
        start = desired_start.latitude, desired_start.longitude
        start_check = None
    else:
        with open(fileio.location) as file:
            current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
        start = (current_location["latitude"], current_location["longitude"])
        start_check = "My Location"
    sys.stdout.write("::TO::") if origin else sys.stdout.write("\r::TO::")
    desired_location = geo_locator.geocode(destination)
    if desired_location:
        end = desired_location.latitude, desired_location.longitude
    else:
        end = destination[0], destination[1]
    if not all(isinstance(v, float) for v in start) or not all(isinstance(v, float) for v in end):
        speaker.speak(text=f"I don't think {destination} exists {env.title}!")
        return
    miles = round(geodesic(start, end).miles)  # calculates miles from starting point to destination
    sys.stdout.write(f"** {desired_location.address} - {miles}")
    if shared.called["directions"]:
        # calculates drive time using d = s/t and distance calculation is only if location is same country
        shared.called["directions"] = False
        avg_speed = 60
        t_taken = miles / avg_speed
        if miles < avg_speed:
            drive_time = int(t_taken * 60)
            speaker.speak(text=f"It might take you about {drive_time} minutes to get there {env.title}!")
        else:
            drive_time = math.ceil(t_taken)
            if drive_time == 1:
                speaker.speak(text=f"It might take you about {drive_time} hour to get there {env.title}!")
            else:
                speaker.speak(text=f"It might take you about {drive_time} hours to get there {env.title}!")
    elif start_check:
        text = f"{env.title}! You're {miles} miles away from {destination}. "
        if not shared.called["locate_places"]:
            text += f"You may also ask where is {destination}"
        speaker.speak(text=text)
    else:
        speaker.speak(text=f"{origin} is {miles} miles away from {destination}.")
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
            speaker.speak(text=f"I need a location to get you the details {env.title}!")
            return
        speaker.speak(text="Tell me the name of a place!", run=True)
        converted = listener.listen(timeout=3, phrase_limit=4)
        if converted != "SR_ERROR":
            if "exit" in converted or "quit" in converted or "Xzibit" in converted:
                return
            place = support.get_capitalized(phrase=converted)
            if not place:
                keyword = "is"
                before_keyword, keyword, after_keyword = converted.partition(keyword)
                place = after_keyword.replace(" in", "").strip()

    with open(fileio.location) as file:
        current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
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
        speaker.speak(text=f"{place} is not a real place on Earth {env.title}! Try again.")
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
    place = support.get_capitalized(phrase=phrase)
    place = place.replace("I ", "").strip() if place else None
    if not place:
        speaker.speak(text="You might want to give a location.", run=True)
        converted = listener.listen(timeout=3, phrase_limit=4)
        if converted != "SR_ERROR":
            place = support.get_capitalized(phrase=phrase)
            place = place.replace("I ", "").strip()
            if not place:
                if no_repeat:
                    return
                speaker.speak(text=f"I can't take you to anywhere without a location {env.title}!")
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

    with open(fileio.location) as file:
        current_location = yaml.load(stream=file, Loader=yaml.FullLoader)

    start_country = current_location["address"]["country"]
    start = current_location["latitude"], current_location["longitude"]
    maps_url = f"https://www.google.com/maps/dir/{start}/{end}/"
    webbrowser.open(maps_url)
    speaker.speak(text=f"Directions on your screen {env.title}!")
    if start_country and end_country:
        if re.match(start_country, end_country, flags=re.IGNORECASE):
            shared.called["directions"] = True
            distance_controller(origin=None, destination=place)
        else:
            speaker.speak(text="You might need a flight to get there!")
