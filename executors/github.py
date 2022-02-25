import os
import re
import sys

import requests
from requests.auth import HTTPBasicAuth

from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.utils import globals, support

env = globals.ENV


def github(phrase: str):
    """Pre-process to check the phrase received and call the ``GitHub`` function as necessary.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not all([env.git_user, env.git_pass]):
        support.no_env_vars()
        return
    auth = HTTPBasicAuth(env.git_user, env.git_pass)
    response = requests.get('https://api.github.com/user/repos?type=all&per_page=100', auth=auth).json()
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
            text=f'You have {total} repositories sir, out of which {forked} are forked, {private} are private, '
                 f'{licensed} are licensed, and {archived} archived.')
    else:
        [result.append(clone_url) if clone_url not in result and re.search(rf'\b{word}\b', repo.lower()) else None
         for word in phrase.lower().split() for item in repos for repo, clone_url in item.items()]
        if result:
            github_controller(target=result)
        else:
            speaker.speak(text="Sorry sir! I did not find that repo.")


def github_controller(target: list) -> None:
    """Clones the GitHub repository matched with existing repository in conditions function.

    Asks confirmation if the results are more than 1 but less than 3 else asks to be more specific.

    Args:
        target: Takes repository name as argument which has to be cloned.
    """
    if len(target) == 1:
        os.system(f"cd {env.home} && git clone -q {target[0]}")
        cloned = target[0].split('/')[-1].replace('.git', '')
        speaker.speak(text=f"I've cloned {cloned} on your home directory sir!")
        return
    elif len(target) <= 3:
        newest = [new.split('/')[-1] for new in target]
        sys.stdout.write(f"\r{', '.join(newest)}")
        speaker.speak(text=f"I found {len(target)} results. On your screen sir! Which one shall I clone?", run=True)
        converted = listener.listen(timeout=3, phrase_limit=5)
        if converted != 'SR_ERROR':
            if any(word in converted.lower() for word in keywords.exit_):
                return
            if 'first' in converted.lower():
                item = 1
            elif 'second' in converted.lower():
                item = 2
            elif 'third' in converted.lower():
                item = 3
            else:
                item = None
                speaker.speak(text="Only first second or third can be accepted sir! Try again!")
                github_controller(target)
            os.system(f"cd {env.home} && git clone -q {target[item]}")
            cloned = target[item].split('/')[-1].replace('.git', '')
            speaker.speak(text=f"I've cloned {cloned} on your home directory sir!")
    else:
        speaker.speak(text=f"I found {len(target)} repositories sir! You may want to be more specific.")
