import socket
import threading
from http.client import HTTPSConnection

import pywifi

from jarvis.modules.logger import logger
from jarvis.modules.models import classes, enums, models


def wifi(conn_object: classes.WiFiConnection) -> classes.WiFiConnection | None:
    """Checks for internet connection as per given frequency. Enables Wi-Fi and connects to SSID if connection fails.

    Args:
        conn_object: Takes an object of unknown errors and OSError as an argument.

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
        else:
            socket_.connect(("8.8.8.8", 80))
        if conn_object.unknown_errors:
            logger.info(
                "Connection established with IP: %s. Resetting flags.",
                socket_.getsockname()[0],
            )
            conn_object.unknown_errors = 0
            conn_object.os_errors = 0
    except OSError as error:
        conn_object.os_errors += 1
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
        conn_object.unknown_errors += 1

    if conn_object.unknown_errors > 10 or conn_object.os_errors > 30:
        logger.warning(conn_object.model_dump_json())
        logger.error(
            "'%s' is running into repeated errors, hence stopping..!", wifi.__name__
        )
        return None
    return conn_object
