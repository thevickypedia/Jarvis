import os
import warnings
from typing import NoReturn

import yaml

from modules.conditions import keywords, keywords_base
from modules.utils import util

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')

keywords_src = keywords_base.keyword_mapping()
keywords_dst = os.path.join('fileio', 'keywords.yaml')


def rewrite_keywords() -> NoReturn:
    """Loads keywords.yaml file if available, else loads the base keywords module as an object."""
    rewrite_keywords.count += 1
    if os.path.isfile(keywords_dst):
        warn = True
        with open(keywords_dst) as file:
            try:
                data = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
            except yaml.YAMLError as error:
                warn = False
                warnings.warn(message=str(error))
                data = {}

        if not data:  # Either an error occurred when reading or a manual deletion
            if warn and rewrite_keywords.count > 1:
                warnings.warn(
                    f"\nSomething went wrong. {keywords_dst!r} appears to be empty."
                    f"\nRe-sourcing {keywords_dst!r} from base."
                )
        elif sorted(list(data.keys())) == sorted(list(keywords_src.keys())) and data.values() and all(data.values()):
            keywords.keywords = util.Dict2Class(data)
            return
        else:  # Mismatch in keys
            if rewrite_keywords.count > 1:
                warnings.warn(
                    "\nData mismatch between base keywords and custom keyword mapping."
                    "\nPlease note: This mapping file is only to change the value for keywords, not the key(s) itself."
                    f"\nRe-sourcing {keywords_dst!r} from base."
                )

    with open(keywords_dst, 'w') as file:
        yaml.dump(stream=file, data=keywords_src, indent=4)

    keywords.keywords = util.Dict2Class(keywords_src)


# Used to count the number of iterations t
rewrite_keywords.count = 0
rewrite_keywords()
