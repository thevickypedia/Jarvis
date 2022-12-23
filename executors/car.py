import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from threading import Thread
from typing import Tuple, Union

import yaml
from playsound import playsound

from executors.communicator import send_email
from executors.location import get_location_from_coordinates
from executors.word_match import word_match
from modules.audio import speaker
from modules.car import connector, controller
from modules.logger.custom_logger import logger
from modules.models import models
from modules.temperature import temperature
from modules.utils import shared, support, util


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


class Operations:
    """Car operations that car condensed into its own object.

    >>> Operations

    """

    def __init__(self):
        """Initiates the callable function and a failure message."""
        self.object = vehicle
        self.disconnect = f"I wasn't able to connect your car {models.env.title}! " \
                          "Please check the logs for more information."

    def turn_on(self, phrase: str) -> str:
        """Calls the vehicle function to turn the car on with the requested climate setting.

        Args:
            phrase: Takes the recognized phrase as an argument.

        Returns:
            str:
            Response after turning on the vehicle.
        """
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
        opr = "START-LOCK" if 'lock' in phrase else "START"
        if car_name := self.object(operation=opr, temp=target_temp - 26):
            return f"Your {car_name} has been started {models.env.title}. {extras}"
        else:
            return self.disconnect

    def turn_off(self) -> str:
        """Calls the vehicle function to turn off the vehicle.

        Returns:
            str:
            Response after turning off the vehicle.
        """
        if car_name := self.object(operation="STOP"):
            return f"Your {car_name} has been turned off {models.env.title}!"
        else:
            return self.disconnect

    def enable_guard(self, phrase) -> str:
        """Requests vehicle function to enable guardian mode for the requested time.

        Args:
            phrase: Takes the recognized phrase as an argument.

        See Also:
            - Extracts a numeric value in the phrase or words that refer to a numeric value in the phrase

        Returns:
            str:
            Response after enabling guardian mode on the vehicle.
        """
        requested_expiry = support.extract_nos(input_=phrase, method=int) or support.words_to_number(input_=phrase) or 1
        if 'hour' in phrase:
            seconds = requested_expiry * 3_600  # Defaults to 1 hour if no numeric value in phrase
        elif 'day' in phrase:
            seconds = requested_expiry * 86_400  # Defaults to 1 day if no numeric value in phrase
        elif 'week' in phrase:
            seconds = requested_expiry * 604_800  # Defaults to 1 week if no numeric value in phrase
        else:
            seconds = 3_600  # Defaults to 1 hour if no datetime conversion was received
        expire = int((time.time() + seconds) * 1000)  # multiply by 1000 to including microseconds making it 13 digits
        if response := self.object(operation="SECURE", end_time=expire):
            return response
        else:
            return self.disconnect

    def lock(self) -> str:
        """Calls vehicle function to perform the lock operation.

        Returns:
            str:
            Response after locking the vehicle.
        """
        if car_name := self.object(operation="LOCK"):
            speaker.speak(text=f"Your {car_name} has been locked {models.env.title}!")
        else:
            return self.disconnect

    def unlock(self, dt_string: str = None) -> str:
        """Calls vehicle function to perform the unlock operation.

        Returns:
            str:
            Response after unlocking the vehicle.
        """
        if car_name := self.object(operation="UNLOCK"):
            if dt_string and shared.called_by_offline:
                send_email(body=f"Your {car_name} was successfully unlocked via offline communicator!",
                           recipient=models.env.recipient, subject=f"Car unlock alert: {dt_string}",
                           title="Vehicle Protection",
                           gmail_user=models.env.alt_gmail_user, gmail_pass=models.env.alt_gmail_pass)
            return f"Your {car_name} has been unlocked {models.env.title}!"
        else:
            return self.disconnect

    def honk(self) -> str:
        """Calls vehicle function to honk the car.

        Returns:
            str:
            Response after honking the vehicle.
        """
        if car_name := self.object(operation="HONK"):
            return f"I've made your {car_name} honk and blink {models.env.title}!"
        else:
            return self.disconnect

    def locate(self) -> str:
        """Calls vehicle function to locate the car.

        Returns:
            str:
            Response after retrieving the location of the vehicle.
        """
        if location := self.object(operation="LOCATE"):
            return location
        else:
            return self.disconnect


def car(phrase: str) -> None:
    """Controls the car to lock, unlock or remote start.

    Args:
        phrase: Takes the phrase spoken as an argument.

    See Also:
        API climate controls: 31 is LO, 57 is HOT
        Car Climate controls: 58 is LO, 84 is HOT
    """
    if all([models.env.car_email, models.env.car_pass, models.env.car_pin]):
        phrase = phrase.lower()
    else:
        logger.warning("InControl email or password or PIN not found.")
        support.no_env_vars()
        return

    allowed_dict = {'on': ['start', 'set', 'turn on'],
                    'off': ['stop', 'turn off'],
                    'guard': ['secur', 'guard'],  # Intentional typo that covers both 'security' and 'secure' in phrase
                    'lock': ['lock'], 'unlock': ['unlock'],
                    'honk': ['honk', 'blink', 'horn'],
                    'locate': ['locate', 'where']}

    if word_match(phrase=phrase, match_list=support.matrix_to_flat_list(list(allowed_dict.values()))):
        if not shared.called_by_offline:
            playsound(sound=models.indicators.exhaust, block=False)
    else:
        speaker.speak(text=f"I didn't quite get that {models.env.title}! What do you want me to do to your car?")
        Thread(target=support.unrecognized_dumper, args=[{"CAR": phrase}]).start()
        return

    response = "Unsupported operation for car controls."
    caller = Operations()
    if word_match(phrase=phrase, match_list=allowed_dict['on']):
        response = caller.turn_on(phrase=phrase)
    elif word_match(phrase=phrase, match_list=allowed_dict['off']):
        response = caller.turn_off()
    elif word_match(phrase=phrase, match_list=allowed_dict['guard']):
        response = caller.enable_guard(phrase=phrase)
    elif word_match(phrase=phrase, match_list=allowed_dict['unlock']):
        dt_string = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        if shared.called_by_offline:
            send_email(body="Your vehicle has been requested to unlock via offline communicator!",
                       recipient=models.env.recipient, subject=f"Car unlock alert: {dt_string}",
                       title="Vehicle Protection",
                       gmail_user=models.env.alt_gmail_user, gmail_pass=models.env.alt_gmail_pass)
        response = caller.unlock(dt_string=dt_string)
    elif word_match(phrase=phrase, match_list=allowed_dict['lock']):
        response = caller.lock()
    elif word_match(phrase=phrase, match_list=allowed_dict['honk']):
        response = caller.honk()
    elif word_match(phrase=phrase, match_list=allowed_dict['locate']):
        response = caller.locate()
    speaker.speak(text=response)


def vehicle(operation: str, temp: int = None, end_time: int = None, retry: bool = True) -> Union[str, dict, None]:
    """Establishes a connection with the car and returns an object to control the primary vehicle.

    Args:
        operation: Operation to be performed.
        temp: Temperature for climate control.
        end_time: End time for guardian mode. Should be a 13 digit integer including microseconds.
        retry: Retry logic used when guardian mode is enabled already.

    Returns:
        str:
        Returns the vehicle's name.
    """
    control = None
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
        elif operation == "START" or operation == "START-LOCK":
            if operation == "START-LOCK":
                lock_status = {each_dict['key']: each_dict['value'] for each_dict in
                               [key for key in control.get_status().get('vehicleStatus').get('coreStatus')
                                if key.get('key') in ["DOOR_IS_ALL_DOORS_LOCKED", "DOOR_BOOT_LOCK_STATUS"]]}
                if lock_status.get('DOOR_IS_ALL_DOORS_LOCKED', 'FALSE') != 'TRUE' or \
                        lock_status.get('DOOR_BOOT_LOCK_STATUS', 'UNLOCKED') != 'LOCKED':
                    logger.warning("Car is unlocked when tried to remote start!")
                    lock_response = control.lock(pin=models.env.car_pin)
                    if lock_response.get("failureDescription"):
                        logger.error(lock_response)
                    else:
                        logger.info("Vehicle has been locked!")
                        time.sleep(3)  # Wait before locking the car, so that there is no overlap in refresh token
            response = control.remote_engine_start(pin=models.env.car_pin, target_temperature=temp)
        elif operation == "STOP":
            response = control.remote_engine_stop(pin=models.env.car_pin)
        elif operation == "SECURE":
            control.enable_guardian_mode(pin=models.env.car_pin, expiration_time=end_time)
            until = datetime.fromtimestamp(end_time / 1000).strftime("%A, %B %d, %I:%M %p")  # Remove microseconds
            return f"Guardian mode has been enabled {models.env.title}! " \
                   f"Your {control.get_attributes().get('vehicleBrand', 'car')} will be guarded until " \
                   f"{until} {util.get_timezone()}"
        elif operation == "SECURE_EXIST":  # Only called during recursion
            current_end = control.get_guardian_mode_status().get('endTime')
            if not current_end:
                return
            utc_dt = datetime.strptime(current_end, "%Y-%m-%dT%H:%M:%S.%fZ")  # Convert str to datetime object
            until = support.convert_utc_to_local(utc_dt=utc_dt).strftime("%A, %B %d, %I:%M %p")
            return f"Guardian mode is already enabled until {until} {util.get_timezone()} {models.env.title}!"
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
        if response and response.get("failureDescription"):
            logger.fatal(response)
            return
        return control.get_attributes().get("vehicleBrand", "car")
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        if operation == "SECURE" and hasattr(error, "code") and error.code == 409 and control and retry:
            return vehicle(operation="SECURE_EXIST", retry=False)
        logger.error(error.__dict__)
        if hasattr(error, "url") and hasattr(error, "code"):
            logger.error(f"Failed to connect to {error.url} with error code: {error.code} while performing {operation}")
