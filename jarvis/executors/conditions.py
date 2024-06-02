import warnings
from threading import Thread

from jarvis.executors import (
    custom_conditions,
    functions,
    listener_controls,
    method,
    others,
    restrictions,
    static_responses,
    unconditional,
    word_match,
)
from jarvis.modules.audio import speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.transformer import gpt
from jarvis.modules.utils import shared, support


def conditions(phrase: str) -> None:
    """Conditions function is used to check the message processed.

    Uses the keywords to match pre-defined conditions and trigger the appropriate function which has dedicated task.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Raises:
        StopSignal:
        When requested to stop Jarvis.
    """
    # Allow conditions during offline communication
    if (
        not shared.called_by_offline
        and not listener_controls.get_listener_state()
        # WATCH OUT: "activate" and "enable" are hard coded
        and not all(
            (
                "activate" in phrase or "enable" in phrase,
                word_match.word_match(
                    phrase=phrase, match_list=keywords.keywords["listener_control"]
                ),
            )
        )
    ):
        logger.info("Ignoring '%s' since listener is deactivated.", phrase)
        return
    if "*" in phrase:
        others.abusive(phrase)
        return

    function_map = functions.function_mapping()
    if shared.called_by_offline and restrictions.restricted(phrase=phrase):
        return
    if custom_conditions.custom_conditions(phrase=phrase, function_map=function_map):
        return

    for category, identifiers in keywords.keywords.items():
        if matched := word_match.word_match(phrase=phrase, match_list=identifiers):
            logger.debug("'%s' matched the category '%s'", matched, category)

            # custom rules for additional keyword matching
            if category == "send_notification":
                if "send" not in phrase.lower():
                    continue
            if category in ("distance", "kill"):
                if word_match.word_match(
                    phrase=phrase, match_list=keywords.keywords["avoid"]
                ):
                    continue
            if category == "speed_test":
                if not (
                    "internet" in phrase.lower()
                    or "connection" in phrase.lower()
                    or "run" in phrase.lower()
                ):
                    continue

            # Stand alone - Internally used [skip for both main and offline processes]
            if category in ("avoid", "ok", "exit_", "ngrok", "secrets"):
                continue

            # Requires manual intervention [skip for offline communicator]
            if shared.called_by_offline and category in (
                "kill",
                "report",
                "repeat",
                "directions",
                "notes",
                "faces",
                "music",
                "voice_changer",
                "restart_control",
                "shutdown",
            ):
                # WATCH OUT: for changes in function name
                if (
                    models.settings.pname
                    in ("background_tasks", "telegram_api", "jarvis_api")
                    and category == "restart_control"
                ):
                    logger.info(
                        "Allowing '%s' through the category '%s', for the process: '%s'",
                        phrase,
                        category,
                        models.settings.pname,
                    )
                else:
                    static_responses.not_allowed_offline()
                    return

            if function_map.get(category):  # keyword category matches function name
                # call function with phrase as arg by default
                method.executor(function_map[category], phrase)
                if category in ("sleep_control", "sentry"):
                    return
            else:
                # edge case scenario if a category has matched but the function name is incorrect or not imported
                warnings.warn(
                    "Condition matched for '%s' but there is not function to call."
                    % category
                )
            return
    # GPT instance available only for communicable processes
    # WATCH OUT: for changes in function name
    if models.settings.pname not in ("JARVIS", "telegram_api", "jarvis_api"):
        logger.warning("%s reached unrecognized category", models.settings.pname)
        return
    logger.info("Received unrecognized lookup parameter: %s", phrase)
    Thread(target=support.unrecognized_dumper, args=[{"CONDITIONS": phrase}]).start()
    if not unconditional.google_maps(query=phrase):
        if gpt.instance:
            gpt.instance.query(phrase=phrase)
        elif response := gpt.existing_response(request=phrase):
            speaker.speak(text=response)
        else:
            static_responses.un_processable()
