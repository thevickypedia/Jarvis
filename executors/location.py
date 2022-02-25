import math
import os
import re
import sys
import webbrowser
from difflib import SequenceMatcher
from pathlib import Path
from socket import gethostname
from ssl import create_default_context
from time import perf_counter
from typing import Tuple, Union

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

from executors import controls, logger
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.utils import globals, support

# stores necessary values for geolocation to receive the latitude, longitude and address
options.default_ssl_context = create_default_context(cafile=certifi.where())
geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)

env = globals.ENV


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
        devices_str = [{str(device).split(':')[0].strip(): str(device).split(':')[1].strip()} for device in devices]
        closest_match = [
            (SequenceMatcher(a=phrase, b=key).ratio() + SequenceMatcher(a=phrase, b=val).ratio()) / 2
            for device in devices_str for key, val in device.items()
        ]
        index = closest_match.index(max(closest_match))
        target_device = icloud_api.devices[index]
    else:
        target_device = [device for device in devices if device.get('name') == gethostname() or
                         gethostname() == device.get('name') + '.local'][0]
    return target_device if target_device else icloud_api.iphone


def location_services(device: AppleDevice) -> Union[None, Tuple[str or float, str or float, str]]:
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
        if not raw_location and sys._getframe(1).f_code.co_name == 'locate':  # noqa
            return 'None', 'None', 'None'
        elif not raw_location:
            raise PyiCloudAPIResponseException(reason=f'Unable to retrieve location for {device}')
        else:
            current_lat_, current_lon_ = raw_location['latitude'], raw_location['longitude']
        os.remove('pyicloud_error') if os.path.isfile('pyicloud_error') else None
    except (PyiCloudAPIResponseException, PyiCloudFailedLoginException) as error:
        if device:
            logger.logger.error(f'Unable to retrieve location::{error}')  # traceback
            caller = sys._getframe(1).f_code.co_name  # noqa
            if caller == '<module>':
                if os.path.isfile('pyicloud_error'):
                    logger.logger.error(f'Exception raised by {caller} once again. Proceeding...')
                    os.remove('pyicloud_error')
                else:
                    logger.logger.error(f'Exception raised by {caller}. Restarting.')
                    Path('pyicloud_error').touch()
                    controls.restart(quiet=True)  # Restarts quietly if the error occurs when called from __main__
        # uses latitude and longitude information from your IP's client when unable to connect to icloud
        st = Speedtest()
        current_lat_, current_lon_ = st.results.client['lat'], st.results.client['lon']
        speaker.speak(text="I have trouble accessing the i-cloud API, so I'll be using your I.P address to get your "
                           "location. Please note that this may not be accurate enough for location services.",
                      run=True)
    except ConnectionError:
        current_lat_, current_lon_ = None, None
        sys.stdout.write('\rBUMMER::Unable to connect to the Internet')
        speaker.speak(text="I was unable to connect to the internet. Please check your connection settings and retry.",
                      run=True)
        sys.stdout.write(f"\rMemory consumed: {support.size_converter(byte_size=0)}"
                         f"\nTotal runtime: {support.time_converter(seconds=perf_counter())}")
        support.terminator()

    try:
        # Uses the latitude and longitude information and converts to the required address.
        locator = geo_locator.reverse(f'{current_lat_}, {current_lon_}', language='en')
        return float(current_lat_), float(current_lon_), locator.raw['address']
    except (GeocoderUnavailable, GeopyError):
        logger.logger.error('Error retrieving address from latitude and longitude information. Initiating self reboot.')
        speaker.speak(text='Received an error while retrieving your address sir! I think a restart should fix this.')
        controls.restart()


def get_current_location():
    """Extracts location information from either an ``AppleDevice`` or the public IP address."""
    # todo: Write to a DB instead of dumping in an yaml file
    current_lat, current_lon, location_info = location_services(device=device_selector())
    current_tz = TimezoneFinder().timezone_at(lat=current_lat, lng=current_lon)
    with open('location.yaml', 'w') as location_writer:
        yaml.dump(data={'timezone': current_tz,
                        'latitude': current_lat, 'longitude': current_lon, 'address': location_info},
                  stream=location_writer, default_flow_style=False)


def location() -> None:
    """Gets the user's current location."""
    with open('location.yaml') as file:
        current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
    speaker.speak(text=f"You're at {current_location['address']['city']} "
                       f"{current_location['address']['state']}, "
                       f"in {current_location['address']['country']}")


def locate(phrase: str) -> None:
    """Locates an Apple device using icloud api for python.

    Args:
        phrase: Takes the voice recognized statement as argument and extracts device name from it.
    """
    if not (target_device := device_selector(phrase=phrase)):
        support.no_env_vars()
        return
    sys.stdout.write(f"\rLocating your {target_device}")
    target_device.play_sound()
    before_keyword, keyword, after_keyword = str(target_device).partition(':')  # partitions the hostname info
    if before_keyword == 'Accessory':
        after_keyword = after_keyword.replace("Vignesh’s", "").replace("Vignesh's", "").strip()
        speaker.speak(text=f"I've located your {after_keyword} sir!")
    else:
        speaker.speak(text=f"Your {before_keyword} should be ringing now sir!")
    speaker.speak(text="Would you like to get the location details?", run=True)
    phrase_location = listener.listen(timeout=3, phrase_limit=3)

    if phrase_location == 'SR_ERROR' and not any(word in phrase_location.lower() for word in keywords.ok):
        return

    ignore_lat, ignore_lon, location_info_ = location_services(target_device)
    lookup = str(target_device).split(':')[0].strip()
    if location_info_ == 'None':
        speaker.speak(text=f"I wasn't able to locate your {lookup} sir! It is probably offline.")
    else:
        post_code = '"'.join(list(location_info_['postcode'].split('-')[0]))
        iphone_location = f"Your {lookup} is near {location_info_['road']}, {location_info_['city']} " \
                          f"{location_info_['state']}. Zipcode: {post_code}, {location_info_['country']}"
        speaker.speak(text=iphone_location)
        stat = target_device.status()
        bat_percent = f"Battery: {round(stat['batteryLevel'] * 100)} %, " if stat['batteryLevel'] else ''
        device_model = stat['deviceDisplayName']
        phone_name = stat['name']
        speaker.speak(text=f"Some more details. {bat_percent} Name: {phone_name}, Model: {device_model}")
    if env.icloud_recovery:
        speaker.speak(text="I can also enable lost mode. Would you like to do it?", run=True)
        phrase_lost = listener.listen(timeout=3, phrase_limit=3)
        if any(word in phrase_lost.lower() for word in keywords.ok):
            message = 'Return my phone immediately.'
            target_device.lost_device(number=env.icloud_recovery, text=message)
            speaker.speak(text="I've enabled lost mode on your phone.")
        else:
            speaker.speak(text="No action taken sir!")


def distance(phrase):
    """Extracts the start and end location to get the distance for it.

    Args:
        phrase:Takes the phrase spoken as an argument.

    See Also:
        A loop differentiates between two-worded places and one-worded place.
        A condition below assumes two different words as two places but not including two words starting upper case
    right next to each other

    Examples:
        New York will be considered as one word and New York and Las Vegas will be considered as two words.
    """
    check = phrase.split()  # str to list
    places = []
    for word in check:
        if word[0].isupper() or '.' in word:  # looks for words that start with uppercase
            try:
                next_word = check[check.index(word) + 1]  # looks if words after an uppercase word is also one
                if next_word[0].isupper():
                    places.append(f"{word + ' ' + check[check.index(word) + 1]}")
                else:
                    if word not in ' '.join(places):
                        places.append(word)
            except IndexError:  # catches exception on lowercase word after an upper case word
                if word not in ' '.join(places):
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
        if globals.called_by_offline['status']:
            return
        speaker.speak(run=True)
        destination = listener.listen(timeout=3, phrase_limit=4)
        if destination != 'SR_ERROR':
            if len(destination.split()) > 2:
                speaker.speak(text="I asked for a destination sir, not a sentence. Try again.")
                distance_controller()
            if 'exit' in destination or 'quit' in destination or 'Xzibit' in destination:
                return

    if origin:
        # if starting_point is received gets latitude and longitude of that location
        desired_start = geo_locator.geocode(origin)
        sys.stdout.write(f"\r{desired_start.address} **")
        start = desired_start.latitude, desired_start.longitude
        start_check = None
    else:
        with open('location.yaml') as file:
            current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
        start = (current_location['latitude'], current_location['longitude'])
        start_check = 'My Location'
    sys.stdout.write("::TO::") if origin else sys.stdout.write("\r::TO::")
    desired_location = geo_locator.geocode(destination)
    if desired_location:
        end = desired_location.latitude, desired_location.longitude
    else:
        end = destination[0], destination[1]
    if not all(isinstance(v, float) for v in start) or not all(isinstance(v, float) for v in end):
        speaker.speak(text=f"I don't think {destination} exists sir!")
        return
    miles = round(geodesic(start, end).miles)  # calculates miles from starting point to destination
    sys.stdout.write(f"** {desired_location.address} - {miles}")
    if globals.called['directions']:
        # calculates drive time using d = s/t and distance calculation is only if location is same country
        globals.called['directions'] = False
        avg_speed = 60
        t_taken = miles / avg_speed
        if miles < avg_speed:
            drive_time = int(t_taken * 60)
            speaker.speak(text=f"It might take you about {drive_time} minutes to get there sir!")
        else:
            drive_time = math.ceil(t_taken)
            if drive_time == 1:
                speaker.speak(text=f"It might take you about {drive_time} hour to get there sir!")
            else:
                speaker.speak(text=f"It might take you about {drive_time} hours to get there sir!")
    elif start_check:
        speaker.speak(text=f"Sir! You're {miles} miles away from {destination}.")
        if not globals.called['locate_places']:
            speaker.speak(text=f"You may also ask where is {destination}")
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
        keyword = 'is'
        before_keyword, keyword, after_keyword = phrase.partition(keyword)
        place = after_keyword.replace(' in', '').strip()
    if not place:
        if globals.called_by_offline['status']:
            speaker.speak(text='I need a location to get you the details sir!')
            return
        speaker.speak(text="Tell me the name of a place!", run=True)
        converted = listener.listen(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            if 'exit' in converted or 'quit' in converted or 'Xzibit' in converted:
                return
            place = support.get_capitalized(phrase=converted)
            if not place:
                keyword = 'is'
                before_keyword, keyword, after_keyword = converted.partition(keyword)
                place = after_keyword.replace(' in', '').strip()

    with open('location.yaml') as file:
        current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
    try:
        destination_location = geo_locator.geocode(place)
        coordinates = destination_location.latitude, destination_location.longitude
        located = geo_locator.reverse(coordinates, language='en')
        data = located.raw
        address = data['address']
        county = address['county'] if 'county' in address else None
        city = address['city'] if 'city' in address.keys() else None
        state = address['state'] if 'state' in address.keys() else None
        country = address['country'] if 'country' in address else None
        if place in country:
            speaker.speak(text=f"{place} is a country")
        elif place in (city or county):
            speaker.speak(
                text=f"{place} is in {state}" if country == current_location['address']['country'] else
                f"{place} is in {state} in {country}")
        elif place in state:
            speaker.speak(text=f"{place} is a state in {country}")
        elif (city or county) and state and country:
            if country == current_location['address']['country']:
                speaker.speak(text=f"{place} is in {city or county}, {state}")
            else:
                speaker.speak(text=f"{place} is in {city or county}, {state}, in {country}")
        if globals.called_by_offline['status']:
            return
        globals.called['locate_places'] = True
    except (TypeError, AttributeError):
        speaker.speak(text=f"{place} is not a real place on Earth sir! Try again.")
        if globals.called_by_offline['status']:
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
    place = place.replace('I ', '').strip() if place else None
    if not place:
        speaker.speak(text="You might want to give a location.", run=True)
        converted = listener.listen(timeout=3, phrase_limit=4)
        if converted != 'SR_ERROR':
            place = support.get_capitalized(phrase=phrase)
            place = place.replace('I ', '').strip()
            if not place:
                if no_repeat:
                    return
                speaker.speak(text="I can't take you to anywhere without a location sir!")
                directions(phrase=None, no_repeat=True)
            if 'exit' in place or 'quit' in place or 'Xzibit' in place:
                return
    destination_location = geo_locator.geocode(place)
    if not destination_location:
        return
    try:
        coordinates = destination_location.latitude, destination_location.longitude
    except AttributeError:
        return
    located = geo_locator.reverse(coordinates, language='en')
    data = located.raw
    address = data['address']
    end_country = address['country'] if 'country' in address else None
    end = f"{located.latitude},{located.longitude}"

    with open('location.yaml') as file:
        current_location = yaml.load(stream=file, Loader=yaml.FullLoader)

    start_country = current_location['address']['country']
    start = current_location['latitude'], current_location['longitude']
    maps_url = f'https://www.google.com/maps/dir/{start}/{end}/'
    webbrowser.open(maps_url)
    speaker.speak(text="Directions on your screen sir!")
    if start_country and end_country:
        if re.match(start_country, end_country, flags=re.IGNORECASE):
            globals.called['directions'] = True
            distance_controller(origin=None, destination=place)
        else:
            speaker.speak(text="You might need a flight to get there!")
