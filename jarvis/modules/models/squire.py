import subprocess
from collections import ChainMap
from datetime import datetime
from typing import Dict, List

from jarvis.modules.exceptions import InvalidEnvVars
from jarvis.modules.peripherals import channel_type, get_audio_devices


def get_distributor_info_linux() -> Dict[str, str]:
    """Returns distributor information (i.e., Ubuntu) for Linux based systems.

    Returns:
        dict:
        A dictionary of key-value pairs with distributor id, name and version.
    """
    try:
        result = subprocess.check_output(
            "lsb_release -a", shell=True, stderr=subprocess.DEVNULL
        )
        return {
            i.split(":")[0].strip().lower().replace(" ", "_"): i.split(":")[1].strip()
            for i in result.decode(encoding="UTF-8").splitlines()
            if ":" in i
        }
    except (subprocess.SubprocessError, subprocess.CalledProcessError):
        return {}


def channel_validator(value: int, ch_type: str) -> int | None:
    """Channel validator for camera and microphone index.

    Args:
        value: Index of the device.
        ch_type: Input/output.

    Returns:
        int | PositiveInt | None:
        Returns the validated device index.
    """
    if ch_type == "input":
        channels = channel_type.input_channels
    else:
        channels = channel_type.output_channels
    if not value:
        return
    if int(value) in list(
        map(
            lambda tag: tag["index"],
            get_audio_devices(channels),
        )
    ):
        return value
    else:
        complicated = dict(
            ChainMap(
                *list(
                    map(
                        lambda tag: {tag["index"]: tag["name"]},
                        get_audio_devices(channels),
                    )
                )
            )
        )
        raise InvalidEnvVars(f"value should be one of {complicated}")


def parse_ignore_hours(
    value: List[int] | List[str] | str | int | List[int | str] | None,
) -> List[int]:
    """Parse the env var ``ignore_hours`` into a valid list.

    Args:
        value: Takes the value from env vars.

    Returns:
        List[int]:
        Returns a list of hours in HH format to ignore for background tasks.
    """
    if isinstance(value, int):
        if value < 0 or value > 24:
            raise ValueError("24h format cannot be less than 0 or greater than 24")
        value = [value]
    elif isinstance(value, str):
        form_list = value.split("-")
        if len(form_list) == 1:
            try:
                assert form_list[0].isdigit()
            except AssertionError:
                raise ValueError(
                    "string format can either be start-end (7-10) or just the hour by itself (7)"
                )
            else:
                value = [int(form_list[0])]
        elif len(form_list) == 2:
            value = handle_multiform(form_list)
        else:
            raise ValueError(
                "string format can either be start-end (7-10) or just the hour by itself (7)"
            )
    refined = []
    for multiple in value:
        if isinstance(multiple, str):
            # comes back as a list of string
            refined.extend(handle_multiform(multiple.split("-")))
        else:
            refined.append(multiple)
    if refined:
        value = refined
    for hour in value:
        try:
            datetime.strptime(str(hour), "%H")
        except ValueError:
            raise ValueError("ignore hours should be 24H format")
    return value


def handle_multiform(form_list: List[str]) -> List[int]:
    """Handles ignore_hours in the format 7-10.

    Args:
        form_list: Takes the split string as an argument.

    Returns:
        List[int]:
        List of hours as integers.

    Raises:
        ValueError:
        In case of validation errors.
    """
    form_list[0] = form_list[0].strip()
    form_list[1] = form_list[1].strip()
    try:
        assert form_list[0].isdigit()
        assert form_list[1].isdigit()
    except AssertionError:
        raise ValueError(
            "string format can either be start-end (7-10) or just the hour by itself (7)"
        )
    start_hour = int(form_list[0])
    end_hour = int(form_list[1])
    if start_hour <= end_hour:
        # Handle the case where the range is not wrapped around midnight
        v = list(range(start_hour, end_hour + 1))
    else:
        # Handle the case where the range wraps around midnight
        v = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
    return v
