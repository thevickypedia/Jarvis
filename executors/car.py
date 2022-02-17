from typing import Union
from urllib.error import HTTPError

from executors.custom_logger import logger
from modules.car import connector, controller


def vehicle(car_email, car_pass, car_pin, operation: str, temp: int = None) -> Union[str, None]:
    """Establishes a connection with the car and returns an object to control the primary vehicle.

    Args:
        car_email: Email to authenticate API.
        car_pass: Password to authenticate API.
        operation: Operation to be performed.
        car_pin: Master PIN to perform operations.
        temp: Temperature for climate control.

    Returns:
        Control:
        Control object to access the primary vehicle.
    """
    try:
        connection = connector.Connect(username=car_email, password=car_pass, logger=logger)
        connection.connect()
        if not connection.head:
            return
        vehicles = connection.get_vehicles(headers=connection.head).get('vehicles')
        primary_vehicle = [each_vehicle for each_vehicle in vehicles if each_vehicle.get('role') == 'Primary'][0]
        handler = controller.Control(vin=primary_vehicle.get('vin'), connection=connection)

        if operation == 'LOCK':
            handler.lock(pin=car_pin)
        elif operation == 'UNLOCK':
            handler.unlock(pin=car_pin)
        elif operation == 'START':
            handler.remote_engine_start(pin=car_pin, target_temperature=temp)
        elif operation == 'STOP':
            handler.remote_engine_stop(pin=car_pin)
        elif operation == 'SECURE':
            handler.enable_guardian_mode(pin=car_pin)
        return handler.get_attributes().get('vehicleBrand', 'car')
    except HTTPError as error:
        logger.error(error)
