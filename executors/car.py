import json
import os
from threading import Thread
from typing import Union
from urllib.error import HTTPError
from urllib.request import urlopen

import yaml
from playsound import playsound

from executors.location import get_location_from_coordinates
from executors.logger import logger
from modules.audio import speaker
from modules.car import connector, controller
from modules.models import models
from modules.temperature import temperature
from modules.utils import globals, support

env = models.env
fileio = models.fileio


def car(phrase: str) -> None:
    """Controls the car to lock, unlock or remote start.

    Args:
        phrase: Takes the phrase spoken as an argument.

    See Also:
        API climate controls: 31 is LO, 57 is HOT
        Car Climate controls: 58 is LO, 84 is HOT
    """
    if not all([env.car_email, env.car_pass, env.car_pin]):
        support.no_env_vars()
        return

    disconnected = f"I wasn't able to connect your car {env.title}! Please check the logs for more information."

    if "start" in phrase or "set" in phrase or "turn on" in phrase:
        extras = ""
        if climate := support.extract_nos(input_=phrase, method=int):
            pass
        elif "high" in phrase or "highest" in phrase:
            climate = 83
        elif "low" in phrase or "lowest" in phrase:
            climate = 57
        else:
            with open(fileio.location) as file:
                current_location = yaml.load(stream=file, Loader=yaml.FullLoader)
            climate = int(temperature.k2f(arg=json.loads(urlopen(
                url=f"https://api.openweathermap.org/data/2.5/onecall?lat={current_location['latitude']}&"
                    f"lon={current_location['longitude']}&exclude=minutely,hourly&appid={env.weather_api}"
            ).read())['current']['temp']))
            extras += f"The current temperature is {climate}°F, so "

        # Custom temperature that has to be set in the vehicle
        target_temp = 83 if climate < 45 else 57 if climate > 70 else 66
        extras += f"I've configured the climate setting to {target_temp}°F"

        if not globals.called_by_offline:
            playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if car_name := vehicle(operation="START", temp=target_temp - 26):
            speaker.speak(text=f"Your {car_name} has been started {env.title}. {extras}")
        else:
            speaker.speak(text=disconnected)
    elif "turn off" in phrase or "stop" in phrase:
        if not globals.called_by_offline:
            playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if car_name := vehicle(operation="STOP"):
            speaker.speak(text=f"Your {car_name} has been turned off {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "secure" in phrase:
        if not globals.called_by_offline:
            playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if car_name := vehicle(operation="SECURE"):
            speaker.speak(text=f"Guardian mode has been enabled {env.title}! Your {car_name} is now secure.")
        else:
            speaker.speak(text=disconnected)
    elif "unlock" in phrase:
        if globals.called_by_offline:
            speaker.speak(text="Cannot unlock the car via offline communicator due to security reasons.")
            return
        playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if car_name := vehicle(operation="UNLOCK"):
            speaker.speak(text=f"Your {car_name} has been unlocked {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "lock" in phrase:
        if not globals.called_by_offline:
            playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if car_name := vehicle(operation="LOCK"):
            speaker.speak(text=f"Your {car_name} has been locked {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "honk" in phrase or "blink" in phrase or "horn" in phrase:
        if not globals.called_by_offline:
            playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if car_name := vehicle(operation="HONK"):
            speaker.speak(text=f"I've made your {car_name} honk and blink {env.title}!")
        else:
            speaker.speak(text=disconnected)
    elif "locate" in phrase or "where" in phrase:
        if not globals.called_by_offline:
            playsound(sound=f"indicators{os.path.sep}exhaust.mp3", block=False)
        if location := vehicle(operation="LOCATE"):
            speaker.speak(text=location)
        else:
            speaker.speak(text=disconnected)
    else:
        speaker.speak(text=f"I didn't quite get that {env.title}! What do you want me to do to your car?")
        Thread(target=support.unrecognized_dumper, args=[{"CAR": phrase}])


def vehicle(operation: str, temp: int = None) -> Union[str, None]:
    """Establishes a connection with the car and returns an object to control the primary vehicle.

    Args:
        operation: Operation to be performed.
        temp: Temperature for climate control.

    Returns:
        Control:
        Control object to access the primary vehicle.
    """
    try:
        connection = connector.Connect(username=env.car_email, password=env.car_pass)
        connection.connect()
        if not connection.head:
            return
        vehicles = connection.get_vehicles(headers=connection.head).get("vehicles")
        primary_vehicle = [each_vehicle for each_vehicle in vehicles if each_vehicle.get("role") == "Primary"][0]
        handler = controller.Control(vin=primary_vehicle.get("vin"), connection=connection)

        if operation == "LOCK":
            handler.lock(pin=env.car_pin)
        elif operation == "UNLOCK":
            handler.unlock(pin=env.car_pin)
        elif operation == "START":
            handler.remote_engine_start(pin=env.car_pin, target_temperature=temp)
        elif operation == "STOP":
            handler.remote_engine_stop(pin=env.car_pin)
        elif operation == "SECURE":
            handler.enable_guardian_mode(pin=env.car_pin)
        elif operation == "HONK":
            handler.honk_blink()
        elif operation == "LOCATE":
            if not (position := handler.get_position().get('position')):
                logger.error("Unable to get position of the vehicle.")
                return
            if not (data := handler.connection.reverse_geocode(latitude=position.get('latitude'),
                                                               longitude=position.get('longitude'))):
                logger.error("Unable to get location details of the vehicle.")
                data = get_location_from_coordinates(coordinates=(position['latitude'], position['longitude']))[-1]
            number = data.get('streetNumber', data.get('house_number'))
            street = data.get('street', data.get('road'))
            state = data.get('region', data.get('state'))
            city, country = data.get('city'), data.get('country')
            if all([number, street, state, city, country]):
                address = f"{number} {street}, {city} {state}, {country}"
            elif data.get('formattedAddress'):
                address = data['formattedAddress']
            else:
                address = data
            return f"Your {handler.get_attributes().get('vehicleBrand', 'car')} is at {address}"
        return handler.get_attributes().get("vehicleBrand", "car")
    except HTTPError as error:
        logger.error(error)
        logger.error(f"Failed to connect {error.url} with error code: {error.code}")
