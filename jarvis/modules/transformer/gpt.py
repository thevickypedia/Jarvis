import collections
import difflib
import os
from threading import Thread
from typing import NoReturn, Union

import openai
import yaml
from openai.error import AuthenticationError, OpenAIError
from openai.openai_object import OpenAIObject

from jarvis.modules.audio import speaker
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support


def dump_history(request: str, response: str) -> NoReturn:
    """Dump responses from GPT to a yaml file for future response.

    Args:
        request: Request from user.
        response: Response from GPT.
    """
    data = []
    if os.path.isfile(models.fileio.gpt_data):
        try:
            with open(models.fileio.gpt_data) as file:
                data = yaml.load(stream=file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as error:
            logger.error(error)
    data.append({'request': request, 'response': response})
    with open(models.fileio.gpt_data, 'w') as file:
        yaml.dump(data=data, stream=file, indent=4, Dumper=yaml.SafeDumper)


def existing_response(request: str) -> Union[str, None]:
    """Return existing response if new request closely matches historical requests.

    Args:
        request: Request from user.

    See Also:
        - Reusing responses is not enabled by default.
        - To enable reusing responses, set the env var ``OPENAI_REUSE_THRESHOLD`` to a value between 0.5 and 0.9
        - This value will choose how close the request should match with a historic request before reusing the response.

    Warnings:
        - This can be a problem for phrases like:
            - `what is the height of Mount Everest`
            - `what is the height of Mount Rushmore`

        - To get around this, refer `env-variables section of read me <https://github.com/thevickypedia/Jarvis#env-
          variables>`__ about ``OPENAI_REUSE_THRESHOLD``

    Returns:
        str:
        Returns the closest matching response stored in historical transactions.
    """
    if not os.path.isfile(models.fileio.gpt_data):
        return
    # exclude if numbers present in new request
    if any(word.isdigit() for word in request):
        logger.debug("request: '%s' contains numbers in it, so skipping existing search", request)
        return
    try:
        with open(models.fileio.gpt_data) as file:
            data = yaml.load(stream=file, Loader=yaml.SafeLoader)
    except yaml.YAMLError as error:
        logger.error(error)
        return
    if not data:
        logger.debug("GPT history is empty")
        return

    # unpack data and store the request: response, match ratio in a new dict
    new_req = request.lower()
    ratios = {}
    for d in data:
        ex_req = d['request'].lower()
        if ex_req == new_req:
            logger.info("Identical historical request: '%s'", d['request'])
            return d['response']
        ratios[d['request']] = (d['response'], difflib.SequenceMatcher(a=ex_req, b=new_req).ratio())

    # no identical requests found in history, and reuse threshold was not set
    if not models.env.openai_reuse_threshold:
        logger.warning("No identical requests found in history, and reuse threshold was not set. Querying OpenAI.")
        return

    # sort the new dict in reverse order so the closest match gets returned first
    ratios = collections.OrderedDict(sorted(ratios.items(), key=lambda kv: kv[1][1], reverse=True))

    # iterate over the ordered dict to look for numbers in existing requests and ignore them
    for existing_request, response_ratio in ratios.items():
        if response_ratio[1] >= models.env.openai_reuse_threshold and \
                not any(word.isdigit() for word in existing_request):
            logger.info("Closest historical request: '%s'", existing_request)
            return response_ratio[0]


class ChatGPT:
    """Wrapper for OpenAI's ChatGPT API.

    >>> ChatGPT

    """

    MESSAGES = []

    def __init__(self):
        """Initiates authentication to GPT api."""
        self.authenticated = False
        self.authenticate()

    def authenticate(self) -> NoReturn:
        """Initiates authentication and prepares GPT responses ready to be audio fed."""
        if models.env.openai_api:
            openai.api_key = models.env.openai_api
        else:
            logger.warning("'openai_api' wasn't found to proceed")
            return
        self.MESSAGES.append({
            "role": "system",
            "content": "All your response will be audio fed, "
                       "so keep your replies within 1 to 2 sentences without any parenthesis."
        })
        try:
            chat: OpenAIObject = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=self.MESSAGES, timeout=10
            )
            self.MESSAGES.append({"role": "system", "content": chat.choices[0].message.content})
            self.authenticated = True
        except AuthenticationError as error:
            logger.error(error)
        except OpenAIError as error:
            logger.critical(error)

    def query(self, phrase: str) -> NoReturn:
        """Queries ChatGPT api with the request and speaks the response.

        See Also:
            - Even without authentication, this plugin can fetch responses from a mapping file.
            - This allows, reuse-ability for requests in identical pattern.

        Args:
            phrase: Takes the phrase spoken as an argument.
        """
        if response := existing_response(request=phrase):
            speaker.speak(text=response)
            return
        if not self.authenticated:
            support.no_env_vars()
            return
        self.MESSAGES.append(
            {"role": "user", "content": phrase},
        )
        try:
            chat: OpenAIObject = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=self.MESSAGES
            )
        except OpenAIError as error:
            logger.error(error)
            speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to process your request.")
            return
        if chat.choices:
            reply = chat.choices[0].message.content
            self.MESSAGES.append({"role": "assistant", "content": reply})
            Thread(target=dump_history, args=(phrase, reply)).start()
            speaker.speak(text=reply)
        else:
            logger.error(chat)
            speaker.speak(text=f"I'm sorry {models.env.title}! I wasn't able to process your request.")


if models.settings.pname in ('JARVIS', 'telegram_api', 'fast_api'):
    if models.env.openai_reuse_threshold:
        logger.info("Initiating GPT instance for '%s' with a reuse threshold of '%.2f'",
                    models.settings.pname, models.env.openai_reuse_threshold)
    else:
        logger.info("Initiating GPT instance for '%s'", models.settings.pname)
    try:
        instance = ChatGPT()
    except TimeoutError as error_:
        logger.error(error_)
        instance = None
else:
    instance = None
