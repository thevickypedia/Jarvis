from typing import AnyStr

import requests
from pydantic import HttpUrl

from jarvis.executors import (
    conditions,
    internet,
    others,
    word_match,
)
from jarvis.modules.auth_bearer import BearerAuth
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared


def ondemand_offline_automation(task: str) -> str | None:
    """Makes a ``POST`` call to offline-communicator to execute a said task.

    Args:
        task: Takes the command to be executed as an argument.

    Returns:
        str:
        Returns the response if request was successful.
    """
    try:
        response = requests.post(
            url=f"http://{models.env.offline_host}:{models.env.offline_port}/offline-communicator",
            json={"command": task},
            auth=BearerAuth(token=models.env.offline_pass),
        )
    except EgressErrors:
        return
    if response.ok:
        return response.json()["detail"].split("\n")[-1]


def communicator(command: str, bg_flag: bool = False) -> AnyStr | HttpUrl:
    """Initiates conditions after flipping ``status`` flag in ``called_by_offline`` dict which suppresses the speaker.

    Args:
        command: Takes the command that has to be executed as an argument.
        bg_flag: Takes the background flag caller as an argument.

    Returns:
        AnyStr:
        Response from Jarvis.
    """
    shared.called_by_offline = True
    shared.called_by_bg_tasks = bg_flag
    # Specific for offline communication and not needed for live conversations
    if word_match.word_match(phrase=command, match_list=keywords.keywords["ngrok"]):
        if public_url := internet.get_tunnel():
            return public_url
        else:
            raise LookupError("Failed to retrieve the public URL")
    if word_match.word_match(phrase=command, match_list=keywords.keywords["photo"]):
        return others.photo()
    # Call condition instead of split_phrase as the 'and' and 'also' filter will overwrite the first response
    conditions.conditions(phrase=command)
    shared.called_by_offline = False
    shared.called_by_bg_tasks = False
    if response := shared.text_spoken:
        shared.text_spoken = None
        return response
    else:
        logger.error("Offline request failed for '%s'", command)
        return f"I was unable to process the request: {command}"
