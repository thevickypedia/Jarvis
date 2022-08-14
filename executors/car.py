import json
import urllib.error
import urllib.request
from threading import Thread
from typing import Tuple, Union

import yaml
from playsound import playsound

from executors.location import get_location_from_coordinates
from executors.logger import logger
from modules.audio import speaker
from modules.car import connector, controller
from modules.models import models
from modules.temperature import temperature
from modules.utils import shared, support


def get_current_temp(location: dict) -> Tuple[Union[int, str], int]:
    """Get the current temperature at a given location.

    Args:
        location: Takes the location information as a dictionary.

    Returns:
        tuple:
        A tuple of current temperature and target temperature.
    """
    try:
        current_temp = int(temperature.k2f(arg=json.loads(urllib.request.urlopen(
            url=f"https://api.openweathermap.org/data/2.5/onecall?lat={location['latitude']}&"
                f"lon={location['longitude']}&exclude=minutely,hourly&appid={models.env.weather_api}"
        ).read())['current']['temp']))
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        logger.error(error)
        return "unknown", 66
    target_temp = 83 if current_temp < 45 else 57 if current_temp > 70 else 66
    return f"{current_temp}\N{DEGREE SIGN}F", target_temp


def car(phrase: str) -> None:
    """Controls the car to lock, unlock or remote start.

    Args:
        phrase: Takes the phrase spoken as an argument.

    See Also:
        API climate controls: 31 is LO, 57 is HOT
        Car Climate controls: 58 is LO, 84 is HOT
    """
    if not all([models.env.car_email, models.env.car_pass, models.env.car_pin]):
        logger.warning("InControl email or password or PIN not found.")
        support.no_env_vars()
        return

    disconnected = f"I wasn't able to connect your car {models.env.title}! Please check the logs for more information."

    if "start" in phrase or "set" in phrase or "turn on" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        extras = ""
        if target_temp := support.extract_nos(input_=phrase, method=int):
            if target_temp < 57:
                target_temp = 57
            elif target_temp > 83:
                target_temp = 83
        elif "high" in phrase or "highest" in phrase:
            target_temp = 83
        elif "low" in phrase or "lowest" in phrase:
            target_temp = 57
        else:
            if vehicle_position := vehicle(operation="LOCATE_INTERNAL"):
                current_temp, target_temp = get_current_temp(location=vehicle_position)
                extras += f"Your car is in {vehicle_position['city']} {vehicle_position['state']}, where the " \
                          f"current temperature is {current_temp}, so "
            else:
                try:
                    with open(models.fileio.location) as file:
                        position = yaml.load(stream=file, Loader=yaml.FullLoader)
                        current_temp, target_temp = get_current_temp(location=position)
                        extras += f"The current temperature in " \
                                  f"{position.get('address', {}).get('city', 'unknown city')} is {current_temp}, so "
                except yaml.YAMLError as error:
                    logger.error(error)
                    target_temp = 69
        extras += f"I've configured the climate setting to {target_temp}\N{DEGREE SIGN}F"
        if car_name := vehicle(operation="START", temp=target_temp - 26):
            speaker.speak(text=f"Your {car_name} has been started {models.env.title}. {extras}")
        else:
            speaker.speak(text=disconnected)
    elif "turn off" in phrase or "stop" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        if car_name := vehicle(operation="STOP"):
            speaker.speak(text=f"Your {car_name} has been turned off {models.env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "secure" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        if car_name := vehicle(operation="SECURE"):
            speaker.speak(text=f"Guardian mode has been enabled {models.env.title}! Your {car_name} is now secure.")
        else:
            speaker.speak(text=disconnected)
    elif "unlock" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        if car_name := vehicle(operation="UNLOCK"):
            speaker.speak(text=f"Your {car_name} has been unlocked {models.env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "lock" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        if car_name := vehicle(operation="LOCK"):
            speaker.speak(text=f"Your {car_name} has been locked {models.env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "honk" in phrase or "blink" in phrase or "horn" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        if car_name := vehicle(operation="HONK"):
            speaker.speak(text=f"I've made your {car_name} honk and blink {models.env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "locate" in phrase or "where" in phrase:
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
        if location := vehicle(operation="LOCATE"):
            speaker.speak(text=location)
        else:
            speaker.speak(text=disconnected)
    else:
        speaker.speak(text=f"I didn't quite get that {models.env.title}! What do you want me to do to your car?")
        Thread(target=support.unrecognized_dumper, args=[{"CAR": phrase}]).start()


def vehicle(operation: str, temp: int = None) -> Union[str, dict, None]:
    """Establishes a connection with the car and returns an object to control the primary vehicle.

    Args:
        operation: Operation to be performed.
        temp: Temperature for climate control.

    Returns:
        str:
        Returns the vehicle's name.
    """
    try:
        connection = connector.Connect(username=models.env.car_email, password=models.env.car_pass)
        connection.connect()
        if not connection.head:
            return
        vehicles = connection.get_vehicles(headers=connection.head).get("vehicles")
        primary_vehicle = [each_vehicle for each_vehicle in vehicles if each_vehicle.get("role") == "Primary"][0]
        control = controller.Control(vin=primary_vehicle.get("vin"), connection=connection)

        response = {}
        if operation == "LOCK":
            response = control.lock(pin=models.env.car_pin)
        elif operation == "UNLOCK":
            response = control.unlock(pin=models.env.car_pin)
        elif operation == "START":
            lock_status = {each_dict['key']: each_dict['value'] for each_dict in
                           [key for key in control.get_status().get('vehicleStatus').get('coreStatus')
                            if key.get('key') in ["DOOR_IS_ALL_DOORS_LOCKED", "DOOR_BOOT_LOCK_STATUS"]]}
            if lock_status.get('DOOR_IS_ALL_DOORS_LOCKED', 'FALSE') != 'TRUE' or \
                    lock_status.get('DOOR_BOOT_LOCK_STATUS', 'UNLOCKED') != 'LOCKED':
                logger.warning("Car is unlocked when tried to remote start!")
                if lock_response := control.lock(pin=models.env.car_pin).get("failureDescription"):
                    logger.error(lock_response)
            response = control.remote_engine_start(pin=models.env.car_pin, target_temperature=temp)
        elif operation == "STOP":
            response = control.remote_engine_stop(pin=models.env.car_pin)
        elif operation == "SECURE":
            response = control.enable_guardian_mode(pin=models.env.car_pin)
        elif operation == "HONK":
            response = control.honk_blink()
        elif operation == "LOCATE" or operation == "LOCATE_INTERNAL":
            if not (position := control.get_position().get('position')):
                logger.error("Unable to get position of the vehicle.")
                return
            data = get_location_from_coordinates(coordinates=(position['latitude'], position['longitude']))
            number = data.get('streetNumber', data.get('house_number', ''))
            street = data.get('street', data.get('road'))
            state = data.get('region', data.get('state', data.get('county')))
            city, country = data.get('city', data.get('residential')), data.get('country')
            if operation == "LOCATE_INTERNAL":
                position['city'] = city
                position['state'] = state
                return position
            if all([street, state, city, country]):
                address = f"{number} {street}, {city} {state}, {country}".strip()
            elif data.get('formattedAddress'):
                address = data['formattedAddress']
            else:
                address = data
            return f"Your {control.get_attributes().get('vehicleBrand', 'car')} is at {address}"
        if response.get("failureDescription"):
            logger.fatal(response)
            return
        return control.get_attributes().get("vehicleBrand", "car")
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        logger.error(error.__dict__)
        if hasattr(error, "url") and hasattr(error, "code"):
            logger.error(f"Failed to connect to {error.url} with error code: {error.code} while performing {operation}")
