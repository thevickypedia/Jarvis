import os
import subprocess
from typing import NoReturn, Tuple, Union

import jinja2

from jarvis.executors.internet import get_connection_info
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.templates import templates

ERRORS: Tuple = (subprocess.CalledProcessError, subprocess.SubprocessError, FileNotFoundError,)


def process_err(error: Union[subprocess.CalledProcessError, subprocess.SubprocessError]) -> str:
    """Logs errors along with return code and output based on type of error.

    Args:
        error: Takes any one of multiple subprocess errors as argument.

    Returns:
        str:
        Decoded version of the error message or an empty string.
    """
    if isinstance(error, subprocess.CalledProcessError):
        result = error.output.decode(encoding='UTF-8').strip()
        logger.error(f"[{error.returncode}]: {result}")
        return result
    else:
        logger.error(error)
        return ""


class ControlConnection:
    """Wrapper for Wi-Fi connection.

    >>> ControlConnection

    """

    @staticmethod
    def darwin_connector() -> bool:
        """Connects to Wi-Fi using SSID and password in env vars for macOS."""
        if not os.path.exists("/System/Library/Frameworks/CoreWLAN.framework"):
            logger.error("WLAN framework not found.")
            return False

        import objc  # macOS specific

        logger.info(f'Scanning for {models.env.wifi_ssid} in WiFi range')

        try:
            # noinspection PyUnresolvedReferences
            objc.loadBundle('CoreWLAN',
                            bundle_path='/System/Library/Frameworks/CoreWLAN.framework',
                            module_globals=globals())
        except ImportError as error:
            logger.error(error)
            return False

        interface = CWInterface.interface()  # noqa
        networks, error = interface.scanForNetworksWithName_error_(models.env.wifi_ssid, None)
        if not networks:
            logger.error(f'Failed to detect the SSID: {models.env.wifi_ssid}')
            logger.error(error) if error else None
            return False

        network = networks.anyObject()
        success, error = interface.associateToNetwork_password_error_(network, models.env.wifi_password, None)
        if success:
            logger.info(f'Connected to {models.env.wifi_ssid}')
            return True
        elif error:
            logger.error(f'Unable to connect to {models.env.wifi_ssid}')
            logger.error(error)

    @staticmethod
    def linux_connector() -> bool:
        """Connects to Wi-Fi using SSID and password in env vars for Linux."""
        cmd = f"nmcli d wifi connect '{models.env.wifi_ssid}' password '{models.env.wifi_password}'"
        try:
            result = subprocess.check_output(cmd, shell=True)
        except ERRORS as error:
            process_err(error)
            return False
        logger.info(f'Connected to {models.env.wifi_ssid}')
        logger.debug(result.decode(encoding='UTF-8').strip())
        return True

    def win_connector(self) -> bool:
        """Connects to Wi-Fi using SSID and password in env vars for Windows."""
        logger.info(f'Connecting to {models.env.wifi_ssid} in WiFi range')
        command = "netsh wlan connect name=\"" + models.env.wifi_ssid + "\" ssid=\"" + models.env.wifi_ssid + \
                  "\" interface=Wi-Fi"
        try:
            output = subprocess.check_output(command, shell=True)
            result = output.decode(encoding="UTF-8").strip()
            logger.info(result)
        except ERRORS as error:
            result = process_err(error)
        if result == f'There is no profile "{models.env.wifi_ssid}" assigned to the specified interface.':
            return self.win_create_new_connection()
        elif result != "Connection request was completed successfully.":
            logger.critical(f"ATTENTION::{result}")
            return False
        return True

    @staticmethod
    def win_create_new_connection() -> bool:
        """Establish a new connection using a xml config for Windows."""
        logger.info(f"Establishing a new connection to {models.env.wifi_ssid}")
        command = "netsh wlan add profile filename=\"" + models.env.wifi_ssid + ".xml\"" + " interface=Wi-Fi"
        rendered = jinja2.Template(templates.generic.win_wifi_xml).render(WIFI_SSID=models.env.wifi_ssid,
                                                                          WIFI_PASSWORD=models.env.wifi_password)
        with open(f'{models.env.wifi_ssid}.xml', 'w') as file:
            file.write(rendered)
        try:
            result = subprocess.check_output(command, shell=True)
            logger.info(result.decode(encoding="UTF-8"))
            os.remove(f'{models.env.wifi_ssid}.xml')
            return True
        except ERRORS as error:
            process_err(error)
            os.remove(f'{models.env.wifi_ssid}.xml')

    def wifi_connector(self) -> bool:
        """Connects to the Wi-Fi SSID stored in env vars (OS-agnostic)."""
        if not models.env.wifi_ssid or not models.env.wifi_password:
            logger.warning("Cannot connect to Wi-Fi without SSID and password.")
            return False
        if models.settings.os == "Darwin":
            return self.darwin_connector()
        elif models.settings.os == "Windows":
            return self.win_connector()
        else:
            return self.linux_connector()


class ControlPeripheral:
    """Initiates ControlPeripheral to toggle Wi-Fi on or off.

    >>> ControlPeripheral

    """

    def __init__(self, name: str = None):
        self.name = name or get_connection_info(target='Name') or "Wi-Fi"

    @staticmethod
    def darwin_enable() -> NoReturn:
        """Enables Wi-Fi on macOS."""
        try:
            result = subprocess.check_output("networksetup -setairportpower airport on", shell=True)
            logger.info(' '.join(result.decode(encoding="UTF-8").splitlines()))
        except ERRORS as error:
            process_err(error)

    @staticmethod
    def darwin_disable() -> NoReturn:
        """Disables Wi-Fi on macOS."""
        try:
            result = subprocess.check_output("networksetup -setairportpower airport off", shell=True)
            logger.info(' '.join(result.decode(encoding="UTF-8").splitlines()))
        except ERRORS as error:
            process_err(error)

    @staticmethod
    def linux_enable() -> NoReturn:
        """Enables Wi-Fi on Linux."""
        try:
            result = subprocess.run("nmcli radio wifi on", shell=True)
            if result.returncode:
                logger.error("Failed to enable Wi-Fi")
            else:
                logger.info("Wi-Fi has been enabled.")
            return result.returncode == 0
        except ERRORS as error:
            process_err(error)

    @staticmethod
    def linux_disable() -> NoReturn:
        """Disables Wi-Fi on Linux."""
        try:
            result = subprocess.run("nmcli radio wifi on", shell=True)
            if result.returncode:
                logger.error("Failed to disable Wi-Fi")
            else:
                logger.info("Wi-Fi has been disabled.")
            return result.returncode == 0
        except ERRORS as error:
            process_err(error)

    def win_enable(self) -> NoReturn:
        """Enables Wi-Fi on Windows."""
        try:
            result = subprocess.check_output(f"netsh interface set interface {self.name!r} enabled", shell=True)
            result = result.decode(encoding="UTF-8").strip()
            if result:
                logger.warning(result)
            else:
                logger.info(f"{self.name} has been enabled.")
        except ERRORS as error:
            process_err(error)

    def win_disable(self) -> NoReturn:
        """Disables Wi-Fi on Windows."""
        try:
            result = subprocess.check_output(f"netsh interface set interface {self.name!r} disabled", shell=True)
            result = result.decode(encoding="UTF-8").strip()
            if result:
                logger.warning(result)
            else:
                logger.info(f"{self.name} has been disabled.")
        except ERRORS as error:
            process_err(error)

    def enable(self) -> NoReturn:
        """Enable Wi-Fi (OS-agnostic)."""
        if models.settings.os == "Darwin":
            self.darwin_enable()
        elif models.settings.os == "Windows":
            self.win_enable()
        else:
            self.linux_enable()

    def disable(self) -> NoReturn:
        """Disable Wi-Fi (OS-agnostic)."""
        if models.settings.os == "Darwin":
            self.darwin_disable()
        elif models.settings.os == "Windows":
            self.win_disable()
        else:
            self.linux_enable()
