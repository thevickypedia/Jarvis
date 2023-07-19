import os
import string
import warnings
from datetime import datetime, timedelta
from typing import NoReturn, Union

from deepdiff import DeepDiff

from jarvis.executors import files
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models


def automation_handler(phrase: str) -> NoReturn:
    """Handles automation file resets by renaming it to tmp if requested to disable.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "enable" in phrase.lower():
        if os.path.isfile(models.fileio.tmp_automation):
            os.rename(src=models.fileio.tmp_automation, dst=models.fileio.automation)
            speaker.speak(text=f"Automation has been enabled {models.env.title}!")
        elif os.path.isfile(models.fileio.automation):
            speaker.speak(text=f"Automation was never disabled {models.env.title}!")
        else:
            speaker.speak(text=f"I couldn't not find the source file to enable automation {models.env.title}!")
    elif "disable" in phrase.lower():
        if os.path.isfile(models.fileio.automation):
            os.rename(src=models.fileio.automation, dst=models.fileio.tmp_automation)
            speaker.speak(text=f"Automation has been disabled {models.env.title}!")
        elif os.path.isfile(models.fileio.tmp_automation):
            speaker.speak(text=f"Automation was never enabled {models.env.title}!")
        else:
            speaker.speak(text=f"I couldn't not find the source file to disable automation {models.env.title}!")


def rewrite_automator(write_data: dict) -> NoReturn:
    """Rewrites the automation file with the updated dictionary.

    Args:
        write_data: Takes the new dictionary as an argument.
    """
    logger.info("Data has been modified. Rewriting automation data into YAML file.")
    read_data = files.get_automation()
    logger.debug(DeepDiff(read_data, write_data, ignore_order=True))
    files.put_automation(data=write_data)


def validate_weather_alert() -> NoReturn:
    """Adds the env var for weather alert (if present) to automation feed file."""
    if models.env.weather_alert:
        automation_data = files.get_automation()
        if tasks_overlap := automation_data.get(models.env.weather_alert):
            for task_overlap in tasks_overlap:
                if "weather" in task_overlap.get("task"):
                    logger.info("Redundancy found in env var and automation. Skipping..")
                    return
                else:
                    logger.warning("%s was found at '%s', appending a minute to weather alert",
                                   task_overlap, models.env.weather_alert)
                    time_overlap = datetime.strptime(models.env.weather_alert, '%I:%M %p')
                    models.env.weather_alert = (time_overlap + timedelta(minutes=1)).strftime('%I:%M %p')
                    automation_data[models.env.weather_alert].append({"task": "weather alert"})
                    files.put_automation(data=automation_data)
        else:  # Write weather alert schedule to 'automation.yaml' since env var is not used to trigger the function
            logger.info("Storing weather alert schedule '%s' to %s", models.env.weather_alert, models.fileio.automation)
            automation_data[models.env.weather_alert] = [{"task": "weather alert"}]
            files.put_automation(data=automation_data)


def auto_helper() -> Union[str, None]:
    """Runs in a thread to help the automator function in the main module.

    Returns:
        str:
        Task to be executed.
    """
    automation_data = files.get_automation()
    if automation_data is None:
        warnings.warn(
            "AUTOMATION FILE :: Invalid file format."
        )
        logger.error("Invalid file format. Logging automation data and renaming the file to avoid repeated errors in a "
                     "loop.\n%s\n\n%s\n\n%s" %
                     (''.join(['*' for _ in range(120)]),
                      open(models.fileio.automation).read(),
                      ''.join(['*' for _ in range(120)])))
        os.rename(src=models.fileio.automation, dst=models.fileio.tmp_automation)
        return

    for automation_time, automation_schedule in automation_data.items():
        if not automation_schedule:
            del automation_data[automation_time]
            rewrite_automator(write_data=automation_data)
            # Use return as python doesn't like dict size change between a loop
            # Since this function is called every second, there is no need for recursion
            return
        if isinstance(automation_schedule, dict):
            automation_schedule = [automation_schedule]
            automation_data[automation_time] = automation_schedule
        for index, automation_info in enumerate(automation_schedule):
            if not (exec_task := automation_info.get("task")):
                logger.error("Following entry doesn't have a task.")
                logger.error("%s - %s", automation_time, automation_schedule)
                del automation_data[automation_time][index]
                rewrite_automator(write_data=automation_data)
                # Use return as python doesn't like dict size change between a loop
                # Since this function is called every second, there is no need for recursion
                return
            try:
                datetime.strptime(automation_time, "%I:%M %p")
            except ValueError:
                logger.error("Following entry has an incorrect datetime format.")
                logger.error("%s - %s", automation_time, automation_schedule)
                automation_data.pop(automation_time)
                rewrite_automator(write_data=automation_data)
                # Use return as python doesn't like dict size change between a loop
                # Since this function is called every second, there is no need for recursion
                return

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

            if automation_time != datetime.now().strftime("%I:%M %p"):
                if automation_info.get("status"):
                    logger.info("Reverting execution status flag for task: %s runs at %s", exec_task, automation_time)
                    del automation_data[automation_time][index]["status"]
                    rewrite_automator(write_data=automation_data)
                continue

            if automation_info.get("status"):
                continue
            exec_task = exec_task.translate(str.maketrans('', '', string.punctuation))  # Remove punctuation from string
            automation_data[automation_time][index]["status"] = True
            rewrite_automator(write_data=automation_data)
            return exec_task
