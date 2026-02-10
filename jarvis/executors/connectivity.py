import socket
import threading
from http.client import HTTPSConnection

import pywifi

from jarvis.modules.logger import logger
from jarvis.modules.models import classes, enums, models


async def wifi() -> None:
    """Checks for internet connection as per given frequency. Enables Wi-Fi and connects to SSID if connection fails.

    Returns:
        WiFiConnection:
        Returns the connection object to keep alive, None to stop calling this function.
    """
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if models.settings.os == enums.SupportedPlatforms.windows:
            # Recreate a new connection everytime
            connection = HTTPSConnection("8.8.8.8", timeout=3)
            connection.request("HEAD", "/")
            ip_addr = connection.getresponse().read().decode().strip()
            connection.close()
        else:
            socket_.connect(("8.8.8.8", 80))
            ip_addr = socket_.getsockname()[0]
            socket_.close()
        if classes.wifi_connection.unknown_errors:
            logger.info("Connection established with IP: %s. Resetting flags.", ip_addr)
            classes.wifi_connection.unknown_errors = 0
            classes.wifi_connection.os_errors = 0
    except OSError as error:
        classes.wifi_connection.os_errors += 1
        logger.error("OSError [%d]: %s", error.errno, error.strerror)
        # Make sure Wi-Fi is enabled
        pywifi.ControlPeripheral(logger=logger).enable()
        connection_control = pywifi.ControlConnection(
            wifi_ssid=models.env.wifi_ssid,
            wifi_password=models.env.wifi_password,
            logger=logger,
        )
        threading.Timer(interval=5, function=connection_control.wifi_connector).start()
    except Exception as error:
        logger.critical(error)
        classes.wifi_connection.unknown_errors += 1

    if classes.wifi_connection.unknown_errors > 10 or classes.wifi_connection.os_errors > 30:
        logger.warning(classes.wifi_connection.model_dump_json())
        logger.error("WiFi connector is running into repeated errors, hence stopping..!")
        classes.wifi_connection = None
