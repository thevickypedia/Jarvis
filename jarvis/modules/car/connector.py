# noinspection PyUnresolvedReferences
"""Module to handle connections on JLR vehicles.

>>> Connector

See Also:
    **API Reference:** https://documenter.getpostman.com/view/6250319/RznBMzqo for Jaguar LandRover InControl API.
"""

import json
import time
from typing import Dict, NoReturn, Union
from uuid import UUID, uuid4

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from jarvis.modules.logger.custom_logger import logger

SESSION = requests.Session()
RETRY = Retry(connect=3, backoff_factor=1.5)
ADAPTER = HTTPAdapter(max_retries=RETRY)
SESSION.mount('http://', adapter=ADAPTER)
SESSION.mount('https://', adapter=ADAPTER)
SESSION.headers = {}  # Headers can't be set to SESSION as they change for each call


def _open(url: str, headers: dict = None, data: dict = None) -> Dict:
    """Open a connection to post the request.

    Args:
        url: URL to which the request has to be posted.
        headers: Headers for the request.
        data: Data to be posted.

    Returns:
        dict:
        JSON loaded response from post request.
    """
    if data:
        if data.get('grant_type', '') == 'password':
            headers['Connection'] = 'close'
        response = SESSION.post(url=url, headers=headers, data=bytes(json.dumps(data), "utf-8"))
    else:
        response = SESSION.get(url=url, headers=headers)
    if not response.ok:
        logger.debug("Response: %d", response.status_code)
        response.raise_for_status()
    # not all functions return a JSON response and I don't have an EV to test which does and which doesn't so ¯\_(ツ)_/¯
    try:
        return response.json()
    except json.JSONDecodeError as error:
        logger.debug(error)


class Connect:
    """Initiates Connection object to connect to the Jaguar LandRover InControl Remote Car API.

    >>> Connect

    """

    IFAS_BASE_URL = "https://ifas.prod-row.jlrmotor.com/ifas/jlr"
    IFOP_BASE_URL = "https://ifop.prod-row.jlrmotor.com/ifop/jlr"
    IF9_BASE_URL = "https://if9.prod-row.jlrmotor.com/if9/jlr"

    def __init__(self, username: str, password: str = None, device_id: Union[UUID, str] = None,
                 refresh_token: Union[UUID, str] = None, auth_expiry: Union[int, float] = 0,
                 china_servers: bool = False):
        """Initiates all the class variables.

        Args:
            username: Login email address.
            password: Login password.
            device_id: Car's device ID. Defaults to UUID4.
            refresh_token: Token to login instead of email and password.
            china_servers: Boolean flag to use China servers.
            auth_expiry: Duration (in seconds) to expire. Defaults to 0 forcing to re-authenticate.
        """
        if not device_id:
            device_id = uuid4()

        if china_servers:
            self.IFAS_BASE_URL = "https://ifas.prod-chn.jlrmotor.com/ifas/jlr"
            self.IFOP_BASE_URL = "https://ifop.prod-chn.jlrmotor.com/ifop/jlr"
            self.IF9_BASE_URL = "https://ifoa.prod-chn.jlrmotor.com/if9/jlr"

        if refresh_token:
            self.oauth = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        else:
            self.oauth = {
                "grant_type": "password",
                "username": username,
                "password": password
            }

        self.head = {}
        self.device_id = str(device_id)
        self.expiration = auth_expiry
        self.username = username

    def post_data(self, command: str, url: str, headers: dict, data: dict = None) -> Dict:
        """Add header authorization and sends a post request.

        Args:
            command: Command to frame the URL.
            url: Base URL and its extension.
            headers: Headers to passed.
            data: Data for post request.

        Returns:
            dict:
            JSON loaded response from post request.
        """
        if headers:
            headers = {**self.head.copy(), **headers}
        else:
            headers = self.head.copy()
        if time.time() > self.expiration:
            logger.warning('Authentication expired, reconnecting.')
            self.connect()
            if headers.get('Authorization'):
                headers['Authorization'] = self.head['Authorization']
        return _open(url=f"{url}/{command}", headers=headers, data=data)

    def connect(self) -> NoReturn:
        """Authenticates device and establishes connection."""
        logger.debug("Connecting...")
        auth = self._authenticate(data=self.oauth)
        self._register_auth(auth=auth)
        if token := auth.get('access_token'):
            self._set_header(access_token=token)
            logger.debug("Authenticated")
            self._register_device_and_log_in()
        else:
            logger.error("Unauthenticated")

    def _register_device_and_log_in(self) -> NoReturn:
        """Registers device and log in the user."""
        self._register_device(headers=self.head)
        logger.debug("Device ID: %s registered.", self.device_id)
        self._login_user(headers=self.head)
        logger.debug("User ID: %s logged in.", self.user_id)

    def _register_auth(self, auth: dict) -> NoReturn:
        """Assigns authentication header values to class variables.

        Args:
            auth: Takes the auth dictionary.
        """
        self.access_token = auth.get('access_token')
        self.expiration = time.time() + int(auth.get('expires_in', 0))
        self.auth_token = auth.get('authorization_token')
        self.refresh_token = auth.get('refresh_token')

    def _set_header(self, access_token: str) -> NoReturn:
        """Sets header.

        Args:
            access_token: Takes auth token to set the header as bearer.
        """
        self.head = {
            "Authorization": f"Bearer {access_token}",
            "X-Device-Id": self.device_id,
            "Content-Type": "application/json"
        }

    def _authenticate(self, data: dict = None) -> Dict:
        """Makes a post call to the tokens end point.

        Args:
            data: Data to be posted.

        Returns:
            dict:
            JSON loaded response from post request.
        """
        url = f"{self.IFAS_BASE_URL}/tokens"
        auth_headers = {
            "Authorization": "Basic YXM6YXNwYXNz",
            "Content-Type": "application/json",
            "X-Device-Id": self.device_id
        }
        return _open(url=url, headers=auth_headers, data=data)

    def _register_device(self, headers: dict = None) -> Dict:
        """Frames the url and data to post to register the device.

        Args:
            headers: Headers to be added to register device.

        Returns:
            dict:
            JSON loaded response from post request.
        """
        url = f'{self.IFOP_BASE_URL}/users/{self.username}/clients'
        data = {
            "access_token": self.access_token,
            "authorization_token": self.auth_token,
            "expires_in": "86400",
            "deviceID": self.device_id
        }
        return _open(url=url, headers=headers, data=data)

    def _login_user(self, headers: dict) -> Dict:
        """Login the user.

        Args:
            headers: Headers to be passed.

        Returns:
            dict:
            Returns the user data.
        """
        url = f"{self.IF9_BASE_URL}/users?loginName={self.username}"
        user_login_header = headers.copy()
        user_login_header["Accept"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json"

        user_data = _open(url, user_login_header)
        self.user_id = user_data.get('userId')
        return user_data

    def refresh_tokens(self):
        """Refresh the token, register the device and login."""
        self.oauth = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        auth = self._authenticate(self.oauth)
        self._register_auth(auth)
        self._set_header(auth['access_token'])
        logger.debug("Tokens refreshed")
        self._register_device_and_log_in()

    def get_vehicles(self, headers: dict) -> Dict:
        """Makes a post request to get the vehicles registered under the account.

        Args:
            headers: Headers for the post request.

        Returns:
            dict:
            Vehicles data.
        """
        url = f"{self.IF9_BASE_URL}/users/{self.user_id}/vehicles?primaryOnly=true"
        return _open(url=url, headers=headers)

    def get_user_info(self) -> Dict:
        """Makes a request to get the user information.

        Returns:
            dict:
            Returns user information.
        """
        return self.post_data(command=self.user_id, url=f"{self.IF9_BASE_URL}/users", headers=self.head)

    def update_user_info(self, user_info_data: dict) -> NoReturn:
        """Update user information to the profile.

        Args:
            user_info_data: User information to be posted in the post request.
        """
        headers = self.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json; charset=utf-8"
        self.post_data(command=self.user_id, url=f"{self.IF9_BASE_URL}/users", headers=headers,
                       data=user_info_data)
