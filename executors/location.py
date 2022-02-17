import os
import sys
from datetime import datetime
from pathlib import Path
from ssl import create_default_context
from time import perf_counter
from typing import Tuple, Union

import certifi
import yaml
from geopy.exc import GeocoderUnavailable, GeopyError
from geopy.geocoders import Nominatim, options
from pyicloud.exceptions import (PyiCloudAPIResponseException,
                                 PyiCloudFailedLoginException)
from pyicloud.services.findmyiphone import AppleDevice
from timezonefinder import TimezoneFinder

from executors import custom_logger, internet, revive
from modules.audio import speaker
from modules.utils import globals, support

# stores necessary values for geolocation to receive the latitude, longitude and address
options.default_ssl_context = create_default_context(cafile=certifi.where())
geo_locator = Nominatim(scheme='http', user_agent='test/1', timeout=3)

st = internet.internet_checker()
env = globals.ENV


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
            if not (device := support.device_selector(icloud_user=env.icloud_user, icloud_pass=env.icloud_pass)):
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
        current_lat_ = st.results.client['lat']
        current_lon_ = st.results.client['lon']
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
            support.device_selector(icloud_user=env.icloud_user, icloud_pass=env.icloud_pass)
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
