from collections.abc import Generator
from typing import Dict

import requests

from jarvis.modules.audio import speaker
from jarvis.modules.auth_bearer import BearerAuth
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support


def get_repos() -> Generator[Dict[str, str | bool]]:
    """Get repositories in GitHub account.

    Yields:
        Generator[Dict[str, str | bool]]:
        Yields each repository information.
    """
    session = requests.Session()
    session.auth = BearerAuth(token=models.env.git_token)
    i = 1
    while True:
        response = session.get(
            f"https://api.github.com/user/repos?type=all&page={i}&per_page=100"
        )
        response.raise_for_status()
        assert response.ok
        response_json = response.json()
        logger.info("Repos in page %d: %d", i, len(response_json))
        if response_json:
            i += 1
        else:
            break
        yield from response_json


def github(*args) -> None:
    """Get GitHub account information."""
    if not models.env.git_token:
        logger.warning("Github token not found.")
        support.no_env_vars()
        return
    total, forked, private, archived, licensed = 0, 0, 0, 0, 0
    try:
        for repo in get_repos():
            total += 1
            forked += 1 if repo["fork"] else 0
            private += 1 if repo["private"] else 0
            archived += 1 if repo["archived"] else 0
            licensed += 1 if repo["license"] else 0
    except (EgressErrors, AssertionError, requests.JSONDecodeError) as error:
        logger.error(error)
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to connect to the GitHub API."
        )
        return
    speaker.speak(
        text=f"You have {total} repositories {models.env.title}, out of which {forked} are forked, "
        f"{private} are private, {licensed} are licensed, and {archived} archived."
    )
