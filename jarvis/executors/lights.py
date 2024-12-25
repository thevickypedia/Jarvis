import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# noinspection PyProtectedMember
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import Callable, Dict, List

from jarvis.executors import files, internet
from jarvis.executors import lights_squire as squire
from jarvis.executors import word_match
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import conversation
from jarvis.modules.lights import preset_values
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support, util


def get_lights(data: dict) -> Dict[str, List[str]]:
    """Extract lights' mapping from the data in smart devices.

    Args:
        data: Raw data from smart devices.

    Returns:
        Dict[str, List[str]]:
        Return lights' information as stored in smart devices yaml mapping.
    """
    for key, value in data.items():
        if key.lower() in ("light", "lights"):
            return data[key]


class ThreadExecutor:
    """Instantiates ``ThreadExecutor`` object to control the lights using pool of threads.

    >>> ThreadExecutor

    """

    def __init__(self, mapping: Dict[str, List[str]]):
        """Initializes the class and assign object members."""
        self.mapping = mapping

    def thread_worker(self, function_to_call: Callable) -> Dict[str, List[str]]:
        """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.

        Returns:
            Dict[str, List[str]]:
            Returns a dictionary of light location and the list of the IPs that failed as key value pairs.
        """
        futures = {}
        executor = ThreadPoolExecutor(max_workers=len(self.mapping.values()))
        with executor:
            for light_location, ip_list in self.mapping.items():
                for ip in ip_list:
                    future = executor.submit(function_to_call, ip)
                    futures[future] = (light_location, ip)

        thread_except = {}
        for future in as_completed(futures):
            if future.exception():
                light_location, ip = futures[future]
                if light_location not in thread_except:
                    thread_except[light_location] = []
                thread_except[light_location].append(ip)
                logger.error(
                    "Thread processing for '%s' at IP '%s' received an exception: %s",
                    light_location,
                    ip,
                    future.exception(),
                )
        return thread_except

    def avail_check(self, function_to_call: Callable) -> None:
        """Speaks an error message if any of the lights aren't reachable.

        Args:
            function_to_call: Takes the function/method that has to be called as an argument.
        """
        status = ThreadPool(processes=1).apply_async(
            func=self.thread_worker, args=(function_to_call,)
        )
        # Speak the initial response when the work is happening behind the scenes
        speaker.speak(run=True)
        try:
            failed = status.get(5)
        except ThreadTimeoutError as error:
            logger.error(error)
            return
        if failed:
            failed_msg = []
            for light_location, ip_list in failed.items():
                if failed_msg:
                    msg = f'{support.pluralize(count=len(ip_list), word="light", to_words=True)} '
                else:
                    msg = f'{support.pluralize(count=len(ip_list), word="light", to_words=True, cap_word=True)} '
                failed_msg.append(msg + f"from {light_location}")
            # Failed only on a single lamp
            if len(failed_msg) == 1 and failed_msg[0].startswith("One"):
                response = "".join(failed_msg) + " isn't available right now!"
            else:
                response = (
                    util.comma_separator(list_=failed_msg)
                    + " aren't available right now!"
                )
            logger.error(response)
            speaker.speak(text=f"I'm sorry {models.env.title}! {response}")


def lights(phrase: str) -> None:
    """Controller for smart lights.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not internet.vpn_checker():
        return

    if (smart_devices := files.get_smart_devices()) and (
        lights_map := get_lights(data=smart_devices)
    ):
        logger.debug(lights_map)
    else:
        logger.warning(
            "Smart devices are not configured for lights in %s",
            models.fileio.smart_devices,
        )
        support.no_env_vars()
        return

    phrase = phrase.lower()

    if "all" in phrase.split():
        light_location = ""
        if "except" in phrase or "exclud" in phrase:
            remove = util.matrix_to_flat_list(input_=squire.word_map.values()) + [
                "lights",
                "light",
            ]
            phrase_location = phrase
            for word in remove:
                phrase_location = phrase_location.replace(word, "")
            exclusion = util.get_closest_match(
                text=phrase_location.strip(), match_list=list(lights_map.keys())
            )
            host_names: List[str] = util.remove_duplicates(
                input_=util.matrix_to_flat_list(
                    [lights_map[light] for light in lights_map if light != exclusion]
                )
            )
            host_names_len = len(host_names)
            logger.debug("%d lights' excluding %s", host_names_len, exclusion)
        else:
            host_names: List[str] = util.remove_duplicates(
                input_=util.matrix_to_flat_list(
                    input_=[v for k, v in lights_map.items() if v]
                )
            )
            host_names_len = len(host_names)
            logger.debug("All lights: %d", host_names_len)
    else:
        remove = util.matrix_to_flat_list(input_=squire.word_map.values()) + [
            "lights",
            "light",
        ]
        phrase_location = phrase
        for word in remove:
            phrase_location = phrase_location.replace(word, "")
        light_location = util.get_closest_match(
            text=phrase_location.strip(), match_list=list(lights_map.keys())
        )
        host_names: List[str] = lights_map[light_location]
        host_names_len = len(host_names)
        logger.info("%d lights' location: %s", host_names_len, light_location)
    host_names = util.remove_none(input_=host_names)

    # extract IP addresses for hostnames that are required
    for _light_location, _light_hostname in lights_map.items():
        lights_map[_light_location] = []
        for hostname in _light_hostname:
            if hostname in host_names:
                if resolved := support.hostname_to_ip(hostname=hostname):
                    logger.debug("Resolved IP %s for hostname %s", resolved, hostname)
                else:
                    logger.debug("Unable to resolve IP for %s", hostname)
                    resolved = ["0.0.0.0"]  # Add placeholder IP to respond accordingly
                lights_map[_light_location].extend(resolved)
    executor = ThreadExecutor(mapping=lights_map)

    plural = "lights" if host_names_len > 1 else "light"
    if word_match.word_match(phrase, squire.word_map["turn_on"]):
        tone = "white" if "white" in phrase else "cool"
        if "turn on" in phrase:
            speaker.speak(
                text=f"{random.choice(conversation.acknowledgement)}! Turning on {host_names_len} {plural}"
            )
        else:
            speaker.speak(
                text=f"{random.choice(conversation.acknowledgement)}! Setting {host_names_len} {plural} to {tone}!"
            )
        executor.avail_check(function_to_call=squire.cool)
    elif word_match.word_match(phrase, squire.word_map["turn_off"]):
        speaker.speak(
            text=f"{random.choice(conversation.acknowledgement)}! Turning off {host_names_len} {plural}"
        )
        if state := squire.check_status():
            support.stop_process(pid=int(state[0]))
        if word_match.word_match(phrase, squire.word_map["reset"]):
            Thread(target=executor.thread_worker, args=[squire.cool]).run()
        executor.avail_check(function_to_call=squire.turn_off)
    elif word_match.word_match(phrase, squire.word_map["party_mode"]):
        host_ip = util.remove_duplicates(
            input_=util.matrix_to_flat_list(input_=list(lights_map.values()))
        )
        if squire.party_mode(host=host_ip, phrase=phrase):
            Thread(target=executor.thread_worker, args=[squire.cool]).run()
            Thread(target=executor.thread_worker, args=[squire.turn_off]).start()
    elif word_match.word_match(phrase, squire.word_map["warm"]):
        if "yellow" in phrase:
            speaker.speak(
                text=f"{random.choice(conversation.acknowledgement)}! "
                f"Setting {host_names_len} {plural} to yellow!"
            )
        else:
            speaker.speak(
                text=f"Sure {models.env.title}! Setting {host_names_len} {plural} to warm!"
            )
        executor.avail_check(function_to_call=squire.warm)
    elif color := word_match.word_match(
        phrase=phrase, match_list=list(preset_values.PRESET_VALUES.keys())
    ):
        speaker.speak(
            text=f"{random.choice(conversation.acknowledgement)}! "
            f"I've changed {host_names_len} {plural} to {color}!"
        )
        host_ip = util.remove_duplicates(
            input_=util.matrix_to_flat_list(input_=list(lights_map.values()))
        )
        for light_ip in host_ip:
            squire.preset(
                host=light_ip,
                speed=50,
                color=[
                    preset_values.PRESET_VALUES[_type]
                    for _type in list(preset_values.PRESET_VALUES.keys())
                    if _type in phrase
                ][0],
            )
    elif word_match.word_match(phrase, squire.word_map["set"]):
        if "bright" in phrase:
            level = 100
        elif "dim" in phrase:
            level = 50
        else:
            level = util.extract_nos(input_=phrase, method=int)
            if level is None:
                level = 100
        speaker.speak(
            text=f"{random.choice(conversation.acknowledgement)}! "
            f"I've set {host_names_len} {plural} to {level}%!"
        )
        level = round((255 * level) / 100)
        Thread(target=executor.thread_worker, args=[squire.turn_off]).run()
        time.sleep(1)
        host_ip = util.remove_duplicates(
            input_=util.matrix_to_flat_list(input_=list(lights_map.values()))
        )
        for light_ip in host_ip:
            squire.lumen(host=light_ip, rgb=level)
    else:
        speaker.speak(
            text=f"I didn't quite get that {models.env.title}! What do you want me to do to your "
            f"{light_location} {plural}?"
        )
        Thread(target=support.unrecognized_dumper, args=[{"LIGHTS": phrase}]).start()
