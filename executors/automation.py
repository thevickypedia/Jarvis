import os
import warnings
from datetime import datetime
from string import punctuation
from typing import Union

import yaml
from yaml.scanner import ScannerError

from api.controller import offline_compatible
from executors.logger import logger
from modules.audio import speaker
from modules.models import models

env = models.env


def automation_handler(phrase: str) -> None:
    """Handles automation file resets by renaming it to tmp if requested to disable.

    Args:
        phrase: Takes the recognized phrase as an argument.
    """
    if "enable" in phrase:
        if os.path.isfile("tmp_automation.yaml"):
            os.rename(src="tmp_automation.yaml", dst="automation.yaml")
            speaker.speak(text=f"Automation has been enabled {env.title}!")
        elif os.path.isfile("automation.yaml"):
            speaker.speak(text=f"Automation was never disabled {env.title}!")
        else:
            speaker.speak(text=f"I couldn't not find the source file to enable automation {env.title}!")
    elif "disable" in phrase:
        if os.path.isfile("automation.yaml"):
            os.rename(src="automation.yaml", dst="tmp_automation.yaml")
            speaker.speak(text=f"Automation has been disabled {env.title}!")
        elif os.path.isfile("tmp_automation.yaml"):
            speaker.speak(text=f"Automation was never enabled {env.title}!")
        else:
            speaker.speak(text=f"I couldn't not find the source file to disable automation {env.title}!")


def rewrite_automator(write_data: dict) -> None:
    """Rewrites the ``'automation.yaml'`` with the updated dictionary.

    Args:
        write_data: Takes the new dictionary as an argument.
    """
    with open("automation.yaml", "w") as file:
        logger.info("Data has been modified. Rewriting automation data into YAML file.")
        yaml.dump(write_data, file, indent=2)


def auto_helper() -> Union[str, None]:
    """Runs in a thread to help the automator function in the main module.

    Returns:
        str:
        Task to be executed.
    """
    offline_list = offline_compatible()
    with open("automation.yaml") as read_file:
        try:
            automation_data = yaml.load(stream=read_file, Loader=yaml.FullLoader)
        except ScannerError:
            warnings.warn(
                "AUTOMATION FILE :: Invalid file format."
            )
            logger.error(f"Invalid file format. "
                         f"Logging automation data and removing the file to avoid endless errors.\n"
                         f"{''.join(['*' for _ in range(120)])}\n\n{read_file.read()}\n\n"
                         f"{''.join(['*' for _ in range(120)])}")
            os.remove("automation.yaml")
            return

    for automation_time, automation_info in automation_data.items():
        if not (exec_task := automation_info.get("task")) or \
                not any(word in exec_task.lower() for word in offline_list):
            logger.error("Following entry doesn't have a task or the task is not a part of offline compatible.")
            logger.error(f"{automation_time} - {automation_info}")
            automation_data.pop(automation_time)
            rewrite_automator(write_data=automation_data)
            break  # Using break instead of continue as python doesn't like dict size change in-between a loop
        try:
            datetime.strptime(automation_time, "%I:%M %p")
        except ValueError:
            logger.error(f"Incorrect Datetime format: {automation_time}. "
                         "Datetime string should be in the format: 6:00 AM. "
                         "Removing the key-value from automation.yaml")
            automation_data.pop(automation_time)
            rewrite_automator(write_data=automation_data)
            break  # Using break instead of continue as python doesn't like dict size change in-between a loop

        if day := automation_info.get("day"):
            today = datetime.today().strftime("%A").upper()
            if isinstance(day, list):
                if today not in [d.upper() for d in day]:
                    continue
            elif isinstance(day, str):
                day = day.upper()
                if day == "WEEKEND" and today in ["SATURDAY", "SUNDAY"]:
                    pass
                elif day == "WEEKDAY" and today in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]:
                    pass
                elif today == day:
                    pass
                else:
                    continue

        if automation_time != datetime.now().strftime("%-I:%M %p"):  # "%-I" to consider 06:05 AM as 6:05 AM
            if automation_info.get("status"):
                logger.info(f"Reverting execution status flag for task: {exec_task} runs at {automation_time}")
                del automation_data[automation_time]["status"]
                rewrite_automator(write_data=automation_data)
            continue

        if automation_info.get("status"):
            continue
        exec_task = exec_task.translate(str.maketrans("", "", punctuation))  # Remove punctuations from the str
        automation_data[automation_time]["status"] = True
        rewrite_automator(write_data=automation_data)
        return exec_task
