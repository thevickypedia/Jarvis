import os
import re

import requests
from requests.auth import HTTPBasicAuth

from jarvis.executors import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support


def github(phrase: str) -> None:
    """Pre-process to check the phrase received and call the ``GitHub`` function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not all([models.env.git_user, models.env.git_pass]):
        logger.warning("Github username or token not found.")
        support.no_env_vars()
        return
    auth = HTTPBasicAuth(models.env.git_user, models.env.git_pass)
    try:
        response = requests.get('https://api.github.com/user/repos?type=all&per_page=100', auth=auth).json()
    except EgressErrors as error:
        logger.error(error)
        speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to connect to the GitHub API.")
        return
    result, repos, total, forked, private, archived, licensed = [], [], 0, 0, 0, 0, 0
    for i in range(len(response)):
        total += 1
        forked += 1 if response[i]['fork'] else 0
        private += 1 if response[i]['private'] else 0
        archived += 1 if response[i]['archived'] else 0
        licensed += 1 if response[i]['license'] else 0
        repos.append({response[i]['name'].replace('_', ' ').replace('-', ' '): response[i]['clone_url']})
    if 'how many' in phrase:
        speaker.speak(text=f'You have {total} repositories {models.env.title}, out of which {forked} are forked, '
                           f'{private} are private, {licensed} are licensed, and {archived} archived.')
    elif not shared.called_by_offline:
        [result.append(clone_url) if clone_url not in result and re.search(rf'\b{word}\b', repo.lower()) else None
         for word in phrase.lower().split() for item in repos for repo, clone_url in item.items()]
        if result:
            github_controller(target=result)
        else:
            speaker.speak(text=f"Sorry {models.env.title}! I did not find that repo.")


def github_controller(target: list) -> None:
    """Clones the GitHub repository matched with existing repository in conditions function.

    Asks confirmation if the results are more than 1 but less than 3 else asks to be more specific.

    Args:
        target: Takes repository name as argument which has to be cloned.
    """
    if len(target) == 1:
        os.system(f"cd {models.env.home} && git clone -q {target[0]}")
        cloned = target[0].split('/')[-1].replace('.git', '')
        speaker.speak(text=f"I've cloned {cloned} on your home directory {models.env.title}!")
        return
    elif len(target) <= 3:
        speaker.speak(text=f"I found {len(target)} results. On your screen {models.env.title}! "
                           "Which one shall I clone?", run=True)
        if not (converted := listener.listen()):
            if word_match.word_match(phrase=converted, match_list=keywords.keywords.exit_):
                return
            if 'first' in converted.lower():
                item = 1
            elif 'second' in converted.lower():
                item = 2
            elif 'third' in converted.lower():
                item = 3
            else:
                item = None
                speaker.speak(text=f"Only first second or third can be accepted {models.env.title}! Try again!")
                github_controller(target)
            os.system(f"cd {models.env.home} && git clone -q {target[item]}")
            cloned = target[item].split('/')[-1].replace('.git', '')
            speaker.speak(text=f"I've cloned {cloned} on your home directory {models.env.title}!")
    else:
        speaker.speak(text=f"I found {len(target)} repositories {models.env.title}! You may want to be more specific.")
