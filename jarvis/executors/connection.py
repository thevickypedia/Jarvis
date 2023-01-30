import os
import socket
import time
from typing import NoReturn

from jarvis.executors.controls import restart_control
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.wifi.connector import ControlConnection, ControlPeripheral


def wifi_connector() -> NoReturn:
    """Checks for internet connection as per given frequency. Enables Wi-Fi and connects to SSID if connection fails.

    See Also:
        - Logs up to 10 consecutive errors from socket module or a total of 5 unknown errors before restarting process.
    """
    # processName filter is not added since process runs on a single function that is covered by funcName
    config.multiprocessing_logger(filename=os.path.join('logs', 'wifi_connector_%d-%m-%Y.log'))
    if not models.env.wifi_ssid or not models.env.wifi_password:
        logger.warning("Cannot retry connections without SSID and password.")
        return

    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    unknown_errors = temporary_errors = 0
    while True:
        try:
            socket_.connect(("8.8.8.8", 80))
            if temporary_errors or unknown_errors:
                logger.info(f"Connection established with IP: {socket_.getsockname()[0]}. Resetting temp errors.")
            temporary_errors = 0  # Resets temporary errors after a successful connection
        except OSError as error:
            logger.error(error)
            if error.errno == 51:
                ControlPeripheral().enable()  # Make sure Wi-Fi is enabled
                time.sleep(5)  # When Wi-Fi is toggled, it takes a couple of seconds to actually turn on
                ControlConnection().wifi_connector()  # Try to connect to Wi-Fi using given SSID
            else:
                temporary_errors += 1  # errors from socket module
        except Exception as error:
            logger.fatal(error)
            unknown_errors += 1

        if unknown_errors > 5 or temporary_errors > 10:
            restart_control(quiet=True)
            return

        time.sleep(models.env.connection_retry)
