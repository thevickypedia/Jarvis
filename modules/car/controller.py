"""**API Reference:** https://documenter.getpostman.com/view/6250319/RznBMzqo for Jaguar LandRover InControl API."""

import time
from typing import Union

from modules.car.connector import Connect

DEFAULT_CONTENT_TYPE = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"


class Control:
    """Initiates Vehicle object to perform remote actions after connecting to the InControl API.

    >>> Control

    """

    def __init__(self, vin: str, connection: Connect):
        """Instantiates a super class with incoming data and existing connection.

        Args:
            vin: Takes the vehicle's VIN as an argument.
            connection: Takes the connection object as an argument.
        """
        self.connection = connection
        self.vin = vin
        self.IF9_BASE_URL = f'https://if9.prod-row.jlrmotor.com/if9/jlr/vehicles/{self.vin}'

    def get_contact_info(self, mcc: str = '+1') -> dict:
        """Get Road Side Assistance and Secure Vehicle Tracker contact information.

        Args:
            mcc: Mobile Country Code. Defaults to +1 (USA).

        Returns:
            dict:
            A dictionary of contact info.
        """
        headers = self.connection.head.copy()
        return self.post_data(command=f'contactinfo/{mcc}', headers=headers)

    def get_attributes(self) -> dict:
        """Requests all vehicle attributes.

        Returns:
            dict:
            A dictionary of all attributes of the vehicle as key value pairs.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.VehicleAttributes-v3+json"
        return self.post_data(command='attributes', headers=headers)

    def get_status(self, ev: bool = False) -> dict:
        """Makes a call to get the status of the vehicle.

        Args:
            ev: Takes a boolean flag if the vehicle is EV.

        Returns:
            dict:
            A dictionary of the vehicle's status information.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.if9.healthstatus-v3+json"
        result = self.post_data(command='status?includeInactive=true', headers=headers)

        if ev:
            core_status_list = result['vehicleStatus']['coreStatus']
            ev_status_list = result['vehicleStatus']['evStatus']
            core_status_list = core_status_list + ev_status_list
            return {d['key']: d['value'] for d in core_status_list}

        return result

    def get_health_status(self) -> dict:
        """Checks for the vehicle health status.

        Returns:
            dict:
            A dictionary of the status report.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        headers["Content-Type"] = DEFAULT_CONTENT_TYPE
        vhs_data = self._authenticate_service(service_name="VHS")
        return self.post_data(command='healthstatus', headers=headers, data=vhs_data)

    def get_departure_timers(self) -> dict:
        """Get departure timers for specified vehicle.

        Returns:
            dict:
            A dictionary of the departure timer information.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.DepartureTimerSettings-v1+json"
        return self.post_data(command="departuretimers", headers=headers)

    def get_wakeup_time(self) -> dict:
        """Get configured wakeup time for specified vehicle.

        Returns:
            dict:
            A dictionary of wakeup time information.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.VehicleWakeupTime-v2+json"
        return self.post_data(command="wakeuptime", headers=headers)

    def get_subscription_packages(self) -> list:
        """Get list of subscription packages for a specific vehicle.

        Returns:
            list:
            A list of all subscription packages along with their status and expiration.
        """
        return self.post_data(command='subscriptionpackages',
                              headers=self.connection.head).get('subscriptionPackages', [])

    def get_trips(self, count: int = 1_000) -> list:
        """Get the trips associated with the specified vehicle.

        Args:
            count: Defaults to the last 1,000 trips.

        Returns:
            list:
            List of all trips information.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.triplist-v2+json"
        return self.post_data(command=f'trips?count={count}', headers=headers).get('trips', [])

    def get_guardian_mode_alarms(self) -> list:
        """Gets all the scheduled Guardian mode time periods.

        Returns:
            list:
            Returns a list of Guardian Mode alarm schedules.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianStatus-v1+json"
        headers["Accept-Encoding"] = "gzip,deflate"
        return self.post_data(command='gm/alarms', headers=headers)

    def get_guardian_mode_alerts(self):
        """Gets the latest Guardian Mode alert for the specified vehicle.

        Returns:
            Returns the latest Guardian Mode alert for the specified vehicle.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/wirelesscar.GuardianAlert-v1+json"
        headers["Accept-Encoding"] = "gzip,deflate"
        return self.post_data(command='gm/alerts', headers=headers)

    def get_guardian_mode_status(self) -> dict:
        """Get the Guardian Mode status indicating whether Guardian Mode is active.

        Returns:
            dict:
            Status of guardian mode as a dictionary.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianStatus-v1+json"
        return self.post_data(command='gm/status', headers=headers)

    def get_guardian_mode_settings_user(self) -> dict:
        """Alarm, SMS and push notification settings (System) for guardian mode.

        Returns:
            dict:
            A dictionary of current settings.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianUserSettings-v1+json"
        return self.post_data(command='gm/settings/user', headers=headers)

    def get_guardian_mode_settings_system(self) -> dict:
        """Alarm, SMS and push notification settings (User) for guardian mode.

        Returns:
            dict:
            A dictionary of current settings.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianSystemSettings-v1+json"
        return self.post_data(command='gm/settings/system', headers=headers)

    def get_trip(self, trip_id: int, page: int = 1) -> dict:
        """Get data associated with a specific trip.

        Args:
            trip_id: A valid vehicle trip id should be passed.
            page: Page ID.

        Returns:
            dict:
            A dictionary of the trip information.
        """
        return self.post_data(command=f'trips/{trip_id}/route?pageSize=1000&page={page}',
                              headers=self.connection.head)

    def get_position(self) -> dict:
        """Get the current position of the vehicle.

        Returns:
            dict:
            A dictionary of the current position of the vehicle.
        """
        return self.post_data(command='position', headers=self.connection.head)

    def get_services(self) -> dict:
        """Get the service history of the vehicle.

        Returns:
            dict:
            A dictionary of the service information.
        """
        return self.post_data(command="services", headers=self.connection.head.copy())

    def get_service_status(self, service_id: str) -> dict:
        """Get a particular service information of the vehicle.

        Args:
            service_id: ID of the particular service.

        Returns:
            dict:
            A dictionary of the service information.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        return self.post_data(command=f'services/{service_id}', headers=headers)

    def get_rcc_target_value(self):
        """Get target temperature for the Vehicle climate.

        Returns:
            dict:
            A dictionary of the target temperature information.
        """
        return self.post_data(command='settings/ClimateControlRccTargetTemp', headers=self.connection.head.copy())

    def set_attributes(self, nickname: str, registration_number: str) -> None:
        """Set attributes for the vehicle profile.

        Args:
            nickname: Nickname for the vehicle.
            registration_number: License plate number.
        """
        attributes_data = {
            "nickname": nickname,
            "registrationNumber": registration_number
        }
        self.post_data(command="attributes", headers=self.connection.head, data=attributes_data)

    def lock(self, pin: int) -> None:
        """Lock the vehicle.

        Args:
            pin: Master PIN of the vehicle.
        """
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v2+json"
        rdl_data = self._authenticate_service(pin=pin, service_name="RDL")
        self.post_data(command="lock", headers=headers, data=rdl_data)

    def unlock(self, pin: int) -> None:
        """Unlock the vehicle.

        Args:
            pin: Master PIN of the vehicle.
        """
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v2+json"
        self.post_data(command="unlock", headers=headers,
                       data=self._authenticate_service(pin=pin, service_name="RDU"))

    def reset_alarm(self, pin: int) -> None:
        """Reset the vehicle alarm.

        Args:
            pin: Master PIN of the vehicle.
        """
        headers = self.connection.head.copy()
        headers["Content-Type"] = DEFAULT_CONTENT_TYPE
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        self.post_data(command="unlock", headers=headers,
                       data=self._authenticate_service(pin=pin, service_name="ALOFF"))

    def honk_blink(self) -> None:
        """Honk the horn and flash the lights associated with the specified vehicle."""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        headers["Content-Type"] = DEFAULT_CONTENT_TYPE
        self.post_data(command="honkBlink", headers=headers,
                       data=self._authenticate_vin_protected_service(service_name="HBLF"))

    def remote_engine_start(self, pin: int, target_temperature: int) -> None:
        """Starts the vehicle remotely.

        Args:
            pin: Master PIN of the vehicle.
            target_temperature: Target temperature when started.
        """
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v2+json"
        self.set_rcc_target_temperature(pin=pin, target_temperature=target_temperature)
        self.post_data(command="engineOn", headers=headers,
                       data=self._authenticate_service(pin=pin, service_name="REON"))

    def remote_engine_stop(self, pin: int) -> None:
        """Turn off the vehicle remotely.

        Args:
            pin: Master PIN of the vehicle.
        """
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v2+json"
        self.post_data(command="engineOff", headers=headers,
                       data=self._authenticate_service(pin=pin, service_name="REOFF"))

    def set_rcc_target_temperature(self, pin: int, target_temperature: int) -> None:
        """Set climate control with a target temperature.

        Args:
            pin: Master PIN of the vehicle.
            target_temperature: Target temperature that has to be set.
        """
        headers = self.connection.head.copy()
        self._prov_command(pin=pin, expiration_time=None, mode="provisioning")
        service_parameters = {
            "key": "ClimateControlRccTargetTemp",
            "value": str(target_temperature),
            "applied": 1
        }
        self.post_data(command="settings", headers=headers, data=service_parameters)

    def preconditioning_start(self, celsius: float) -> dict:
        """Start the climate preconditioning at the specified temperature.

        Notes:
            Note the absence of the decimal sign. 210 equals 21.0C.
            Pass 155 for LO and 285 for HI.

        Args:
            celsius: Celsius without the decimal sign.

        Returns:
            dict:
            A dictionary response.
        """
        service_parameters = [
            {
                "key": "PRECONDITIONING",
                "value": "START"
            },
            {
                "key": "TARGET_TEMPERATURE_CELSIUS",
                "value": celsius
            }
        ]
        return self._preconditioning_control(service_parameters=service_parameters)

    def preconditioning_stop(self):
        """Stop the climate preconditioning immediately.

        Returns:
            dict:
            A dictionary response.
        """
        service_parameters = [
            {
                "key": "PRECONDITIONING",
                "value": "STOP"
            }
        ]
        return self._preconditioning_control(service_parameters=service_parameters)

    def climate_prioritize(self, priority: str) -> dict:
        """Prioritize climate controls for either range or comfort.

        Args:
            priority: Takes ``PRIORITIZE_RANGE`` or ``PRIORITIZE_COMFORT`` to prioritize either range or comfort.

        Returns:
            dict:
            A dictionary response.
        """
        service_parameters = [
            {
                "key": "PRIORITY_SETTING",
                "value": priority
            }
        ]
        return self._preconditioning_control(service_parameters=service_parameters)

    def _preconditioning_control(self, service_parameters: Union[list, dict]) -> dict:
        """Initiates climate pre-conditioning.

        Args:
            service_parameters: Service parameters for the climate setting.

        Returns:
            dict:
            A dictionary response.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v5+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.PhevService-v1+json; charset=utf-8"

        ecc_data = self._authenticate_vin_protected_service(service_name="ECC")
        ecc_data['serviceParameters'] = service_parameters
        return self.post_data(command="preconditioning", headers=headers, data=ecc_data)

    def charging_stop(self) -> None:
        """Stop charging the EV."""
        service_parameters = [
            {
                "key": "CHARGE_NOW_SETTING",
                "value": "FORCE_OFF"
            }
        ]
        self._charging_profile_control(service_parameter_key="serviceParameters", service_parameters=service_parameters)

    def charging_start(self) -> None:
        """Start charging the EV."""
        service_parameters = [
            {
                "key": "CHARGE_NOW_SETTING",
                "value": "FORCE_ON"
            }
        ]
        self._charging_profile_control(service_parameter_key="serviceParameters", service_parameters=service_parameters)

    def set_max_soc(self, max_charge_level: Union[int, float]) -> dict:
        """Set the maximum state of charge.

        Args:
            max_charge_level: Maximum charge level in percentage.

        See Also:
            The vehicle will never charge more than the specified charge level.

        Returns:
            dict:
            A dictionary response.
        """
        service_parameters = [
            {
                "key": "SET_PERMANENT_MAX_SOC",
                "value": max_charge_level
            }
        ]
        return self._charging_profile_control(service_parameter_key="serviceParameters",
                                              service_parameters=service_parameters)

    def set_one_off_max_soc(self, max_charge_level: Union[int, float]) -> dict:
        """Set the one-off maximum state of charge.

        Args:
            max_charge_level: Percentage of charge level.

        See Also:
            - The vehicle will not charge more than the specified charge level for the current charging session.
            - Will presumably reset to the previous value the next time the vehicle is connected to a charger.

        Returns:
            dict:
            A dictionary response.
        """
        service_parameters = [
            {
                "key": "SET_ONE_OFF_MAX_SOC",
                "value": max_charge_level
            }
        ]
        return self._charging_profile_control(service_parameter_key="serviceParameters",
                                              service_parameters=service_parameters)

    def add_departure_timer(self, index: int, year: int, month: int, day: int, hour: int, minute: int) -> dict:
        """Add a single departure timer for the specified vehicle.

        Args:
            index: Identifier.
            year: Intended timer year.
            month: Intended timer month.
            day: Intended timer day.
            hour: Intended timer hour.
            minute: Intended timer minute.

        See Also:
            - The departure timer is seemingly identifier by its numerical index value.
            - A unique index timer value must be specified when creating the departure timer.

        Returns:
            dict:
            A dictionary response.
        """
        departure_timer_setting = {
            "timers": [
                {
                    "departureTime": {
                        "hour": hour, "minute": minute
                    },
                    "timerIndex": index, "timerTarget": {
                        "singleDay": {
                            "day": day, "month": month, "year": year
                        }
                    }, "timerType": {
                        "key": "BOTHCHARGEANDPRECONDITION", "value": True
                    }
                }
            ]
        }
        return self._charging_profile_control(service_parameter_key="departureTimerSetting",
                                              service_parameters=departure_timer_setting)

    def add_repeated_departure_timer(self, index: int, schedule: dict, hour: int, minute: int) -> dict:
        """Add repeated departure timer for the specified vehicle.

        Args:
            index: Identifier.
            schedule: Which days of a week the departure timer should be active for.
            hour: Intended timer hour.
            minute: Intended timer minute.

        Examples:
            {'friday':True,'monday':True,'saturday':True,'sunday':False,'thursday':True,'tuesday':True,'wednesday':True}

        Returns:
            dict:
            A response dictionary.
        """
        departure_timer_setting = {
            "timers": [
                {
                    "departureTime": {
                        "hour": hour, "minute": minute
                    },
                    "timerIndex": index, "timerTarget":
                    {
                        "repeatSchedule": schedule
                    },
                    "timerType": {
                        "key": "BOTHCHARGEANDPRECONDITION", "value": True
                    }
                }
            ]
        }
        return self._charging_profile_control(service_parameter_key="departureTimerSetting",
                                              service_parameters=departure_timer_setting)

    def delete_departure_timer(self, index: int) -> dict:
        """Delete departure timers specified by their index.

        Args:
            index: Index to be deleted.

        Returns:
            dict:
            A dictionary response.
        """
        departure_timer_setting = {
            "timers": [
                {
                    "timerIndex": index
                }
            ]
        }
        return self._charging_profile_control(service_parameter_key="departureTimerSetting",
                                              service_parameters=departure_timer_setting)

    def add_charging_period(self, index: int, schedule: dict,
                            hour_from: int, minute_from: int, hour_to: int, minute_to: int) -> dict:
        """Set a time period for charging. The vehicle will prioritize charging during the specified period.

        Args:
            index: Identifier.
            schedule: Which days of a week the departure timer should be active for.
            hour_from: Starting hour.
            minute_from: Starting minute.
            hour_to: Ending hour.
            minute_to: Ending minute.

        Examples:
            {'friday':True,'monday':True,'saturday':True,'sunday':False,'thursday':True,'tuesday':True,'wednesday':True}

        Returns:
            dict:
            A dictionary response.
        """
        tariff_settings = {
            "tariffs": [
                {
                    "tariffIndex": index, "tariffDefinition": {
                        "enabled": True,
                        "repeatSchedule": schedule,
                        "tariffZone": [
                            {
                                "zoneName": "TARIFF_ZONE_A",
                                "bandType": "PEAK",
                                "endTime": {
                                    "hour": hour_from,
                                    "minute": minute_from
                                }
                            },
                            {
                                "zoneName": "TARIFF_ZONE_B",
                                "bandType": "OFFPEAK",
                                "endTime": {
                                    "hour": hour_to,
                                    "minute": minute_to
                                }
                            },
                            {
                                "zoneName": "TARIFF_ZONE_C",
                                "bandType": "PEAK",
                                "endTime": {
                                    "hour": 0,
                                    "minute": 0
                                }
                            }
                        ]
                    }
                }
            ]
        }
        return self._charging_profile_control(service_parameter_key="tariffSettings",
                                              service_parameters=tariff_settings)

    def _charging_profile_control(self, service_parameter_key: str, service_parameters: Union[dict, list]) -> dict:
        """Charging profile handler.

        Args:
            service_parameter_key: Parameter key.
            service_parameters: Parameter values.

        Returns:
            dict:
            A dictionary response.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v5+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.PhevService-v1+json; charset=utf-8"
        cp_data = self._authenticate_vin_protected_service(service_name="CP")
        cp_data[service_parameter_key] = service_parameters
        return self.post_data(command="chargeProfile", headers=headers, data=cp_data)

    def set_wakeup_time(self, wakeup_time: int) -> dict:
        """Set wakeup time.

        Args:
            wakeup_time: Epoch value for wake up start time.

        See Also:
            - The vehicle will enter a sleep mode after four days of inactivity.
            - In order to use remote control features after this time a wakeup timer is required.
            - Ensures vehicle is available for remote control for a period of time after the specified wakeup time.
            - Wakeup timer for a specific time has to be set before the vehicle enters sleep mode.

        Returns:
            dict:
            A dictionary response.
        """
        swu_data = self._authenticate_service(service_name="SWU")
        swu_data["serviceCommand"] = "START"
        swu_data["startTime"] = wakeup_time
        return self._set_wakeup(wakeup_data=swu_data)

    def delete_wakeup_time(self) -> dict:
        """Cancel the wakeup timer.

        Returns:
            dict:
            A dictionary response.
        """
        swu_data = self._authenticate_service(service_name="SWU")
        swu_data["serviceCommand"] = "END"
        return self._set_wakeup(wakeup_data=swu_data)

    def _set_wakeup(self, wakeup_data: dict) -> dict:
        """Handles setting wakeup timer.

        Args:
            wakeup_data: Data from wake up controllers.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v3+json"
        headers["Content-Type"] = DEFAULT_CONTENT_TYPE
        return self.post_data(command="swu", headers=headers, data=wakeup_data)

    def enable_service_mode(self, pin: int, expiration_time: Union[int, float] = None) -> dict:
        """Service Mode will allow the vehicle to be serviced without InControl triggering a vehicle theft alarm.

        Args:
            pin: Master PIN of the vehicle.
            expiration_time: Epoch value until when the service mode is to be disabled. Defaults to 24 hours.

        Returns:
            dict:
            A dictionary response.
        """
        return self._prov_command(pin=pin, expiration_time=expiration_time or int(time.time()) + 86_400,
                                  mode="protectionStrategy_serviceMode")

    def enable_guardian_mode(self, pin: int, expiration_time: Union[int, float] = None) -> dict:
        """Guardian Mode is a security feature that will generate alarms when vehicle interaction is detected.

        Args:
            pin: Master PIN of the vehicle.
            expiration_time: Epoch value until when the guardian mode is to be disabled. Defaults to 24 hours.

        See Also:
            - Guardian Mode will only generate a single alert.
            - The alert does not indicate what sort of interaction took place, just the timestamp.

        Returns:
            dict:
            A dictionary response.
        """
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianAlarmList-v1+json"
        gm_data = self._authenticate_service(pin=pin, service_name="GM")
        gm_data["endTime"] = expiration_time or int(time.time()) + 86_400
        gm_data["status"] = "ACTIVE"
        return self.post_data(command="gm/alarms", headers=headers, data=gm_data)

    def enable_transport_mode(self, pin: int, expiration_time: Union[int, float] = None) -> dict:
        """Allows the vehicle to be transported without InControl triggering a vehicle theft alarm.

        Args:
            pin: Master PIN of the vehicle.
            expiration_time: Epoch value until when the transport mode is to be disabled. Defaults to 24 hours.

        Returns:
            dict:
            A dictionary response.
        """
        return self._prov_command(pin=pin, expiration_time=expiration_time or int(time.time()) + 86_400,
                                  mode="protectionStrategy_transportMode")

    def enable_privacy_mode(self, pin: int) -> dict:
        """The vehicle will not log journey information as long as privacy mode is enabled.

        Args:
            pin: Master PIN of the vehicle.

        Returns:
            dict:
            A dictionary response.
        """
        return self._prov_command(pin=pin, expiration_time=None, mode="privacySwitch_on")

    def disable_privacy_mode(self, pin: int) -> dict:
        """The vehicle will resume journey information logging.

        Args:
            pin: Master PIN of the vehicle.

        Returns:
            dict:
            A dictionary response.
        """
        return self._prov_command(pin=pin, expiration_time=None, mode="privacySwitch_off")

    def _prov_command(self, pin: int, expiration_time: Union[int, float, None], mode: str) -> dict:
        """Performs ServiceConfiguration commands.

        Args:
            pin: Master PIN of the vehicle.
            expiration_time: Epoch value until when the said task has to be performed.
            mode: Task that has to be performed.

        Returns:
            dict:
            A dictionary response.
        """
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json"
        prov_data = self._authenticate_service(pin=pin, service_name="PROV")
        prov_data["serviceCommand"] = mode
        prov_data["startTime"] = None
        prov_data["endTime"] = expiration_time
        return self.post_data(command="prov", headers=headers, data=prov_data)

    def _authenticate_vin_protected_service(self, service_name: str) -> dict:
        """Authenticates services that use VIN for auth.

        Args:
            service_name: Name of the service that has to be authenticated.

        Returns:
            dict:
            A dictionary response.
        """
        return self._authenticate_service(pin=int(self.vin[-4:]), service_name=service_name)

    def _authenticate_service(self, service_name: str, pin: int = None):
        """Authenticate a service.

        Args:
            pin: Master PIN of the vehicle.
            service_name: Name of the service that has to be authenticated.

        Returns:
            dict:
            A dictionary response.
        """
        data = {
            "serviceName": service_name,
            "pin": pin
        }
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.AuthenticateRequest-v2+json; charset=utf-8"
        return self.post_data(command=f"users/{self.connection.user_id}/authenticate", headers=headers, data=data)

    def post_data(self, command: str, headers: dict, data: dict = None) -> Union[dict, list]:
        """Posts the data from ``Control`` module to ``Connect`` module.

        Args:
            command: Command to be performed.
            headers: Headers to be added in the outgoing request.
            data: Data to be passed in the outgoing request.
        """
        return self.connection.post_data(command=command, url=self.IF9_BASE_URL, headers=headers, data=data)
