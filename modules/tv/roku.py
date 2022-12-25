from threading import Thread
from typing import Dict, List, NoReturn, Union
from xml.etree import ElementTree

import requests

from modules.exceptions import TVError
from modules.logger.custom_logger import logger


class TV:
    """Controller for Roku TV's.

    >>> TV

    References:
        https://developer.roku.com/docs/developer-program/debugging/external-control-api.md
    """

    PORT = 8060
    SESSION = requests.Session()

    def __init__(self, ip_address: str):
        """Instantiates the roku tv and makes a test call.

        Args:
            ip_address: IP address of the TV.
        """
        self.BASE_URL = f'http://{ip_address}:{self.PORT}'
        try:
            requests.get(url=self.BASE_URL)
        except requests.RequestException as error:
            logger.error(error)
            raise TVError

    def make_call(self, path, method) -> requests.Response:
        """Makes a session call using the path and method provided.

        Args:
            path: URL path to make the call.
            method: Method using which the call has to be made.

        Returns:
            requests.Response:
            Response from the session call.
        """
        if method == 'GET':
            return self.SESSION.get(url=self.BASE_URL + path)
        if method == 'POST':
            return self.SESSION.post(url=self.BASE_URL + path)

    def get_state(self) -> bool:
        """Gets the TV state to determine whether it is powered on or off.

        Returns:
            bool:
            True if powered on.
        """
        response = self.make_call(path='/query/device-info', method='GET')
        xml_parsed = ElementTree.fromstring(response.content)
        if xml_parsed.find('power-mode').text:
            return xml_parsed.find('power-mode').text == 'PowerOn'

    def startup(self) -> NoReturn:
        """Powers on the TV and launches Home screen."""
        self.make_call(path='/keypress/PowerOn', method='POST')
        self.make_call(path='/keypress/Home', method='POST')

    def shutdown(self) -> NoReturn:
        """Turns off the TV is it is powered on."""
        if self.get_state():
            self.make_call(path='/keypress/PowerOff', method='POST')

    def increase_volume(self, limit: int = 10) -> NoReturn:
        """Increases the volume on the TV.

        Args:
            limit: Number of iterations to increase the volume.
        """
        for _ in range(limit):
            self.make_call(path='/keypress/VolumeUp', method='POST')

    def decrease_volume(self, limit: int = 10) -> NoReturn:
        """Decreases the volume on the TV.

        Args:
            limit: Number of iterations to decrease the volume.
        """
        for _ in range(limit):
            self.make_call(path='/keypress/VolumeDown', method='POST')

    def mute(self) -> NoReturn:
        """Mutes the TV."""
        self.make_call(path='/keypress/VolumeMute', method='POST')

    def stop(self) -> NoReturn:
        """Sends a keypress to stop content on TV."""
        self.make_call(path='/keypress/Stop', method='POST')

    def pause(self) -> NoReturn:
        """Sends a keypress to pause content on TV."""
        self.make_call(path='/keypress/Pause', method='POST')

    def play(self) -> NoReturn:
        """Sends a keypress to play content on TV."""
        self.make_call(path='/keypress/Play', method='POST')

    def forward(self) -> NoReturn:
        """Sends a keypress to forward content on TV."""
        self.make_call(path='/keypress/Fwd', method='POST')

    def rewind(self) -> NoReturn:
        """Sends a keypress to rewind content on TV."""
        self.make_call(path='/keypress/Rev', method='POST')

    @staticmethod
    def get_sources() -> List[str]:
        """Returns a list of predetermined sources.

        Returns:
            list:
            Preset sources.
        """
        # todo: find a call to get this info
        return ['InputHDMI1', 'InputHDMI2', 'InputHDMI3', 'InputHDMI4', 'InputAV1']

    def set_source(self, val: str) -> NoReturn:
        """Set input source on TV.

        Args:
            val: Source name.
        """
        self.make_call(path=f'/keypress/{val}', method='POST')

    def _set_vol_executor(self, target) -> NoReturn:
        """Executed in thread to set volume to a specific level.

        With the lack of a better option, volume is decreased to zero and then increased to the required level.

        Args:
            target: Volume in percentage.
        """
        self.decrease_volume(limit=100)
        self.increase_volume(limit=target)

    def set_volume(self, target: int) -> NoReturn:
        """Initiates threaded volume setter.

        Args:
            target: Volume in percentage.
        """
        Thread(target=self._set_vol_executor, args=(target,)).start()

    def current_app(self) -> Union[str, None]:
        """Find current app running on the TV.

        Returns:
            str:
            Name of the application.
        """
        response = self.make_call(path='/query/active-app', method='GET')
        xml_parsed = ElementTree.fromstring(response.content)
        if not (app_info := xml_parsed.find('screensaver')):
            app_info = xml_parsed.find('app')
        if not app_info:
            return
        logger.debug(dict(id=app_info.get('id'), version=app_info.get('version'), name=app_info.text))
        return app_info.text

    @staticmethod
    def get_volume():
        """Get current volume on the TV. Placeholder method."""
        # todo: find a call to get this info
        return 'Unknown'

    def launch_app(self, app_name: str) -> NoReturn:
        """Launches an application on the TV.

        Args:
            app_name: Name of the application to launch.
        """
        # noinspection PyTypeChecker
        app_id = next((item for item in self.get_apps(raw=True)
                       if item['name'].lower() == app_name.lower()), {}).get('id')
        if app_id:
            response = self.make_call(path=f'/launch/{app_id}', method='POST')
            if not response.ok:
                logger.error(f'{response.status_code}: {response.text}')
        else:
            logger.error(f'{app_name} not found in tv')

    def get_apps(self, raw: bool = False) -> Union[List[str], List[Dict[str, str]]]:
        """Get list of applications installed on the TV.

        Args:
            raw: Takes a boolean flag if the entire dictionary has to be returned.

        Returns:
            list:
            List of app names.
        """
        response = self.make_call(path='/query/apps', method='GET')
        xml_parsed = ElementTree.fromstring(response.content)
        if raw:
            return [dict(id=node.get('id'), version=node.get('version'), name=node.text) for node in xml_parsed]
        return [node.text for node in xml_parsed]
