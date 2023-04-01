import collections
import os
import warnings
from collections.abc import Generator
from typing import NoReturn, Union

import yaml
from pydantic.error_wrappers import ValidationError

from jarvis.executors import word_match
from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.models.classes import BackgroundTask
from jarvis.modules.offline import compatibles
from jarvis.modules.utils import support


def background_task_handler(phrase: str) -> NoReturn:
    """Handles background tasks file resets by renaming it to tmp if requested to disable.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "enable" in phrase.lower():
        if os.path.isfile(models.fileio.tmp_background_tasks):
            os.rename(src=models.fileio.tmp_background_tasks, dst=models.fileio.background_tasks)
            speaker.speak(text=f"Background tasks have been enabled {models.env.title}!")
        elif os.path.isfile(models.fileio.background_tasks):
            speaker.speak(text=f"Background tasks were never disabled {models.env.title}!")
        else:
            speaker.speak(text=f"I couldn't not find the source file to enable background tasks {models.env.title}!")
    elif "disable" in phrase.lower():
        if os.path.isfile(models.fileio.background_tasks):
            os.rename(src=models.fileio.background_tasks, dst=models.fileio.tmp_background_tasks)
            speaker.speak(text=f"Background tasks have been disabled {models.env.title}!")
        elif os.path.isfile(models.fileio.tmp_background_tasks):
            speaker.speak(text=f"Background tasks were never enabled {models.env.title}!")
        else:
            speaker.speak(text=f"I couldn't not find the source file to disable background tasks {models.env.title}!")


def compare_tasks(dict1: dict, dict2: dict) -> bool:
    """Compares tasks currently in background tasks yaml file and the tasks already loaded.

    Args:
        dict1: Takes either the task in yaml file or loaded task as an argument.
        dict2: Takes either the task in yaml file or loaded task as an argument.

    Returns:
        bool:
        A boolean flag to if both the dictionaries are similar.
    """
    if 'ignore_hours' in dict1 and dict1['ignore_hours'] == [] and 'ignore_hours' not in dict2:
        dict1.pop('ignore_hours')
    if 'ignore_hours' in dict2 and dict2['ignore_hours'] == [] and 'ignore_hours' not in dict1:
        dict2.pop('ignore_hours')
    if collections.OrderedDict(sorted(dict1.items())) == collections.OrderedDict(sorted(dict2.items())):
        return True


def remove_corrupted(task: Union[BackgroundTask, dict]) -> NoReturn:
    """Removes a corrupted task from the background tasks feed file.

    Args:
        task: Takes a background task object as an argument.
    """
    with open(models.fileio.background_tasks) as read_file:
        existing_data = yaml.load(stream=read_file, Loader=yaml.FullLoader)
    for task_ in existing_data:
        if (isinstance(task, dict) and compare_tasks(task_, task)) or \
                (isinstance(task, BackgroundTask) and compare_tasks(task_, task.__dict__)):
            logger.info("Removing corrupted task: %s", task_)
            existing_data.remove(task_)
    with open(models.fileio.background_tasks, 'w') as write_file:
        yaml.dump(data=existing_data, stream=write_file)


def validate_tasks(log: bool = True) -> Generator[BackgroundTask]:
    """Validates each background task if it is offline compatible.

    Args:
        log: Takes a boolean flag to suppress info level logging.

    Yields:
        BackgroundTask:
        BackgroundTask object.
    """
    if os.path.isfile(models.fileio.background_tasks):
        task_info = []
        with open(models.fileio.background_tasks) as file:
            try:
                task_info = yaml.load(stream=file, Loader=yaml.FullLoader) or []
            except yaml.YAMLError as error:
                logger.error(error)
                warnings.warn(
                    "BACKGROUND TASKS :: Invalid file format."
                )
                logger.error("Invalid file format. Logging background tasks and renaming the file to avoid repeated "
                             "errors in a loop.\n%s\n\n%s\n\n%s" %
                             (''.join(['*' for _ in range(120)]), file.read(), ''.join(['*' for _ in range(120)])))
                os.rename(src=models.fileio.background_tasks, dst=models.fileio.tmp_background_tasks)
        if task_info:
            logger.info("Background tasks: %d", len(task_info)) if log else None
        else:
            return
        for t in task_info:
            try:
                task = BackgroundTask(seconds=t.get('seconds'), task=t.get('task'), ignore_hours=t.get('ignore_hours'))
            except ValidationError as error:
                logger.error(error)
                remove_corrupted(t)
                continue
            if word_match.word_match(phrase=task.task, match_list=compatibles.offline_compatible()):
                if log:
                    logger.info("'%s' will be executed every %s",
                                task.task, support.time_converter(second=task.seconds))
                yield task
            else:
                logger.error("'%s' is not a part of offline communication compatible request.", task.task)
                remove_corrupted(task=task)
