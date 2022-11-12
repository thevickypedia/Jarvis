import ast
import os
from typing import NoReturn

import yaml

from modules.conditions import keywords, keywords_base

# Used by docs
if not os.path.isdir('fileio'):
    os.makedirs(name='fileio')

keywords_key = [__keyword for __keyword in dir(keywords_base) if not __keyword.startswith('__')]
keywords_src = os.path.join('fileio', 'keywords.yaml')


class Dict2Class(object):
    """Turns a dictionary into an object."""

    def __init__(self, dictionary: dict):
        """Creates an object and inserts the key value pairs as members of the class.

        Args:
            dictionary: Takes the dictionary to be converted as an argument.
        """
        for key in dictionary:
            setattr(self, key, dictionary[key])


def rewrite_keywords() -> NoReturn:
    """Loads keywords.yaml file if available, else loads the base keywords module as an object."""
    if os.path.isfile(keywords_src):
        with open(keywords_src) as file:
            data = yaml.load(stream=file, Loader=yaml.FullLoader)
        if list(data.keys()) == keywords_key and list(data.values()) and all(list(data.values())):
            keywords.keywords = Dict2Class(data)
            return

    with open(keywords_base.__file__) as file:
        data = file.read().split('\n\n')

    dictionary = {}
    for d in data:
        if '=' not in d:
            continue
        var, lis = d.split(' = ')
        dictionary[var] = ast.literal_eval(lis)

    with open(keywords_src, 'w') as file:
        yaml.dump(stream=file, data=dictionary, indent=4)

    keywords.keywords = Dict2Class(dictionary)


rewrite_keywords()
