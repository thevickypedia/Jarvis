import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from multiprocessing import current_process
from multiprocessing.context import \
    TimeoutError as ThreadTimeoutError  # noqa: PyProtectedMember
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import Dict, List, NoReturn, Tuple, Union

import gmailconnector
import jinja2
import requests

from jarvis.executors import communicator, files, location, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.car import connector, controller
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import classes, models
from jarvis.modules.templates import templates
from jarvis.modules.utils import shared, support, util

CONNECTION = classes.VehicleConnection()
AUTHORIZATION = classes.VehicleAuthorization()


def create_connection() -> NoReturn:
    """Creates a new connection and stores the refresh token and device ID in a dedicated object.

    Returns:
        Tuple[connector.Connect, str]:
        Connection object and the primary vehicle's VIN number as a tuple.
    """
    if AUTHORIZATION.refresh_token and time.time() - AUTHORIZATION.expiration <= 86_400:
        # this might never happen, as the connection and vin are reused until auth expiry anyway
        connection = connector.Connect(username=models.env.car_email, refresh_token=AUTHORIZATION.refresh_token,
                                       device_id=AUTHORIZATION.device_id)
    else:
        connection = connector.Connect(username=models.env.car_email, password=models.env.car_pass,
                                       auth_expiry=time.time() + 86_400)
    try:
        connection.connect()
    except requests.RequestException as error:
        logger.error(error)
        connection.head = None
    if connection.head:
        AUTHORIZATION.device_id = connection.device_id
        AUTHORIZATION.expiration = connection.expiration
        AUTHORIZATION.refresh_token = connection.refresh_token
        logger.debug(AUTHORIZATION.__dict__)
        vehicles = connection.get_vehicles(headers=connection.head).get("vehicles")
        if vin := [vehicle_.get('vin') for vehicle_ in vehicles if vehicle_.get('role', '') == 'Primary']:
            CONNECTION.connection = connection
            CONNECTION.vin = vin[0]


# Initiate connection only for main and offline communicators
# WATCH OUT: for changes in function name
if current_process().name in ('MainProcess', 'telegram_api', 'fast_api'):
    if all([models.env.car_email, models.env.car_pass, models.env.car_pin]):
        logger.info("Creating a new vehicle authorization connection for '%s'", current_process().name)
        Thread(target=create_connection).start()


def current_set_temperature(latitude: float, longitude: float) -> Tuple[Union[int, str], int]:
    """Get the current temperature at a given location.

    Returns:
        tuple:
        A tuple of current temperature and target temperature.
    """
    try:
        current_temp = int(json.loads(urllib.request.urlopen(
            url=f"https://api.openweathermap.org/data/2.5/onecall?lat={latitude}&"
                f"lon={longitude}&exclude=minutely,hourly&appid={models.env.weather_api}&units=imperial"
        ).read())['current']['temp'])
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
            phrase: Takes the phrase spoken as an argument.

        See Also:
            API climate controls (Conversion): 31 is LO, 57 is HOT
            Car Climate controls (Fahrenheit): 58 is LO, 84 is HOT

        Warnings:
            - API docs are misleading to believe that the temperature arg is Celsius, but not really.

            https://documenter.getpostman.com/view/6250319/RznBMzqo#59910c25-c107-4335-b178-22e343782b41

        Returns:
            str:
            Response after turning on the vehicle.
        """
        extras = ""
        if target_temp := util.extract_nos(input_=phrase, method=int):
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
                current_temp, target_temp = current_set_temperature(latitude=vehicle_position['latitude'],
                                                                    longitude=vehicle_position['longitude'])
                extras += f"Your car is in {vehicle_position['city']} {vehicle_position['state']}, where the " \
                          f"current temperature is {current_temp}, so "
            else:
                host_location = files.get_location()
                if host_location['latitude'] and host_location['longitude']:
                    current_temp, target_temp = current_set_temperature(latitude=host_location['latitude'],
                                                                        longitude=host_location['longitude'])
                    extras += f"The current temperature in " \
                              f"{host_location.get('address', {}).get('city', 'unknown city')} is {current_temp}, so "
                else:
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
            phrase: Takes the phrase spoken as an argument.

        See Also:
            - Extracts a numeric value in the phrase or words that refer to a numeric value in the phrase

        Returns:
            str:
            Response after enabling guardian mode on the vehicle.
        """
        requested_expiry = util.extract_nos(input_=phrase, method=int) or util.words_to_number(input_=phrase) or 1
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
                communicator.send_email(body=f"Your {car_name} was successfully unlocked via offline communicator!",
                                        recipient=models.env.recipient, subject=f"Car unlock alert: {dt_string}",
                                        title="Vehicle Protection",
                                        gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
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
        if _location := self.object(operation="LOCATE"):
            return _location
        else:
            return self.disconnect

    def report(self) -> str:
        """Calls vehicle function to get the status report.

        Returns:
            str:
            Response after generating a status report of the vehicle.
        """
        if response := self.object(operation="REPORT"):
            return response
        else:
            return self.disconnect


def car(phrase: str) -> None:
    """Controls the car to lock, unlock or remote start.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if all([models.env.car_email, models.env.car_pass, models.env.car_pin]):
        phrase = phrase.lower()
    else:
        logger.warning("InControl email or password or PIN not found.")
        support.no_env_vars()
        return

    allowed_dict = {'on': ['start', 'set', 'turn on'],
                    'off': ['stop', 'turn off'],
                    'report': ['report'],
                    'guard': ['security', 'guardian', 'secure', 'guard'],
                    'lock': ['lock'], 'unlock': ['unlock'],
                    'honk': ['honk', 'blink', 'horn'],
                    'locate': ['locate', 'where']}

    if not word_match.word_match(phrase=phrase, match_list=util.matrix_to_flat_list(list(allowed_dict.values()))):
        speaker.speak(text=f"I didn't quite get that {models.env.title}! What do you want me to do to your car?")
        Thread(target=support.unrecognized_dumper, args=[{"CAR": phrase}]).start()
        return

    response = "Unsupported operation for car controls."
    caller = Operations()
    if word_match.word_match(phrase=phrase, match_list=allowed_dict['on']):
        response = caller.turn_on(phrase=phrase)
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['off']):
        response = caller.turn_off()
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['report']):
        response = caller.report()
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['guard']):
        response = caller.enable_guard(phrase=phrase)
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['unlock']):
        dt_string = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        if shared.called_by_offline:
            communicator.send_email(body="Your vehicle has been requested to unlock via offline communicator!",
                                    recipient=models.env.recipient, subject=f"Car unlock alert: {dt_string}",
                                    title="Vehicle Protection",
                                    gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
        response = caller.unlock(dt_string=dt_string)
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['lock']):
        response = caller.lock()
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['honk']):
        response = caller.honk()
    elif word_match.word_match(phrase=phrase, match_list=allowed_dict['locate']):
        response = caller.locate()
    speaker.speak(text=response)


def convert_dt_report(dt_string: str) -> str:
    """Converts UTC to local datetime string. Helper function for generating car report.

    Args:
        dt_string: Takes the UTC datetime string as an argument.

    Returns:
        str:
        Returns the local datetime string.
    """
    utc_dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S+0000")
    return support.utc_to_local(utc_dt=utc_dt).strftime("%A, %B %d %Y - %I:%M %p")


def report(status_data: Dict[str, Union[str, Union[Dict[str, str]]]],
           subscription_data: List[Dict[str, str]],
           attributes: Dict[str, Union[List[Dict[str, str]], Dict[str, str]]]) -> str:
    """Generates a report based on the vehicle's status and sends an email notification.

    Args:
        status_data: Raw status data.
        subscription_data: Raw subscription data.
        attributes: Raw attributes data.

    Returns:
        str:
        Response to the user.
    """
    default_dt_string = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0000")
    report_time = convert_dt_report(dt_string=status_data.get('lastUpdatedTime', default_dt_string))
    overall_status = {'alerts': [], 'subscriptions': [], 'status': {}}
    overall_status['status']: Dict[str, str]
    overall_status['alerts']: List[Dict[str, str]]
    overall_status['subscriptions']: List[Dict[str, List[str]]]
    for alert in status_data.get('vehicleAlerts', [{}]):
        if alert.get('active', False) and alert.get('value', 'false') == 'true':
            alert['lastUpdatedTime'] = convert_dt_report(dt_string=alert.get('lastUpdatedTime', default_dt_string))
            overall_status['alerts'].append({alert['key']: alert['lastUpdatedTime']})
    for status in status_data.get('vehicleStatus', {}):
        for dict_ in status_data['vehicleStatus'].get(status, [{}]):
            if dict_.get('key', '') in ("SRS_STATUS", "DOOR_IS_ALL_DOORS_LOCKED"):
                overall_status['status'][dict_['key']] = dict_['value']
            if dict_.get('key', '') == "ENGINE_COOLANT_TEMP":
                overall_status['status'][dict_['key']] = f"{dict_['value']}\N{DEGREE SIGN}F"
            if dict_.get('key', '') == f"ODOMETER_{models.env.distance_unit.upper()}":
                overall_status['status'][dict_['key']] = f"{int(dict_['value']):02,} {models.env.distance_unit}"
            if dict_.get('key', '') == "FUEL_LEVEL_PERC":
                overall_status['status'][dict_['key']] = dict_['value'] + '%'
            if dict_.get('key', '') == "BATTERY_VOLTAGE":
                overall_status['status'][dict_['key']] = dict_['value'] + 'v'
            if dict_.get('key', '') == "DISTANCE_TO_EMPTY_FUEL":
                distance_to_empty_fuel = float(dict_['value'])
                if models.env.distance_unit == models.DistanceUnits.MILES:  # Convert to miles if custom unit is set
                    distance_to_empty_fuel = util.kms_to_miles(float(dict_['value']))
                overall_status['status'][dict_['key']] = f"{int(distance_to_empty_fuel):02,} {models.env.distance_unit}"
            if dict_.get('key', '') in ["TYRE_PRESSURE_FRONT_LEFT", "TYRE_PRESSURE_FRONT_RIGHT",
                                        "TYRE_PRESSURE_REAR_LEFT", "TYRE_PRESSURE_REAR_RIGHT"]:
                overall_status['status'][dict_['key']] = f"{round(int(dict_['value']) * 14.696 / 100)} psi"
    for package in subscription_data:
        expiration_date = package.get('expirationDate')
        name = package.get('name')
        pkg_status = package.get('status')
        if name and pkg_status and expiration_date:
            overall_status['subscriptions'].append({name: [convert_dt_report(dt_string=expiration_date), pkg_status]})
    if overall_status['status']:  # sort dict by key
        overall_status['status'] = dict(sorted(overall_status['status'].items()))
    if overall_status['alerts']:  # sort list of dict by the key in each dict
        overall_status['alerts'] = sorted(overall_status['alerts'], key=lambda d: list(d.keys()))
    if overall_status['subscriptions']:  # sort list of dict by the key in each dict
        overall_status['subscriptions'] = sorted(overall_status['subscriptions'], key=lambda d: list(d.values())[0])
    logger.debug(overall_status)
    template = jinja2.Template(templates.EmailTemplates.car_report)
    rendered = template.render(title=f"Last Connected: {report_time}",
                               alerts=overall_status['alerts'] or [{'ALL_OK': report_time}],
                               status=overall_status['status'] or {'NOTHING_TO_REPORT': report_time},
                               subscriptions=overall_status['subscriptions'] or [{'NO_SUBSCRIPTIONS': ['N/A', 'N/A']}])
    car_name = f"{attributes.get('vehicleBrand', 'Car')} " \
               f"{attributes.get('vehicleType', '')} " \
               f"{attributes.get('modelYear', '')}"
    mail_obj = gmailconnector.SendEmail(gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
    response = mail_obj.send_email(subject=f"{car_name} Report - {datetime.now().strftime('%c')}",
                                   sender="Jarvis", html_body=rendered, recipient=models.env.recipient)
    if response.ok:
        logger.info("Report has been sent via email.")
        return f"Vehicle report has been sent via email {models.env.title}!"
    else:
        logger.error("Failed to send report.")
        logger.error(response.json())
        return f"Failed to send the vehicle report {models.env.title}! Please check the logs for more information."


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
        # no need to check for expiration as connection will be reset in connector module
        if not CONNECTION.connection:
            create_connection()
        control = controller.Control(connection=CONNECTION.connection, vin=CONNECTION.vin)
        attributes = ThreadPool(processes=1).apply_async(func=control.get_attributes)
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
            until = support.utc_to_local(utc_dt=utc_dt).strftime("%A, %B %d, %I:%M %p")
            return f"Guardian mode is already enabled until {until} {util.get_timezone()} {models.env.title}!"
        elif operation == "HONK":
            response = control.honk_blink()
        elif operation == "LOCATE" or operation == "LOCATE_INTERNAL":
            if not (position := control.get_position().get('position')):
                logger.error("Unable to get position of the vehicle.")
                return
            logger.info("latitude: %f, longitude: %f", position['latitude'], position['longitude'])
            data = location.get_location_from_coordinates(coordinates=(position['latitude'], position['longitude']))
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
        elif operation == "REPORT":
            status = ThreadPool(processes=1).apply_async(func=control.get_status)
            subscriptions = ThreadPool(processes=1).apply_async(func=control.get_subscription_packages)
            attributes = attributes.get()
            status = status.get()
            subscriptions = subscriptions.get()
            return report(status_data=status, subscription_data=subscriptions, attributes=attributes)
        if response and response.get("failureDescription"):
            logger.critical(response)
            return
        try:
            car_name = attributes.get(timeout=3).get("vehicleBrand", "car")
        except ThreadTimeoutError as error:
            logger.error(error)
            car_name = "car"
        return car_name
    except EgressErrors as error:
        # Happens when security mode is already enabled
        if operation == "SECURE" and \
                error.__dict__.get('response') and \
                error.__dict__['response'].status_code == 409 and \
                control and retry:
            return vehicle(operation="SECURE_EXIST", retry=False)
        logger.error(error)
        logger.error("Failed to connect while performing %s", operation)
