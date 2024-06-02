"""Generative Pre-trained Transformer with Ollama API client.

Warnings:
    - This module uses a pre-trained transformer to generate predictive responses.
    - Due to the size of machine learning models, this feature will be disabled in limited mode.

RAM Requirements:
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
import subprocess
import warnings
from collections.abc import Generator

# noinspection PyProtectedMember
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import List

import httpcore
import httpx
import ollama

from jarvis.executors import files, static_responses
from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support


def dump_history(request: str, response: str) -> None:
    """Dump responses from GPT to a yaml file for future response.

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


class Customizer:
    """Customize prompt for the model with pre-defined instructions.

    >>> Customizer

    """

    def __init__(self):
        """Initializes the model name."""
        self.model_name = "jarvis"

    def run(self) -> str:
        """Runs the customizer with SDK as the primary option and CLI as secondary.

        Returns:
            str:
            Returns the model name.
        """
        try:
            self.customize_model_sdk()
            return self.model_name
        except ollama.ResponseError as error:
            logger.error(error)
        try:
            self.customize_model_cli()
            return self.model_name
        except (subprocess.SubprocessError, AssertionError) as error:
            logger.error(error)
        return models.env.ollama_model

    def customize_model_cli(self) -> None:
        """Uses the CLI to customize the model."""
        model_file = os.path.join(os.path.dirname(__file__), "Modelfile")
        model_file = model_file.lstrip(os.getcwd())
        process = subprocess.Popen(
            f"ollama create {self.model_name} -f {model_file}",
            shell=True,
            universal_newlines=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for line in process.stdout:
            logger.info(line.strip())
        process.wait()
        for line in process.stderr:
            logger.warning(line.strip())
        assert process.returncode == 0, "Failed to customize the model"

    def customize_model_sdk(self) -> None:
        """Uses the CLI to customize the model.

        Warnings:
            `Model creation with SDK is currently broke <https://github.com/ollama/ollama-python/issues/171>`__.
        """
        model_file = os.path.join(os.path.dirname(__file__), "Modelfile")
        for res in ollama.create(
            model=self.model_name, modelfile=model_file, stream=True
        ):
            logger.info(res["response"])
            if res["done"]:
                break


class Ollama:
    """Wrapper for Ollama client that initiates the private AI.

    >>> Ollama

    """

    def __init__(self):
        """Instantiates the model and runs it locally."""
        try:
            self.models = ollama.list().get("models")
        except (httpcore.ConnectError, httpx.ConnectError) as error:
            logger.error(error)
            logger.error(
                "Ollama client is either not installed or not running, refer: https://ollama.com/download"
            )
            raise ValueError
        for model in self.models:
            if model.get("name") == f"{models.env.ollama_model}:latest":
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
        self.model_name = Customizer().run()
        self.client = ollama.Client()

    def request_model(self, request: str) -> Generator[str]:
        """Interacts with the model with a request and yields the response.

        Args:
            request:

        Yields:
            Streaming response from the model.
        """
        for res in self.client.generate(
            model=self.model_name,
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
