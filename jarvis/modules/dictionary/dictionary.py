# noinspection PyUnresolvedReferences
"""Module to get meanings of words from `wordnetweb.princeton.edu <http://wordnetweb.princeton.edu/perl/webwn?s=>`__.

>>> Dictionary

"""

import re
from typing import Dict, Union

import requests
from bs4 import BeautifulSoup

from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger


def meaning(term: str) -> Union[Dict, None]:
    """Gets the meaning of a word from `wordnetweb.princeton.edu <http://wordnetweb.princeton.edu/perl/webwn?s=>`__.

    Args:
        term: Word for which the meaning has to be fetched.

    Returns:
        dict:
        A dictionary of the part of speech and the meaning of the word.
    """
    try:
        response = requests.get(f"http://wordnetweb.princeton.edu/perl/webwn?s={term}")
    except EgressErrors as error:
        logger.error(error)
        return
    if not response.ok:
        logger.error('Failed to get the meaning')
        return
    html = BeautifulSoup(response.text, "html.parser")
    types = html.findAll("h3")
    lists = html.findAll("ul")
    out = {}
    for a in types:
        reg = str(lists[types.index(a)])
        meanings = []
        for x in re.findall(r'\((.*?)\)', reg):
            if 'often followed by' in x:
                pass
            elif len(x) > 5 or ' ' in str(x):
                meanings.append(x)
        name = a.text
        out[name] = meanings
    return out
