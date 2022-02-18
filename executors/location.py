import os
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from socket import gethostname
from ssl import create_default_context
from time import perf_counter
from typing import Tuple, Union

import certifi
import yaml
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from pyicloud import PyiCloudService
from pyicloud.exceptions import (PyiCloudAPIResponseException,
                                 PyiCloudFailedLoginException)
from pyicloud.services.findmyiphone import AppleDevice
from speedtest import Speedtest
from timezonefinder import TimezoneFinder

from executors import custom_logger, revive
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.utils import globals, support

# stores necessary values for geolocation to receive the latitude, longitude and address
options.default_ssl_context = create_default_context(cafile=certifi.where())
geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)

env = globals.ENV


def device_selector(icloud_user: str, icloud_pass: str, phrase: str = None) -> Union[AppleDevice, None]:
    """Selects a device using the received input string.

    See Also:
        - Opens a html table with the index value and name of device.
        - When chosen an index value, the device name will be returned.

    Args:
        icloud_user: Username for Apple iCloud account.
        icloud_pass: Password for Apple iCloud account.
        phrase: Takes the voice recognized statement as argument.

    Returns:
        AppleDevice:
        Returns the selected device from the class ``AppleDevice``
    """
    if not all([icloud_user, icloud_pass]):
        return
    icloud_api = PyiCloudService(icloud_user, icloud_pass)
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
            if not (device := device_selector(icloud_user=env.icloud_user, icloud_pass=env.icloud_pass)):
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
            custom_logger.logger.error(f'Unable to retrieve location::{error}')  # traceback
            caller = sys._getframe(1).f_code.co_name  # noqa
            if caller == '<module>':
                if os.path.isfile('pyicloud_error'):
                    custom_logger.logger.error(f'Exception raised by {caller} once again. Proceeding...')
                    os.remove('pyicloud_error')
                else:
                    custom_logger.logger.error(f'Exception raised by {caller}. Restarting.')
                    Path('pyicloud_error').touch()
                    revive.restart(quiet=True)  # Restarts quietly if the error occurs when called from __main__
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
        custom_logger.logger.error('Error retrieving address from latitude and longitude information. '
                                   'Initiating self reboot.')
        speaker.speak(text='Received an error while retrieving your address sir! I think a restart should fix this.')
        revive.restart(quick=True)


def current_location():
    """Extracts location information from either an ``AppleDevice`` or the public IP address.

    See Also:
        Checks modified time of location.yaml (if exists) and uses the data only if it was modified less than 72 hours.
    """
    if os.path.isfile('location.yaml') and \
            int(datetime.now().timestamp()) - int(os.stat('location.yaml').st_mtime) < env.restart_interval + 300:
        location_details = yaml.load(open('location.yaml'), Loader=yaml.FullLoader)
        return {
            'current_lat': location_details['latitude'],
            'current_lon': location_details['longitude'],
            'location_info': location_details['address'],
            'current_tz': location_details['timezone']
        }
    else:
        current_lat, current_lon, location_info = location_services(
            device_selector(icloud_user=env.icloud_user, icloud_pass=env.icloud_pass)
        )
        current_tz = TimezoneFinder().timezone_at(lat=current_lat, lng=current_lon)
        with open('location.yaml', 'w') as location_writer:
            yaml.dump(data={'timezone': current_tz,
                            'latitude': current_lat, 'longitude': current_lon, 'address': location_info},
                      stream=location_writer, default_flow_style=False)
        return {
            'current_lat': current_lat,
            'current_lon': current_lon,
            'location_info': location_info,
            'current_tz': current_tz
        }


def location() -> None:
    """Gets the user's current location."""
    speaker.speak(text=f"You're at {globals.current_location_['location_info']['city']} "
                       f"{globals.current_location_['location_info']['state']}, "
                       f"in {globals.current_location_['location_info']['country']}")


def locate(phrase: str, no_repeat: bool = False) -> None:
    """Locates an Apple device using icloud api for python.

    Args:
        no_repeat: A placeholder flag switched during ``recursion`` so that, ``Jarvis`` doesn't repeat himself.
        phrase: Takes the voice recognized statement as argument and extracts device name from it.
    """
    if not (target_device := device_selector(icloud_user=env.icloud_user, icloud_pass=env.icloud_pass,
                                             phrase=phrase)):
        support.no_env_vars()
        return
    sys.stdout.write(f"\rLocating your {target_device}")
    if no_repeat:
        speaker.speak(text="Would you like to get the location details?")
    else:
        target_device.play_sound()
        before_keyword, keyword, after_keyword = str(target_device).partition(':')  # partitions the hostname info
        if before_keyword == 'Accessory':
            after_keyword = after_keyword.replace("Vignesh’s", "").replace("Vignesh's", "").strip()
            speaker.speak(text=f"I've located your {after_keyword} sir!")
        else:
            speaker.speak(text=f"Your {before_keyword} should be ringing now sir!")
        speaker.speak(text="Would you like to get the location details?")
    speaker.speak(run=True)
    phrase_location = listener.listen(timeout=3, phrase_limit=3)
    if phrase_location == 'SR_ERROR':
        if no_repeat:
            return
        speaker.speak(text="I didn't quite get that. Try again.")
        locate(phrase=phrase, no_repeat=True)
    else:
        if any(word in phrase_location.lower() for word in keywords.ok):
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
