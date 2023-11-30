import yaml

from jarvis.modules.logger import logger
from jarvis.modules.models import models


def remove(func_name: str) -> None:
    """Remove process map for a function that has stopped running.

    Args:
        func_name: Name of the function that has to be removed from the mapping.
    """
    with open(models.fileio.processes) as file:
        process_map = yaml.load(stream=file, Loader=yaml.FullLoader)
    logger.debug(process_map)
    if process_map.get(func_name):
        logger.info("%s: %s has been removed from processes mapping", func_name, process_map[func_name])
        del process_map[func_name]
    logger.debug(process_map)
    with open(models.fileio.processes, 'w') as file:
        yaml.dump(data=process_map, stream=file)


def update_map(func_name: str, old_pid: int, new_pid: int) -> None:
    """Remove process map for a function that has stopped running.

    Args:
        func_name: Name of the function that has to be removed from the mapping.
        old_pid: Old process ID that needs to be updating.
        new_pid: New process ID that needs to be updated.
    """
    with open(models.fileio.processes) as file:
        process_map = yaml.load(stream=file, Loader=yaml.FullLoader)
    logger.debug(process_map)
    if process_map.get(func_name) and process_map[func_name].get(old_pid):
        _temp = process_map[func_name][old_pid]
        del process_map[func_name][old_pid]
        process_map[func_name][new_pid] = _temp
        logger.info("%s has been updated from pid '%d' to pid '%d'", func_name, old_pid, new_pid)
    logger.debug(process_map)
    with open(models.fileio.processes, 'w') as file:
        yaml.dump(data=process_map, stream=file)
