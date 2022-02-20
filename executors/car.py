import json
from threading import Thread
from typing import Union
from urllib.error import HTTPError
from urllib.request import urlopen

from playsound import playsound

from executors.logger import logger
from modules.audio import speaker
from modules.car import connector, controller
from modules.temperature import temperature
from modules.utils import globals, support

env = globals.ENV


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

    disconnected = "I wasn't able to connect your car sir! Please check the logs for more information."

    if 'start' in phrase or 'set' in phrase or 'turn on' in phrase:
        extras = ''
        if climate := support.extract_nos(input_=phrase):
            climate = int(climate)
        elif 'high' in phrase or 'highest' in phrase:
            climate = 83
        elif 'low' in phrase or 'lowest' in phrase:
            climate = 57
        else:
            climate = int(temperature.k2f(arg=json.loads(urlopen(
                url=f"https://api.openweathermap.org/data/2.5/onecall?lat={globals.current_location_['current_lat']}&"
                    f"lon={globals.current_location_['current_lon']}&exclude=minutely,hourly&appid={env.weather_api}"
            ).read())['current']['temp']))
            extras += f'The current temperature is {climate}°F, so '

        # Custom temperature that has to be set in the vehicle
        target_temp = 83 if climate < 45 else 57 if climate > 70 else 66
        extras += f"I've configured the climate setting to {target_temp}°F"

        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=env.car_email, car_pass=env.car_pass, car_pin=env.car_pin,
                               operation='START', temp=target_temp - 26):
            speaker.speak(text=f'Your {car_name} has been started sir. {extras}')
        else:
            speaker.speak(text=disconnected)
    elif 'turn off' in phrase or 'stop' in phrase:
        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=env.car_email, car_pass=env.car_pass, operation='STOP', car_pin=env.car_pin):
            speaker.speak(text=f'Your {car_name} has been turned off sir!')
        else:
            speaker.speak(text=disconnected)
    elif 'secure' in phrase:
        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=env.car_email, car_pass=env.car_pass, operation='SECURE', car_pin=env.car_pin):
            speaker.speak(text=f'Guardian mode has been enabled sir! Your {car_name} is now secure.')
        else:
            speaker.speak(text=disconnected)
    elif 'unlock' in phrase:
        if globals.called_by_offline['status']:
            speaker.speak(text='Cannot unlock the car via offline communicator due to security reasons.')
            return
        playsound(sound='indicators/exhaust.mp3', block=False)
        if car_name := vehicle(car_email=env.car_email, car_pass=env.car_pass, operation='UNLOCK', car_pin=env.car_pin):
            speaker.speak(text=f'Your {car_name} has been unlocked sir!')
        else:
            speaker.speak(text=disconnected)
    elif 'lock' in phrase:
        playsound(sound='indicators/exhaust.mp3', block=False) if not globals.called_by_offline['status'] else None
        if car_name := vehicle(car_email=env.car_email, car_pass=env.car_pass, operation='LOCK', car_pin=env.car_pin):
            speaker.speak(text=f'Your {car_name} has been locked sir!')
        else:
            speaker.speak(text=disconnected)
    else:
        speaker.speak(text="I didn't quite get that sir! What do you want me to do to your car?")
        Thread(target=support.unrecognized_dumper, args=[{'CAR': phrase}])


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
