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

env = models.env
fileio = models.FileIO()
indicators = models.Indicators()


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
                f"lon={location['longitude']}&exclude=minutely,hourly&appid={env.weather_api}"
        ).read())['current']['temp']))
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        logger.error(error)
        return "unknown", 66
    target_temp = 83 if current_temp < 45 else 57 if current_temp > 70 else 66
    return f"{current_temp}°F", target_temp


def car(phrase: str) -> None:
    """Controls the car to lock, unlock or remote start.

    Args:
        phrase: Takes the phrase spoken as an argument.

    See Also:
        API climate controls: 31 is LO, 57 is HOT
        Car Climate controls: 58 is LO, 84 is HOT
    """
    if not all([env.car_email, env.car_pass, env.car_pin]):
        logger.warning("InControl email or password or PIN not found.")
        support.no_env_vars()
        return

    disconnected = f"I wasn't able to connect your car {env.title}! Please check the logs for more information."

    if "start" in phrase or "set" in phrase or "turn on" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
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
                    with open(fileio.location) as file:
                        current_temp, target_temp = get_current_temp(location=yaml.load(stream=file,
                                                                                        Loader=yaml.FullLoader))
                        extras += f"The current temperature is {current_temp}, so "
                except yaml.YAMLError as error:
                    logger.error(error)
                    target_temp = 69
        extras += f"I've configured the climate setting to {target_temp}°F"
        if car_name := vehicle(operation="START", temp=target_temp - 26):
            speaker.speak(text=f"Your {car_name} has been started {env.title}. {extras}")
        else:
            speaker.speak(text=disconnected)
    elif "turn off" in phrase or "stop" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
        if car_name := vehicle(operation="STOP"):
            speaker.speak(text=f"Your {car_name} has been turned off {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "secure" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
        if car_name := vehicle(operation="SECURE"):
            speaker.speak(text=f"Guardian mode has been enabled {env.title}! Your {car_name} is now secure.")
        else:
            speaker.speak(text=disconnected)
    elif "unlock" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
        if car_name := vehicle(operation="UNLOCK"):
            speaker.speak(text=f"Your {car_name} has been unlocked {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "lock" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
        if car_name := vehicle(operation="LOCK"):
            speaker.speak(text=f"Your {car_name} has been locked {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "honk" in phrase or "blink" in phrase or "horn" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
        if car_name := vehicle(operation="HONK"):
            speaker.speak(text=f"I've made your {car_name} honk and blink {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "locate" in phrase or "where" in phrase:
        if not shared.called_by_offline:
            playsound(sound=indicators.exhaust, block=False)
        if location := vehicle(operation="LOCATE"):
            speaker.speak(text=location)
        else:
            speaker.speak(text=disconnected)
    else:
        speaker.speak(text=f"I didn't quite get that {env.title}! What do you want me to do to your car?")
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
        connection = connector.Connect(username=env.car_email, password=env.car_pass)
        connection.connect()
        if not connection.head:
            return
        vehicles = connection.get_vehicles(headers=connection.head).get("vehicles")
        primary_vehicle = [each_vehicle for each_vehicle in vehicles if each_vehicle.get("role") == "Primary"][0]
        handler = controller.Control(vin=primary_vehicle.get("vin"), connection=connection)

        response = {}
        if operation == "LOCK":
            response = handler.lock(pin=env.car_pin)
        elif operation == "UNLOCK":
            response = handler.unlock(pin=env.car_pin)
        elif operation == "START":
            response = handler.remote_engine_start(pin=env.car_pin, target_temperature=temp)
        elif operation == "STOP":
            response = handler.remote_engine_stop(pin=env.car_pin)
        elif operation == "SECURE":
            response = handler.enable_guardian_mode(pin=env.car_pin)
        elif operation == "HONK":
            response = handler.honk_blink()
        elif operation == "LOCATE" or operation == "LOCATE_INTERNAL":
            if not (position := handler.get_position().get('position')):
                logger.error("Unable to get position of the vehicle.")
                return
            if not (data := handler.connection.reverse_geocode(latitude=position.get('latitude'),
                                                               longitude=position.get('longitude'))):
                logger.error("Unable to get location details of the vehicle.")
                data = get_location_from_coordinates(coordinates=(position['latitude'], position['longitude']))
            number = data.get('streetNumber', data.get('house_number'))
            street = data.get('street', data.get('road'))
            state = data.get('region', data.get('state'))
            city, country = data.get('city'), data.get('country')
            if operation == "LOCATE_INTERNAL":
                position['city'] = city
                position['state'] = state
                return position
            if all([number, street, state, city, country]):
                address = f"{number} {street}, {city} {state}, {country}"
            elif data.get('formattedAddress'):
                address = data['formattedAddress']
            else:
                address = data
            return f"Your {handler.get_attributes().get('vehicleBrand', 'car')} is at {address}"
        if response.get("failureDescription"):
            logger.fatal(response)
            return
        return handler.get_attributes().get("vehicleBrand", "car")
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        if isinstance(error, urllib.error.URLError):
            logger.fatal("UNKNOWN ERROR! REQUIRES INVESTIGATION!")
            logger.fatal(error)
        else:
            logger.error(error)
            logger.error(f"Failed to connect {error.url} with error code: {error.code}")
