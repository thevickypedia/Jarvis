import warnings
from threading import Thread

from jarvis.executors import (custom_conditions, functions, listener_controls,
                              others, static_responses, unconditional,
                              word_match)
from jarvis.modules.conditions import keywords
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.transformer import gpt
from jarvis.modules.utils import shared, support


def conditions(phrase: str) -> bool:
    """Conditions function is used to check the message processed.

    Uses the keywords to match pre-defined conditions and trigger the appropriate function which has dedicated task.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Raises:
        StopSignal:
        When requested to stop Jarvis.

    Returns:
        bool:
        Boolean True only when asked to sleep for conditioned sleep message.
    """
    # Allow conditions during offline communication
    if not shared.called_by_offline and \
            not listener_controls.get_listener_state() and \
            not all(("activate" in phrase or "enable" in phrase,  # WATCH OUT: "activate" and "enable" are hard coded
                     word_match.word_match(phrase=phrase, match_list=keywords.keywords['listener_control']))):
        logger.info("Ignoring '%s' since listener is deactivated.", phrase)
        return False
    if "*" in phrase:
        others.abusive(phrase)
        return False

    function_map = functions.function_mapping()
    if custom_conditions.custom_conditions(phrase=phrase, function_map=function_map):
        return False

    for category, identifiers in keywords.keywords.items():
        if word_match.word_match(phrase=phrase, match_list=identifiers):

            # custom rules for additional keyword matching
            if category == "send_notification":
                if "send" not in phrase.lower():
                    continue
            if category in ("distance", "kill"):
                if word_match.word_match(phrase=phrase, match_list=keywords.keywords['avoid']):
                    continue
            if category == "speed_test":
                if not ('internet' in phrase.lower() or 'connection' in phrase.lower() or 'run' in phrase.lower()):
                    continue

            # Stand alone - Internally used [skip for both main and offline processes]
            if category in ("avoid", "ok", "exit_", "ngrok", "secrets"):
                continue

            # Requires manual intervention [skip for offline communicator]
            if shared.called_by_offline and category in ('kill', 'report', 'repeat', 'directions', 'notes',
                                                         'music', 'voice_changer', 'restart_control', 'shutdown'):
                # WATCH OUT: for changes in function name
                if models.settings.pname == "background_tasks" and category == "restart_control":
                    # Eg: Allowing 'restart' through the category 'restart_control' for the process 'background_tasks'
                    logger.info("Allowing '%s' through the category '%s', for the process: '%s'",
                                phrase, category, models.settings.pname)
                else:
                    static_responses.not_allowed_offline()
                    return False

            if function_map.get(category):  # keyword category matches function name
                function_map[category](phrase)  # call function with phrase as arg by default
                if category in ("sleep_control", "sentry"):
                    return True  # repeat listeners are ended and wake word detection is activated
            else:
                # edge case scenario if a category has matched but the function name is incorrect or not imported
                warnings.warn("Condition matched for '%s' but there is not function to call." % category)
            return False
    # GPT instance available only for communicable processes
    if models.settings.pname not in ('JARVIS', 'telegram_api', 'fast_api'):
        logger.warning("%s reached unrecognized category", models.settings.pname)
        return False
    logger.info("Received unrecognized lookup parameter: %s", phrase)
    Thread(target=support.unrecognized_dumper, args=[{'CONDITIONS': phrase}]).start()
    if not unconditional.google_maps(query=phrase):
        if gpt.instance:
            gpt.instance.query(phrase=phrase)
        else:
            static_responses.un_processable()
