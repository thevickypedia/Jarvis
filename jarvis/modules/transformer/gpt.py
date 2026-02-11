"""Generative Pre-trained Transformer with Ollama API client.

Warnings:
    - This module uses a pre-trained transformer to generate predictive responses.
    - Although this feature is enabled by default, please note that machine learning models are memory beasts.
    - Please refer the following minimum requirements before choosing the right model.

**RAM Requirements**
    - 8 GB to run the 7B models
    - 16 GB to run the 13B models
    - 32 GB to run the 33B models

References:
    - Model Artifactory: https://ollama.com/library
    - Alternatives: https://huggingface.co/meta-llama
    - Supported Models: https://github.com/ollama/ollama/blob/main/README.md#model-library
"""

import collections
import difflib
import time
from collections.abc import Generator

# noinspection PyProtectedMember
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import List

import ollama

from jarvis.executors import files, static_responses
from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
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
        logger.debug("request: '%s' contains numbers in it, so skipping existing search", request)
        return None
    if not (data := files.get_gpt_data()):
        logger.debug("GPT history is empty")
        return None

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
        logger.warning("No identical requests found in history, and reuse threshold was not set.")
        return None

    # sort the new dict in reverse order so the closest match gets returned first
    ratios = collections.OrderedDict(sorted(ratios.items(), key=lambda kv: kv[1][1], reverse=True))

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
    return None


SYSTEM_MESSAGE = """You are Jarvis, a virtual assistant designed by Mr. Rao.
Answer only as Jarvis.

Conversation Rules:
1. Keep every response under 100 words.
2. Respond in exactly one complete sentence.
3. Use proper commas and full stops.
4. Do not use emojis, special symbols, bullet points, or extra formatting.
5. Be clear, confident, and concise."""


class Ollama:
    """Wrapper for Ollama client that initiates the private AI.

    >>> Ollama

    """

    def __init__(self):
        """Instantiates the model and runs it locally."""
        if models.env.ollama_server:
            self.client = ollama.Client(host=str(models.env.ollama_server))
        else:
            self.client = ollama.Client()
        try:
            self.client.list()
        except Exception as error:
            logger.error(error)
            raise ValueError(error.__str__())
        self.create_custom_model()

    def create_custom_model(self) -> None:
        """Creates the custom model using the base model.

        See Also:
            - | If the base model doesn't exist on the server,
              | the create endpoint automatically pulls the model from Ollama library.
            - Custom model is created to isolate the system message and custom parameter options (mentioned below)

        Attributes:
            - temperature (float, 0.0–2.0): Higher is more creative and random, lower is more focused and deterministic.
            - | top_p (float, 0.0–1.0): Higher considers more possible tokens (more diverse),
              | lower limits choices to the most probable ones.
            - num_predict (int, 1+): Higher generates longer responses, lower generates shorter responses.
            - repeat_penalty (float, 0.0–2.0+): Higher reduces repetition, lower allows more repeated words or phrases.
            - | num_ctx (int, 128+): Higher allows more context to be remembered,
              | lower limits how much context the model can use.

        References:
            https://docs.ollama.com/modelfile#parameter
        """
        self.client.create(
            model=models.env.ollama_custom_model,
            from_=models.env.ollama_base_model,
            parameters=ollama.Options(temperature=0.6, top_p=0.85, num_predict=40, repeat_penalty=1.05, num_ctx=2048),
            system=SYSTEM_MESSAGE,
        )

    def request_model(self, request: str) -> Generator[str]:
        """Interacts with the model with a request and yields the response.

        Args:
            request:

        Yields:
            Streaming response from the model.
        """
        for res in self.client.generate(
            model=models.env.ollama_custom_model,
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
            logger.info("GPT: Rendering response from existing results.")
            speaker.speak(text=response)
            return
        logger.debug("GPT: Generating response from: %s", models.env.ollama_custom_model)
        try:
            start_time = time.time()
            process = ThreadPool(processes=1).apply_async(self.generator, args=(phrase,))
            model_response = process.get(models.env.ollama_timeout)
            token_gen = support.time_converter(time.time() - start_time)
            logger.info(
                "GPT: Finished generating response from: %s in %s",
                models.env.ollama_custom_model,
                token_gen,
            )
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
            f"Initiating GPT instance for {models.settings.pname.value!r} with a "
            f"reuse threshold of '{models.env.ollama_reuse_threshold:.2f}'"
        )
    else:
        start = f"Initiating GPT instance for {models.settings.pname.value!r}"
    logger.info(start)
    if models.settings.pname == enums.ProcessNames.jarvis:
        support.write_screen(start)
    try:
        instance = Ollama()
        finish = f"GPT instance has been loaded for {models.settings.pname.value!r}"
        if models.settings.pname == enums.ProcessNames.jarvis:
            support.write_screen(finish)
        logger.info(finish)
    except ValueError as start_error:
        logger.error("Failed to load GPT instance for '%s'", models.settings.pname)
        instance = None
        if models.settings.pname == enums.ProcessNames.jarvis:
            support.write_screen(f"Failed to load GPT instance: {start_error.__str__()!r}")
            time.sleep(3)
else:
    logger.info("Startup disabled for GPT")
    instance = None
