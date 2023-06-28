import os
import warnings
from collections import OrderedDict
from typing import NoReturn

import yaml

from jarvis.modules.builtin_overrides import ordered_dump, ordered_load
from jarvis.modules.conditions import conversation, keywords
from jarvis.modules.models import models

# Used by docs
if not os.path.isdir(models.fileio.root):
    os.makedirs(name=models.fileio.root)


def rewrite_keywords() -> NoReturn:
    """Loads keywords.yaml file if available, else loads the base keywords module as an object."""
    keywords_src = OrderedDict(**keywords.keyword_mapping(), **conversation.conversation_mapping())
    if os.path.isfile(models.fileio.keywords):
        with open(models.fileio.keywords) as dst_file:
            try:
                data = ordered_load(stream=dst_file, Loader=yaml.SafeLoader) or {}
            except yaml.YAMLError as error:
                warnings.warn(message=str(error))
                data = None

        if not data:  # Either an error occurred when reading or a manual deletion
            if data is {}:
                warnings.warn(
                    f"\nSomething went wrong. {models.fileio.keywords!r} appears to be empty."
                    f"\nRe-sourcing {models.fileio.keywords!r} from base."
                )
        # compare as sorted, since this will allow changing the order of keywords in the yaml file
        elif sorted(list(data.keys())) == sorted(list(keywords_src.keys())) and data.values() and all(data.values()):
            keywords.keywords = data
            return
        else:  # Mismatch in keys
            warnings.warn(
                "\nData mismatch between base keywords and custom keyword mapping."
                "\nPlease note: This mapping file is only to change the value for keywords, not the key(s) itself."
                f"\nRe-sourcing {models.fileio.keywords!r} from base."
            )

    with open(models.fileio.keywords, 'w') as dst_file:
        ordered_dump(stream=dst_file, data=keywords_src, indent=4)
    keywords.keywords = keywords_src


rewrite_keywords()
