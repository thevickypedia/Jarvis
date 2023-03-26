import os
import socket
import time
from http.client import HTTPSConnection
from typing import NoReturn

from pywifi import ControlConnection, ControlPeripheral

from jarvis.executors import controls
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models


def wifi_connector() -> NoReturn:
    """Checks for internet connection as per given frequency. Enables Wi-Fi and connects to SSID if connection fails.

    See Also:
        - Logs up to 5 unknown errors before restarting process.
    """
    # processName filter is not added since process runs on a single function that is covered by funcName
    config.multiprocessing_logger(filename=os.path.join('logs', 'wifi_connector_%d-%m-%Y.log'))
    if not models.env.wifi_ssid or not models.env.wifi_password:
        logger.warning("Cannot retry connections without SSID and password.")
        return

    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.info("Initiating scan for wifi connectivity.")
    unknown_errors = 0
    while True:
        try:
            if models.settings.os == models.supported_platforms.windows:
                connection = HTTPSConnection("8.8.8.8", timeout=5)  # Recreate a new connection everytime
                connection.request("HEAD", "/")
            else:
                socket_.connect(("8.8.8.8", 80))
            if unknown_errors:
                logger.info("Connection established with IP: %s. Resetting temp errors.", socket_.getsockname()[0])
        except OSError as error:
            logger.error("OSError [%d]: %s", error.errno, error.strerror)
            ControlPeripheral(logger=logger).enable()  # Make sure Wi-Fi is enabled
            time.sleep(5)  # When Wi-Fi is toggled, it takes a couple of seconds to actually turn on
            ControlConnection(wifi_ssid=models.env.wifi_ssid, wifi_password=models.env.wifi_password,
                              logger=logger).wifi_connector()  # Try to connect to Wi-Fi using given SSID
        except Exception as error:
            logger.critical(error)
            unknown_errors += 1

        if unknown_errors > 5:
            controls.restart_control(quiet=True)
            return

        time.sleep(models.env.connection_retry)
