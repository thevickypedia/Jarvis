import json
import os
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from logging import Logger
from math import floor, log
from platform import platform
from resource import RUSAGE_SELF, getrusage
from shutil import disk_usage
from socket import AF_INET, SOCK_DGRAM, gethostname, socket
from subprocess import PIPE, Popen, check_output
from typing import Union
from urllib.error import HTTPError
from urllib.request import urlopen

import yaml
from appscript import app as apple_script
from gmailconnector.send_email import SendEmail
from holidays import CountryHoliday
from psutil import cpu_count, virtual_memory
from pyicloud import PyiCloudService
from pyicloud.services.findmyiphone import AppleDevice
from vpn.controller import VPNServer

from modules.car.car_connector import Connect
from modules.car.car_controller import Control
from modules.notifications.notify import notify


class Helper:
    """Class for methods that support functions within Jarvis.

    >>> Helper

    """

    def __init__(self, logger: Logger):
        """Instantiates the ``Helper`` object.

        Args:
            logger: Logger module.
        """
        self.logger = logger

    def get_ssid(self) -> str:
        """Gets SSID of the network connected.

        Returns:
            str:
            Wi-Fi or Ethernet SSID.
        """
        process = Popen(
            ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
            stdout=PIPE)
        out, err = process.communicate()
        if error := process.returncode:
            self.logger.error(f"Failed to fetch SSID with exit code: {error}\n{err}")
        # noinspection PyTypeChecker
        return dict(map(str.strip, info.split(': ')) for info in out.decode('utf-8').splitlines()[:-1] if
                    len(info.split()) == 2).get('SSID')

    def threat_notify(self, converted: str, date_extn: Union[str, None], gmail_user: str, gmail_pass: str,
                      phone_number: str, recipient: str) -> None:
        """Sends an SMS and email notification in case of a threat.

        References:
            Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS and email.

        Args:
            converted: Takes the voice recognized statement as argument.
            date_extn: Name of the attachment file which is the picture of the intruder.
            gmail_user: Email address for the gmail account.
            gmail_pass: Password of the gmail account.
            phone_number: Phone number to send SMS.
            recipient: Email address of the recipient.
        """
        dt_string = f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}"
        title_ = f'Intruder Alert on {dt_string}'

        if converted:
            notify(user=gmail_user, password=gmail_pass, number=phone_number, subject="!!INTRUDER ALERT!!",
                   body=f"{dt_string}\n{converted}")
            body_ = f"""<html><head></head><body><h2>Conversation of Intruder:</h2><br>{converted}<br><br>
                                        <h2>Attached is a photo of the intruder.</h2>"""
        else:
            notify(user=gmail_user, password=gmail_pass, number=phone_number, subject="!!INTRUDER ALERT!!",
                   body=f"{dt_string}\nCheck your email for more information.")
            body_ = """<html><head></head><body><h2>No conversation was recorded,
                                    but attached is a photo of the intruder.</h2>"""
        if date_extn:
            attachment_ = f'threat/{date_extn}.jpg'
            response_ = SendEmail(gmail_user=gmail_user, gmail_pass=gmail_pass,
                                  recipient=recipient, subject=title_, body=body_, attachment=attachment_).send_email()
            if response_.ok:
                self.logger.info('Email has been sent!')
            else:
                self.logger.error(f"Email dispatch failed with response: {response_.body}\n")

    def offline_communicator_initiate(self, offline_host: str, offline_port: int, home: str) -> None:
        """Initiates Jarvis API and Ngrok for requests from external sources if they aren't running already.

        Notes:
            - ``forever_ngrok.py`` is a simple script that triggers ngrok connection in the port ``4483``.
            - The connection is tunneled through a public facing URL used to make ``POST`` requests to Jarvis API.
            - ``uvicorn`` command launches JarvisAPI ``fast.py`` using the same port ``4483``
        """
        ngrok_status, api_status = False, False
        targets = ['forever_ngrok.py', 'fast.py']
        for target_script in targets:
            pid_check = check_output(f"ps -ef | grep {target_script}", shell=True)
            pid_list = pid_check.decode('utf-8').split('\n')
            for id_ in pid_list:
                if id_ and 'grep' not in id_ and '/bin/sh' not in id_:
                    if target_script == 'forever_ngrok.py':
                        ngrok_status = True
                        self.logger.info('An instance of ngrok connection for offline communicator is running already.')
                    elif target_script == 'fast.py':
                        api_status = True
                        self.logger.info('An instance of Jarvis API for offline communicator is running already.')

        activator = 'source venv/bin/activate'
        if not ngrok_status:
            if os.path.exists(f"{home}/JarvisHelper"):
                self.logger.info('Initiating ngrok connection for offline communicator.')
                initiate = f'cd {home}/JarvisHelper && {activator} && export port={offline_port} && python {targets[0]}'
                apple_script('Terminal').do_script(initiate)
            else:
                self.logger.error(f'JarvisHelper is not available to trigger an ngrok tunneling through {offline_port}')
                endpoint = rf'http:\\{offline_host}:{offline_port}'
                self.logger.error(f'However offline communicator can still be accessed via '
                                  f'{endpoint}\\offline-communicator for API calls and {endpoint}\\docs for docs.')

        if not api_status:
            self.logger.info('Initiating FastAPI for offline listener.')
            offline_script = f'cd {os.getcwd()} && {activator} && cd api && python {targets[1]}'
            apple_script('Terminal').do_script(offline_script)

    @staticmethod
    def celebrate() -> str:
        """Function to look if the current date is a holiday or a birthday.

        Returns:
            str:
            A string of the event observed today.
        """
        day = datetime.today().date()
        today = datetime.now().strftime("%d-%B")
        us_holidays = CountryHoliday('US').get(day)  # checks if the current date is a US holiday
        in_holidays = CountryHoliday('IND', prov='TN', state='TN').get(day)  # checks if Indian (esp TN) holiday
        if in_holidays:
            return in_holidays
        elif us_holidays and 'Observed' not in us_holidays:
            return us_holidays
        elif (birthday := os.environ.get('birthday')) and today == birthday:
            return 'Birthday'

    @staticmethod
    def part_of_day() -> str:
        """Checks the current hour to determine the part of day.

        Returns:
            str:
            Morning, Afternoon, Evening or Night based on time of day.
        """
        current_hour = int(datetime.now().strftime("%H"))
        if 5 <= current_hour <= 11:
            return 'Morning'
        if 12 <= current_hour <= 15:
            return 'Afternoon'
        if 16 <= current_hour <= 19:
            return 'Evening'
        return 'Night'

    @staticmethod
    def time_converter(seconds: float) -> str:
        """Modifies seconds to appropriate days/hours/minutes/seconds.

        Args:
            seconds: Takes number of seconds as argument.

        Returns:
            str:
            Seconds converted to days or hours or minutes or seconds.
        """
        days = round(seconds // 86400)
        seconds = round(seconds % (24 * 3600))
        hours = round(seconds // 3600)
        seconds %= 3600
        minutes = round(seconds // 60)
        seconds %= 60
        if days:
            return f'{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds'
        elif hours:
            return f'{hours} hours, {minutes} minutes, and {seconds} seconds'
        elif minutes:
            return f'{minutes} minutes, and {seconds} seconds'
        elif seconds:
            return f'{seconds} seconds'

    @staticmethod
    def get_capitalized(phrase: str, dot: bool = True) -> str:
        """Looks for words starting with an upper-case letter.

        Args:
            phrase: Takes input string as an argument.
            dot: Takes a boolean flag whether to include words separated by (.) dot.

        Returns:
            str:
            Returns the upper case words if skimmed.
        """
        place = ''
        for word in phrase.split():
            if word[0].isupper():
                place += word + ' '
            elif '.' in word and dot:
                place += word + ' '
        if place:
            return place

    @staticmethod
    def unrecognized_dumper(train_data: dict) -> None:
        """If none of the conditions are met, converted text is written to a yaml file for training purpose.

        Args:
            train_data: Takes the dictionary that has to be written as an argument.
        """
        dt_string = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")
        if os.path.isfile('training_data.yaml'):
            with open('training_data.yaml') as reader:
                data = yaml.safe_load(stream=reader) or {}
            for key, value in train_data.items():
                if data.get(key):
                    data[key].update({dt_string: value})
                else:
                    data.update({key: {dt_string: value}})
        else:
            data = {key1: {dt_string: value1} for key1, value1 in train_data.items()}

        with open('training_data.yaml', 'w') as writer:
            yaml.dump(data=data, stream=writer)

    @staticmethod
    def size_converter(byte_size: int) -> str:
        """Gets the current memory consumed and converts it to human friendly format.

        Args:
            byte_size: Receives byte size as argument.

        Returns:
            str:
            Converted understandable size.
        """
        if not byte_size:
            byte_size = getrusage(RUSAGE_SELF).ru_maxrss
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        integer = int(floor(log(byte_size, 1024)))
        power = pow(1024, integer)
        size = round(byte_size / power, 2)
        return f'{size} {size_name[integer]}'

    def system_info_gatherer(self) -> str:
        """Gets the system configuration.

        Returns:
            str:
            A string with the message that has to be spoken.
        """
        total, used, free = disk_usage("/")
        total = self.size_converter(total)
        used = self.size_converter(used)
        free = self.size_converter(free)
        ram = self.size_converter(virtual_memory().total).replace('.0', '')
        ram_used = self.size_converter(virtual_memory().percent).replace(' B', ' %')
        physical = cpu_count(logical=False)
        logical = cpu_count(logical=True)
        o_system = platform().split('.')[0]
        return f"You're running {o_system}, with {physical} physical cores and {logical} logical cores. " \
               f"Your physical drive capacity is {total}. You have used up {used} of space. Your free space is " \
               f"{free}. Your RAM capacity is {ram}. You are currently utilizing {ram_used} of your memory."

    def hosted_device_info(self) -> dict:
        """Gets basic information of the hosted device.

        Returns:
            dict:
            A dictionary of key-value pairs with device type, operating system, os version.
        """
        system_kernel = (check_output("sysctl hw.model", shell=True)).decode('utf-8').splitlines()  # gets model info
        device = self.extract_str(system_kernel[0].split(':')[1])
        platform_info = platform().split('-')
        version = '.'.join(platform_info[1].split('.')[0:2])
        return {'device': device, 'os_name': platform_info[0], 'os_version': float(version)}

    @staticmethod
    def extract_nos(input_: str) -> float:
        """Extracts number part from a string.

        Args:
            input_: Takes string as an argument.

        Returns:
            float:
            Float values.
        """
        if value := re.findall(r"\d+", input_):
            return float('.'.join(value))

    @staticmethod
    def format_nos(input_: float) -> int:
        """Removes ``.0`` float values.

        Args:
            input_: Int if found, else returns the received float value.

        Returns:
            int:
            Formatted integer.
        """
        return int(input_) if isinstance(input_, float) and input_.is_integer() else input_

    @staticmethod
    def extract_str(input_: str) -> str:
        """Extracts strings from the received input.

        Args:
            input_: Takes a string as argument.

        Returns:
            str:
            A string after removing special characters.
        """
        return ''.join([i for i in input_ if not i.isdigit() and i not in [',', '.', '?', '-', ';', '!', ':']]).strip()

    @staticmethod
    def stop_terminal() -> None:
        """Uses pid to kill terminals as terminals await user confirmation interrupting shutdown/restart."""
        pid_check = check_output("ps -ef | grep 'iTerm\\|Terminal'", shell=True)
        pid_list = pid_check.decode('utf-8').split('\n')
        for id_ in pid_list:
            if id_ and 'Applications' in id_ and '/usr/bin/login' not in id_:
                os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout

    @staticmethod
    def remove_files() -> None:
        """Function that deletes multiple files when called during exit operation.

        Warnings:
            Deletes:
                - all ``.lock`` files created for alarms and reminders.
                - ``location.yaml`` file, to recreate a new one next time around.
                - ``meetings`` file, to recreate a new one next time around.
        """
        os.removedirs('alarm') if os.path.isdir('alarm') else None
        os.removedirs('reminder') if os.path.isdir('reminder') else None
        os.remove('location.yaml') if os.path.isfile('location.yaml') else None
        os.remove('meetings') if os.path.isfile('meetings') else None

    @staticmethod
    def vpn_checker() -> str:
        """Uses simple check on network id to see if it is connected to local host or not.

        Returns:
            str:
            Private IP address of host machine.
        """
        socket_ = socket(AF_INET, SOCK_DGRAM)
        socket_.connect(("8.8.8.8", 80))
        ip_address = socket_.getsockname()[0]
        socket_.close()
        if not (ip_address.startswith('192') | ip_address.startswith('127')):
            ip_address = 'VPN:' + ip_address
            info = json.load(urlopen('https://ipinfo.io/json'))
            sys.stdout.write(f"\rVPN connection is detected to {info.get('ip')} at {info.get('city')}, "
                             f"{info.get('region')} maintained by {info.get('org')}")
        return ip_address

    @staticmethod
    def device_selector(icloud_user: str, icloud_pass: str, converted: str = None) -> Union[AppleDevice, None]:
        """Selects a device using the received input string.

        See Also:
            - Opens a html table with the index value and name of device.
            - When chosen an index value, the device name will be returned.

        Args:
            icloud_user: Username for Apple iCloud account.
            icloud_pass: Password for Apple iCloud account.
            converted: Takes the voice recognized statement as argument.

        Returns:
            AppleDevice:
            Returns the selected device from the class ``AppleDevice``
        """
        if not all([icloud_user, icloud_pass]):
            return
        icloud_api = PyiCloudService(icloud_user, icloud_pass)
        devices = [device for device in icloud_api.devices]
        if converted:
            devices_str = [{str(device).split(':')[0].strip(): str(device).split(':')[1].strip()} for device in devices]
            closest_match = [
                (SequenceMatcher(a=converted, b=key).ratio() + SequenceMatcher(a=converted, b=val).ratio()) / 2
                for device in devices_str for key, val in device.items()]
            index = closest_match.index(max(closest_match))
            target_device = icloud_api.devices[index]
        else:
            target_device = [device for device in devices if device.get('name') == gethostname() or
                             gethostname() == device.get('name') + '.local'][0]
        return target_device if target_device else icloud_api.iphone

    @staticmethod
    def lock_files(alarm_files: bool = False, reminder_files: bool = False) -> list:
        """Checks for ``*.lock`` files within the ``alarm`` directory if present.

        Args:
            alarm_files: Takes a boolean value to gather list of alarm lock files.
            reminder_files: Takes a boolean value to gather list of reminder lock files.

        Returns:
            list:
            List of ``*.lock`` file names ignoring other hidden files.
        """
        if alarm_files:
            return [f for f in os.listdir('alarm') if not f.startswith('.')] if os.path.isdir('alarm') else None
        elif reminder_files:
            return [f for f in os.listdir('reminder') if not f.startswith('.')] if os.path.isdir('reminder') else None

    @staticmethod
    def terminator() -> None:
        """Exits the process with specified status without calling cleanup handlers, flushing stdio buffers, etc.

        Using this, eliminates the hassle of forcing multiple threads to stop.

        Examples:
            - os._exit(0)
            - kill -15 `PID`
        """
        pid_check = check_output("ps -ef | grep jarvis.py", shell=True)
        pid_list = pid_check.decode('utf-8').splitlines()
        for pid_info in pid_list:
            if pid_info and 'grep' not in pid_info and '/bin/sh' not in pid_info:
                os.system(f'kill -15 {pid_info.split()[1].strip()}')

    def exit_message(self) -> str:
        """Variety of exit messages based on day of week and time of day.

        Returns:
            str:
            A greeting bye message.
        """
        am_pm = datetime.now().strftime("%p")  # current part of day (AM/PM)
        hour = datetime.now().strftime("%I")  # current hour
        day = datetime.now().strftime("%A")  # current day

        if am_pm == 'AM' and int(hour) < 10:
            exit_msg = f"Have a nice day, and happy {day}."
        elif am_pm == 'AM' and int(hour) >= 10:
            exit_msg = f"Enjoy your {day}."
        elif am_pm == 'PM' and (int(hour) == 12 or int(hour) < 3) and day in ['Friday', 'Saturday']:
            exit_msg = "Have a nice afternoon, and enjoy your weekend."
        elif am_pm == 'PM' and (int(hour) == 12 or int(hour) < 3):
            exit_msg = "Have a nice afternoon."
        elif am_pm == 'PM' and int(hour) < 6 and day in ['Friday', 'Saturday']:
            exit_msg = "Have a nice evening, and enjoy your weekend."
        elif am_pm == 'PM' and int(hour) < 6:
            exit_msg = "Have a nice evening."
        elif day in ['Friday', 'Saturday']:
            exit_msg = "Have a nice night, and enjoy your weekend."
        else:
            exit_msg = "Have a nice night."

        if event := self.celebrate():
            exit_msg += f'\nAnd by the way, happy {event}'

        return exit_msg

    def vehicle(self, car_email, car_pass, car_pin, operation: str, temp: int = None) -> Union[str, None]:
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
            connection = Connect(username=car_email, password=car_pass, logger=self.logger)
            connection.connect()
            if not connection.head:
                return
            vehicles = connection.get_vehicles(headers=connection.head).get('vehicles')
            primary_vehicle = [vehicle for vehicle in vehicles if vehicle.get('role') == 'Primary'][0]
            controller = Control(vin=primary_vehicle.get('vin'), connection=connection)

            if operation == 'LOCK':
                controller.lock(pin=car_pin)
            elif operation == 'UNLOCK':
                controller.unlock(pin=car_pin)
            elif operation == 'START':
                controller.remote_engine_start(pin=car_pin, target_temperature=temp)
            elif operation == 'STOP':
                controller.remote_engine_stop(pin=car_pin)
            elif operation == 'SECURE':
                controller.enable_guardian_mode(pin=car_pin)
            return os.environ.get('car_name', controller.get_attributes().get('vehicleBrand', 'car'))
        except HTTPError as error:
            self.logger.error(error)

    @staticmethod
    def vpn_server_switch(operation: str, phone_number: str, recipient: str) -> None:
        """Automator to ``START`` or ``STOP`` the VPN portal.

        Args:
            operation: Takes ``START`` or ``STOP`` as an argument.
            phone_number: Phone number to which the notification has to be sent.
            recipient: Email address to which the notification has to be sent.

        See Also:
            - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
        """
        os.environ['VPN_LIVE'] = 'True'
        vpn_object = VPNServer(vpn_username=os.environ.get('vpn_username', os.environ.get('USER', 'openvpn')),
                               vpn_password=os.environ.get('vpn_password', 'aws_vpn_2021'), log='FILE',
                               gmail_user=os.environ.get('offline_user', os.environ.get('gmail_user')),
                               gmail_pass=os.environ.get('offline_pass', os.environ.get('gmail_pass')),
                               phone=phone_number, recipient=recipient)
        if operation == 'START':
            vpn_object.create_vpn_server()
        elif operation == 'STOP':
            vpn_object.delete_vpn_server()
        del os.environ['VPN_LIVE']
