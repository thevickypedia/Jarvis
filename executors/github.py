import os
import re
import sys

import git
import requests
from requests.auth import HTTPBasicAuth

from executors.word_match import word_match
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import shared, support


def github(phrase: str) -> None:
    """Pre-process to check the phrase received and call the ``GitHub`` function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if 'update yourself' in phrase or 'update your self' in phrase:
        update()
        return

    if not all([models.env.git_user, models.env.git_pass]):
        logger.warning("Github username or token not found.")
        support.no_env_vars()
        return
    auth = HTTPBasicAuth(models.env.git_user, models.env.git_pass)
    try:
        response = requests.get('https://api.github.com/user/repos?type=all&per_page=100', auth=auth).json()
    except (requests.RequestException, requests.Timeout, ConnectionError, TimeoutError, requests.JSONDecodeError) \
            as error:
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
        speaker.speak(
            text=f'You have {total} repositories {models.env.title}, out of which {forked} are forked, {private} are '
                 f'private, {licensed} are licensed, and {archived} archived.')
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
        newest = [new.split('/')[-1] for new in target]
        sys.stdout.write(f"\r{', '.join(newest)}")
        speaker.speak(text=f"I found {len(target)} results. On your screen {models.env.title}! "
                           "Which one shall I clone?", run=True)
        if not (converted := listener.listen(timeout=3, phrase_limit=5)):
            if word_match(phrase=converted, match_list=keywords.exit_):
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


def update() -> None:
    """Pulls the latest version of ``Jarvis`` and restarts if there were any changes."""
    output = git.cmd.Git('Jarvis').pull()
    if not output:
        speaker.speak(text=f"I was not able to update myself {models.env.title}!")
        return

    if output.strip() == 'Already up to date.':
        speaker.speak(text=f"I'm already running on the latest version {models.env.title}!")
        return

    status = None
    for each in output.splitlines():
        if 'files changed' in each:
            status = each.split(',')[0].strip()
            break
    speaker.speak(text=f"I've updated myself to the latest version {models.env.title}! "
                       "However, you might need to restart the main process for the changes to take effect.")
    if status:
        speaker.speak(text=status)
