"""**API Reference:** https://documenter.getpostman.com/view/6250319/RznBMzqo for Jaguar LandRover InControl API."""

import json
from logging import DEBUG, Logger, StreamHandler, getLogger
from os import environ
from time import time
from typing import Union
from urllib.error import HTTPError
from urllib.request import Request, build_opener
from uuid import UUID, uuid4


def logger_module() -> Logger:
    """Creates a custom logger using stream handler.

    Returns:
        Logger:
        Returns the logger module.
    """
    logger = getLogger(__name__)
    logger.addHandler(hdlr=StreamHandler())
    logger.setLevel(level=DEBUG)
    return logger


class Connect:
    """Initiates Connection object to connect to the Jaguar LandRover InControl Remote Car API.

    >>> Connect

    """

    IFAS_BASE_URL = "https://ifas.prod-row.jlrmotor.com/ifas/jlr"
    IFOP_BASE_URL = "https://ifop.prod-row.jlrmotor.com/ifop/jlr"
    IF9_BASE_URL = "https://if9.prod-row.jlrmotor.com/if9/jlr"

    def __init__(self, username: str = environ.get('USERNAME'), password: str = environ.get('PASSWORD'),
                 device_id: Union[UUID, str] = None, refresh_token=environ.get('TOKEN'),
                 china_servers: bool = False, logger: Logger = None, auth_expiry: int = 0):
        """Initiates all the class variables.

        Args:
            username: Login email address.
            password: Login password.
            device_id: Car's device ID. Defaults to UUID4.
            refresh_token: Token to login instead of email and password.
            china_servers: Boolean flag whether to use China servers.
            logger: Logger module. Defaults to logging using stream handler.
            auth_expiry: Duration (in seconds) to expire. Defaults to 0 forcing to re-authenticate.
        """
        if not device_id:
            device_id = uuid4()
        if not logger:
            logger = logger_module()

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
        self.logger = logger
        self.expiration = auth_expiry
        self.username = username

    def post_data(self, command: str, url: str, headers: dict, data: dict = None) -> dict:
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
        if time() > self.expiration:
            self.logger.debug('Authentication expired, reconnecting.')
            self.connect()
            if headers['Authorization']:
                headers['Authorization'] = self.head['Authorization']
        return self._open(url=f"{url}/{command}", headers=headers, data=data)

    def connect(self) -> None:
        """Authenticates device and establishes connection."""
        self.logger.debug("Connecting...")
        auth = self._authenticate(data=self.oauth)
        self._register_auth(auth=auth)
        if token := auth.get('access_token'):
            self._set_header(access_token=token)
            self.logger.debug("Authenticated")
            self._register_device_and_log_in()
        else:
            self.logger.error("Unauthenticated")

    def _register_device_and_log_in(self) -> None:
        """Registers device and log in the user."""
        self._register_device(headers=self.head)
        self.logger.debug(f"Device ID: {self.device_id} registered.")
        self._login_user(headers=self.head)
        self.logger.debug(f"User ID: {self.user_id} logged in.")

    def _open(self, url: str, headers: dict = None, data: dict = None) -> dict:
        """Open a connection to post the request.

        Args:
            url: URL to which the request has to be posted.
            headers: Headers for the request.
            data: Data to be posted.

        Returns:
            dict:
            JSON loaded response from post request.
        """
        request = Request(url=url, headers=headers)
        if data:
            request.data = bytes(json.dumps(data), encoding="utf8")

        response = build_opener().open(request)

        if not 200 <= response.code <= 300:
            raise HTTPError(code=response.code, msg='HTTPError', url=url, hdrs=response.headers, fp=response.fp)

        charset = response.info().get('charset', 'utf-8')
        if resp_data := response.read().decode(charset):
            return json.loads(resp_data)

    def _register_auth(self, auth: dict) -> None:
        """Assigns authentication header values to class variables.

        Args:
            auth: Takes the auth dictionary.
        """
        self.access_token = auth.get('access_token')
        self.expiration = time() + int(auth.get('expires_in', 0))
        self.auth_token = auth.get('authorization_token')
        self.refresh_token = auth.get('refresh_token')

    def _set_header(self, access_token: str) -> None:
        """Sets header.

        Args:
            access_token: Takes auth token to set the header as bearer.
        """
        self.head = {
            "Authorization": f"Bearer {access_token}",
            "X-Device-Id": self.device_id,
            "Content-Type": "application/json"
        }

    def _authenticate(self, data: dict = None) -> dict:
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
        return self._open(url=url, headers=auth_headers, data=data)

    def _register_device(self, headers: dict = None) -> dict:
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
        return self._open(url=url, headers=headers, data=data)

    def _login_user(self, headers: dict) -> dict:
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

        user_data = self._open(url, user_login_header)
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
        self.logger.debug("Tokens refreshed")
        self._register_device_and_log_in()

    def get_vehicles(self, headers: dict) -> dict:
        """Makes a post request to get the vehicles registered under the account.

        Args:
            headers: Headers for the post request.

        Returns:
            dict:
            Vehicles data.
        """
        url = f"{self.IF9_BASE_URL}/users/{self.user_id}/vehicles?primaryOnly=true"
        return self._open(url=url, headers=headers)

    def get_user_info(self) -> dict:
        """Makes a request to get the user information.

        Returns:
            dict:
            Returns user information.
        """
        return self.post_data(command=self.user_id, url=f"{self.IF9_BASE_URL}/users", headers=self.head)

    def update_user_info(self, user_info_data: dict) -> None:
        """Update user information to the profile.

        Args:
            user_info_data: User information to be posted in the post request.
        """
        headers = self.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json; charset=utf-8"
        self.post_data(command=self.user_id, url=f"{self.IF9_BASE_URL}/users", headers=headers,
                       data=user_info_data)

    def reverse_geocode(self, latitude: Union[float, str], longitude: Union[float, str]) -> dict:
        """Uses reverse geocoding to get the location from latitude and longitude.

        Args:
            latitude: Latitude of location.
            longitude: Longitude or location.

        Returns:
            dict:
            JSON loaded response from post request.
        """
        return self.post_data(command="en", url=f"{self.IF9_BASE_URL}/geocode/reverse/{latitude:.6f}/{longitude:.6f}",
                              headers=self.head)
