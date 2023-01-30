import os
import warnings
from typing import NoReturn

import yaml

from jarvis.modules.conditions import keywords, keywords_base
from jarvis.modules.utils import util

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')

keywords_src = keywords_base.keyword_mapping()
keywords_dst = os.path.join('fileio', 'keywords.yaml')

get_time = lambda file: os.stat(file).st_mtime  # noqa: E731
_updated = {'time': 0.0}  # Initiate a dict


def rewrite_keywords(init: bool = False) -> NoReturn:
    """Loads keywords.yaml file if available, else loads the base keywords module as an object.

    Args:
        init: Takes a boolean flag to suppress logging when triggered for the first time.
    """
    if os.path.isfile(keywords_dst):
        modified = get_time(keywords_dst)
        if _updated['time'] == modified:
            return  # Avoid reading when there are clearly no changes made
        _updated['time'] = modified
        with open(keywords_dst) as file:
            try:
                data = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
            except yaml.YAMLError as error:
                warnings.warn(message=str(error))
                data = None

        if not data:  # Either an error occurred when reading or a manual deletion
            if data is {} and not init:  # ignore when None, since a warning would have been displayed already
                warnings.warn(
                    f"\nSomething went wrong. {keywords_dst!r} appears to be empty."
                    f"\nRe-sourcing {keywords_dst!r} from base."
                )
        elif sorted(list(data.keys())) == sorted(list(keywords_src.keys())) and data.values() and all(data.values()):
            keywords.keywords = util.Dict2Class(data)
            return
        else:  # Mismatch in keys
            if not init:
                warnings.warn(
                    "\nData mismatch between base keywords and custom keyword mapping."
                    "\nPlease note: This mapping file is only to change the value for keywords, not the key(s) itself."
                    f"\nRe-sourcing {keywords_dst!r} from base."
                )

    with open(keywords_dst, 'w') as file:
        yaml.dump(stream=file, data=keywords_src, indent=4)
    _updated['time'] = get_time(keywords_dst)
    keywords.keywords = util.Dict2Class(keywords_src)


rewrite_keywords(init=True)
