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
