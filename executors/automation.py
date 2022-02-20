import json
import os
from datetime import datetime
from string import punctuation
from typing import Union

from api.controller import offline_compatible
from executors.logger import logger
from modules.audio import speaker


def automation_handler(phrase: str) -> None:
    """Handles automation file resets by renaming it to tmp if requested to disable.

    Args:
        phrase: Takes the recognized phrase as an argument.
    """
    if 'enable' in phrase:
        if os.path.isfile('tmp_automation.json'):
            os.rename(src='tmp_automation.json', dst='automation.json')
            speaker.speak(text='Automation has been enabled sir!')
        elif os.path.isfile('automation.json'):
            speaker.speak(text='Automation was never disabled sir!')
        else:
            speaker.speak(text="I couldn't not find the source file to enable automation sir!")
    elif 'disable' in phrase:
        if os.path.isfile('automation.json'):
            os.rename(src='automation.json', dst='tmp_automation.json')
            speaker.speak(text='Automation has been disabled sir!')
        elif os.path.isfile('tmp_automation.json'):
            speaker.speak(text='Automation was never enabled sir!')
        else:
            speaker.speak(text="I couldn't not find the source file to disable automation sir!")


def rewrite_automator(filename: str, json_object: dict) -> None:
    """Rewrites the ``automation_file`` with the updated json object.

    Args:
        filename: Name of the automation source file.
        json_object: Takes the new json object as a dictionary.
    """
    with open(filename, 'w') as file:
        logger.warning('Data has been modified. Rewriting automation data into JSON file.')
        json.dump(json_object, file, indent=2)


def auto_helper(automation_file: str) -> Union[str, None]:
    """Runs in a thread to help the automator function in the main module.

    Args:
        automation_file: Source file for automation.

    Returns:
        str:
        Task to be executed.
    """
    offline_list = offline_compatible()
    with open(automation_file) as read_file:
        try:
            automation_data = json.load(read_file)
        except json.JSONDecodeError:
            logger.error('Invalid file format. '
                         'Logging automation data and removing the file to avoid endless errors.\n'
                         f'{"".join(["*" for _ in range(120)])}\n\n'
                         f'{open(automation_file).read()}\n\n'
                         f'{"".join(["*" for _ in range(120)])}')
            os.remove(automation_file)
            return

    for automation_time, automation_info in automation_data.items():
        exec_status = automation_info.get('status')
        if not (exec_task := automation_info.get('task')) or \
                not any(word in exec_task.lower() for word in offline_list):
            logger.error("Following entry doesn't have a task or the task is not a part of offline compatible.")
            logger.error(f'{automation_time} - {automation_info}')
            automation_data.pop(automation_time)
            rewrite_automator(filename=automation_file, json_object=automation_data)
            break  # Using break instead of continue as python doesn't like dict size change in-between a loop
        try:
            datetime.strptime(automation_time, "%I:%M %p")
        except ValueError:
            logger.error(f'Incorrect Datetime format: {automation_time}. '
                         'Datetime string should be in the format: 6:00 AM. '
                         'Removing the key-value from automation.json')
            automation_data.pop(automation_time)
            rewrite_automator(filename=automation_file, json_object=automation_data)
            break  # Using break instead of continue as python doesn't like dict size change in-between a loop

        if day := automation_info.get('day'):
            today = datetime.today().strftime('%A').upper()
            if isinstance(day, list):
                day_list = [d.upper() for d in day]
                if today not in day_list:
                    continue
            elif isinstance(day, str):
                day = day.upper()
                if day == 'WEEKEND' and today in ['SATURDAY', 'SUNDAY']:
                    pass
                elif day == 'WEEKDAY' and today in ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']:
                    pass
                elif today == day:
                    pass
                else:
                    continue

        if automation_time != datetime.now().strftime("%-I:%M %p"):  # "%-I" to consider 06:05 AM as 6:05 AM
            if exec_status:
                logger.info(f"Reverting execution status flag for task: {exec_task} runs at {automation_time}")
                automation_data[automation_time]['status'] = False
                rewrite_automator(filename=automation_file, json_object=automation_data)
            continue

        if exec_status:
            continue
        exec_task = exec_task.translate(str.maketrans('', '', punctuation))  # Remove punctuations from the str
        automation_data[automation_time]['status'] = True
        rewrite_automator(filename=automation_file, json_object=automation_data)
        return exec_task
