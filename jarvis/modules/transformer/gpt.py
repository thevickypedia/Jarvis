"""Generative Pre-trained Transformer with Ollama API client.

Warnings:
    - This module uses a pre-trained transformer to generate predictive responses.
    - Although this feature is enabled by default, please note that machine learning models are memory beasts.
    - Please refer the following minimum requirements before choosing the right model.
    - This feature can be disabled by setting the env var ``ollama=False`` in the ``env_file``

Notes:
    There are quite a few parameters that can be adjusted, to customize the model usage and interaction with Jarvis.

    - `Params for Jarvis <https://github.com/thevickypedia/Jarvis/wiki/2.-Environment-Variables
      #ollama-gpt-integration>`__

    - `Params for Ollama API (Modelfile) <https://github.com/ollama/ollama/blob/main/docs/modelfile.md
      #valid-parameters-and-values>`__

**RAM Requirements**
    - 8 GB to run the 7B models
    - 16 GB to run the 13B models
    - 32 GB to run the 33B models

References:
    - Model Artifactory: https://ollama.com/library
    - Alternatives: https://huggingface.co/meta-llama
    - Supported Models: https://github.com/ollama/ollama/blob/main/README.md#model-library

See Also:
    `Future Plans <https://github.com/thevickypedia/Jarvis/blob/master/jarvis/modules/transformer/gpt.md>`__
"""

import collections
import difflib
import os
import warnings
from collections.abc import Generator

# noinspection PyProtectedMember
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import List, NoReturn

import httpcore
import httpx
import jinja2
import ollama

from jarvis.executors import files, static_responses
from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import support


def dump_history(request: str, response: str) -> None:
    """Dump responses from GPT into a yaml file for future response.

    Args:
        request: Request from user.
        response: Response from GPT.
    """
    data = files.get_gpt_data()
    data.append({"request": request, "response": response})
    files.put_gpt_data(data)


def existing_response(request: str) -> str | None:
    """Return existing response if new request closely matches historical requests.

    Args:
        request: Request from user.

    See Also:
        - Reusing responses is not enabled by default.
        - To enable reusing responses, set the env var ``OLLAMA_REUSE_THRESHOLD`` to a value between 0.5 and 0.9
        - This value will choose how close the request should match with a historic request before reusing the response.

    Warnings:
        - This can be a problem for phrases like:
            - `what is the height of Mount Everest`
            - `what is the height of Mount Rushmore`

        - To get around this, refer `env-variables section of the wiki page
          <https://github.com/thevickypedia/Jarvis/wiki/2.-Environment-Variables#ollama-
          gpt-integration>`__ about ``OLLAMA_REUSE_THRESHOLD``

    Returns:
        str:
        Returns the closest matching response stored in historical transactions.
    """
    # exclude if numbers present in new request
    if any(word.isdigit() for word in request):
        logger.debug(
            "request: '%s' contains numbers in it, so skipping existing search", request
        )
        return
    if not (data := files.get_gpt_data()):
        logger.debug("GPT history is empty")
        return

    # unpack data and store the request: response, match ratio in a new dict
    new_req = request.lower()
    ratios = {}
    for d in data:
        ex_req = d["request"].lower()
        if ex_req == new_req:
            logger.info("Identical historical request: '%s'", d["request"])
            return d["response"]
        ratios[d["request"]] = (
            d["response"],
            difflib.SequenceMatcher(a=ex_req, b=new_req).ratio(),
        )

    # no identical requests found in history, and reuse threshold was not set
    if not models.env.ollama_reuse_threshold:
        logger.warning(
            "No identical requests found in history, and reuse threshold was not set."
        )
        return

    # sort the new dict in reverse order so the closest match gets returned first
    ratios = collections.OrderedDict(
        sorted(ratios.items(), key=lambda kv: kv[1][1], reverse=True)
    )

    # iterate over the ordered dict to look for numbers in existing requests and ignore them
    for existing_request, response_ratio in ratios.items():
        if response_ratio[1] >= models.env.ollama_reuse_threshold and not any(
            word.isdigit() for word in existing_request
        ):
            logger.info(
                "Closest historical request [%s]: '%s'",
                response_ratio[1],
                existing_request,
            )
            return response_ratio[0]


def create_model_file() -> None:
    """Creates ``Modelfile`` if not found."""
    if not os.path.isfile(models.fileio.ollama_model_file):
        logger.info(
            "'%s' not found, creating one at '%s'",
            os.path.basename(models.fileio.ollama_model_file),
            os.path.basename(models.fileio.root),
        )
        logger.info(
            "Feel free to modify this file in the future for custom instructions"
        )
        template = jinja2.Template(source=templates.llama.modelfile)
        rendered = template.render(MODEL_NAME=models.env.ollama_model)
        with open(models.fileio.ollama_model_file, "w") as file:
            file.write(rendered)
            file.flush()


def customize_model() -> None:
    """Uses the CLI to customize the model."""
    create_model_file()
    try:
        for res in ollama.create(
            model=models.env.ollama_model,
            from_=models.fileio.ollama_model_file,
            stream=True,
        ):
            logger.info(res["status"])
    except ollama.ResponseError as error:
        logger.error(error)


def setup_local_instance() -> None | NoReturn:
    """Attempts to set up ollama with a local instance."""
    try:
        llama_models = ollama.list().get("models")
    except (httpcore.ConnectError, httpx.ConnectError) as error:
        logger.error(error)
        logger.error(
            "Ollama client is either not installed or not running, refer: https://ollama.com/download"
        )
        raise ValueError
    for model in llama_models:
        if model.get("name") == models.env.ollama_model:
            logger.info(f"Model {models.env.ollama_model!r} found")
            break
    else:
        # To run manually: ollama run llama2
        logger.info(f"Downloading {models.env.ollama_model!r}")
        try:
            ollama.pull(models.env.ollama_model)
        except ollama.ResponseError as error:
            logger.error(error)
            warnings.warn(
                f"\n\tInvalid model name: {models.env.ollama_model}\n"
                "Refer https://github.com/ollama/ollama/blob/main/README.md#model-library for valid models",
                UserWarning,
            )
            raise ValueError
    customize_model()


class Ollama:
    """Wrapper for Ollama client that initiates the private AI.

    >>> Ollama

    """

    def __init__(self):
        """Instantiates the model and runs it locally."""
        if models.env.ollama_server:
            self.client = ollama.Client(host=models.env.ollama_server)
        else:
            setup_local_instance()
            self.client = ollama.Client()
        try:
            self.client.list()
        except (
            httpx.HTTPError,
            httpx.ConnectTimeout,
            httpx.ConnectError,
            httpx.TransportError,
        ) as error:
            logger.error(error)

    def request_model(self, request: str) -> Generator[str]:
        """Interacts with the model with a request and yields the response.

        Args:
            request:

        Yields:
            Streaming response from the model.
        """
        for res in self.client.generate(
            model=models.env.ollama_model,
            prompt=request,
            stream=True,
            options=ollama.Options(num_predict=100),
        ):
            # noinspection PyTypeChecker
            yield res["response"]
            # noinspection PyTypeChecker
            if res["done"]:
                break

    def generator(self, phrase: str) -> List[str]:
        """Returns the streaming response from the model in a list."""
        return list(self.request_model(phrase))

    def query(self, phrase: str) -> None:
        """Queries the Ollama api with the request and speaks the response.

        See Also:
            This plugin can fetch responses from a mapping file for, reusability when requests are identical.

        Args:
            phrase: Takes the phrase spoken as an argument.
        """
        if response := existing_response(request=phrase):
            speaker.speak(text=response)
            return
        try:
            process = ThreadPool(processes=1).apply_async(
                self.generator, args=(phrase,)
            )
            model_response = process.get(models.env.ollama_timeout)
        except (ollama.ResponseError, ThreadTimeoutError) as error:
            logger.error("%s - %s", type(error), error)
            static_responses.un_processable()
            return
        if model_response:
            reply = "".join(model_response)
            Thread(target=dump_history, args=(phrase, reply)).start()
            speaker.speak(text=reply)
        else:
            logger.error("Unable to process response for %s", phrase)
            static_responses.un_processable()


if models.startup_gpt:
    if models.env.ollama_reuse_threshold:
        start = (
            f"Initiating GPT instance for {models.settings.pname!r} with a "
            f"reuse threshold of '{models.env.ollama_reuse_threshold:.2f}'"
        )
    else:
        start = f"Initiating GPT instance for {models.settings.pname}"
    logger.info(start)
    if models.settings.pname == "JARVIS":
        support.write_screen(start)
    try:
        instance = Ollama()
        finish = f"GPT instance has been loaded for {models.settings.pname!r}"
        if models.settings.pname == "JARVIS":
            support.write_screen(finish)
        logger.info(finish)
    except ValueError:
        logger.error("Failed to load GPT instance for '%s'", models.settings.pname)
        instance = None
else:
    instance = None
