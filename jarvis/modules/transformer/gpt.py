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
import time
import warnings
from threading import Thread

import httpcore
import httpx
import ollama

from jarvis.executors import files, static_responses
from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger
from jarvis.modules.models import models


def dump_history(request: str, response: str) -> None:
    """Dump responses from GPT to a yaml file for future response.

    Args:
        request: Request from user.
        response: Response from GPT.
    """
    data = files.get_gpt_data()
    data.append({"request": request, "response": response})
    files.put_gpt_data(data)


# todo: customize the model to improve response time and remove this functionality
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

        - To get around this, refer `env-variables section of read me <https://github.com/thevickypedia/Jarvis#env-
          variables>`__ about ``OLLAMA_REUSE_THRESHOLD``

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
                "Ollama client has to be installed, refer: https://ollama.com/download"
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
        self.client = ollama.Client()

    def query(self, phrase: str, respond: bool = True) -> None:
        """Queries the Ollama api with the request and speaks the response.

        See Also:
            - This plugin can fetch responses from a mapping file for, reusability when requests are identical.

        Args:
            phrase: Takes the phrase spoken as an argument.
            respond: Takes a boolean flag to suppress response.
        """
        if response := existing_response(request=phrase):
            speaker.speak(text=response)
            return
        start = time.time()
        response = []
        # todo: implement ollama_timeout functionality
        #  timeout should be skipped when respond is set to False
        try:
            for idx, res in enumerate(
                self.client.generate(
                    model=models.env.ollama_model,
                    prompt=phrase,
                    stream=True,
                    options=ollama.Options(num_predict=100),
                )
            ):
                if idx == 0:
                    # todo: change this to debug before releasing
                    logger.info(
                        f"Generator started in {round(float(time.time() - start), 2)}s"
                    )
                # noinspection PyTypeChecker
                response.append(res["response"])
                # noinspection PyTypeChecker
                if res["done"]:
                    break
            # todo: change this to debug before releasing
            logger.info(
                f"Generator completed in {round(float(time.time() - start), 2)}s\n\n"
            )
        except ollama.ResponseError as error:
            logger.error(error)
            static_responses.un_processable() if respond else None
            return
        if respond and response:
            reply = "".join(response)
            Thread(target=dump_history, args=(phrase, reply)).start()
            speaker.speak(text=reply)
        elif response:
            logger.info("Request: %s", phrase)
            logger.info("Response: %s", "".join(response))
        else:
            logger.error("Unable to process response for %s", phrase)
            static_responses.un_processable() if respond else None


# WATCH OUT: for changes in function name
if (
    models.settings.pname in ("JARVIS", "telegram_api", "jarvis_api")
    and not models.env.limited
):
    if models.env.ollama_reuse_threshold:
        logger.info(
            "Initiating GPT instance for '%s' with a reuse threshold of '%.2f'",
            models.settings.pname,
            models.env.ollama_reuse_threshold,
        )
    else:
        logger.info("Initiating GPT instance for '%s'", models.settings.pname)
    try:
        instance = Ollama()
        logger.info("GPT instance has been loaded for '%s'", models.settings.pname)
        instance.query(
            phrase=(
                "Conversation Guidelines:\n\n"
                "1. Keep your responses as short as possible (less than 100 words)\n"
                "2. Use commas and full stops but DO NOT use emojis or other punctuations.\n"
                "3. Your responses will be fed into a voice model, so ONLY one response for each request."
            ),
            respond=False,
        )
    except ValueError:
        logger.error("Failed to load GPT instance for '%s'", models.settings.pname)
        instance = None
else:
    instance = None
