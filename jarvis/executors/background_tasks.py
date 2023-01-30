import os
import warnings
from typing import Iterable, NoReturn, Union

import yaml
from pydantic.error_wrappers import ValidationError

from jarvis.executors.word_match import word_match
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


def remove_corrupted(task: Union[BackgroundTask, dict]) -> NoReturn:
    """Removes a corrupted task from the background tasks feed file.

    Args:
        task: Takes a background task object as an argument.
    """
    with open(models.fileio.background_tasks) as read_file:
        existing_data = yaml.load(stream=read_file, Loader=yaml.FullLoader)
    for task_ in existing_data:
        if (isinstance(task, dict) and task_ == task) or (isinstance(task, BackgroundTask) and task_ == task.__dict__):
            logger.info(f"Removing corrupted task: {task_}")
            existing_data.remove(task_)
    with open(models.fileio.background_tasks, 'w') as write_file:
        yaml.dump(data=existing_data, stream=write_file)


def validate_background_tasks(log: bool = True) -> Iterable[BackgroundTask]:
    """Validates each background task if it is offline compatible.

    Args:
        log: Takes a boolean flag to suppress info level logging.

    Yields:
        Iterable:
        BackgroundTask object(s).
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
                logger.error(f"Invalid file format. "
                             f"Logging background tasks and renaming the file to avoid repeated errors in a loop.\n"
                             f"{''.join(['*' for _ in range(120)])}"
                             f"\n\n{file.read()}\n\n"
                             f"{''.join(['*' for _ in range(120)])}")
                os.rename(src=models.fileio.background_tasks, dst=models.fileio.tmp_background_tasks)
        if task_info:
            logger.info(f"Background tasks: {len(task_info)}") if log else None
        else:
            return
        for t in task_info:
            try:
                task = BackgroundTask(seconds=t.get('seconds'), task=t.get('task'), ignore_hours=t.get('ignore_hours'))
            except ValidationError as error:
                logger.error(error)
                remove_corrupted(t)
                continue
            if word_match(phrase=task.task, match_list=compatibles.offline_compatible()):
                if log:
                    logger.info(f"{task.task!r} will be executed every {support.time_converter(second=task.seconds)}")
                yield task
            else:
                logger.error(f"{task.task!r} is not a part of offline communication compatible request.")
                remove_corrupted(task=task)
