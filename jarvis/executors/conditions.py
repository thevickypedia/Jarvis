import warnings
from multiprocessing import current_process
from threading import Thread

from jarvis.executors.alarm import kill_alarm, set_alarm  # noqa
from jarvis.executors.automation import automation_handler  # noqa
from jarvis.executors.background_task import background_task_handler  # noqa
from jarvis.executors.car import car  # noqa
from jarvis.executors.comm_squire import send_notification  # noqa
from jarvis.executors.communicator import read_gmail  # noqa
from jarvis.executors.controls import (kill, restart_control, sentry,  # noqa
                                       shutdown, sleep_control)
from jarvis.executors.date_time import current_date, current_time  # noqa
from jarvis.executors.display_functions import brightness  # noqa
from jarvis.executors.face import faces  # noqa
from jarvis.executors.github import github  # noqa
from jarvis.executors.guard import guard_disable, guard_enable  # noqa
from jarvis.executors.internet import ip_info, speed_test  # noqa
from jarvis.executors.ios_functions import locate  # noqa
from jarvis.executors.lights import lights  # noqa
from jarvis.executors.listener_controls import get_listener_state  # noqa
from jarvis.executors.location import (directions, distance,  # noqa
                                       locate_places, location)
from jarvis.executors.myq_controller import garage  # noqa
from jarvis.executors.others import (abusive, apps, facts, flip_a_coin,  # noqa
                                     google_home, jokes, meaning, music, news,
                                     notes, photo, repeat, report, version)
from jarvis.executors.remind import reminder  # noqa
from jarvis.executors.robinhood import robinhood  # noqa
from jarvis.executors.simulator import simulation  # noqa
from jarvis.executors.static_responses import (about_me, age,  # noqa
                                               capabilities, form, greeting,
                                               languages, what, whats_up, who)
from jarvis.executors.system import system_info, system_vitals  # noqa
from jarvis.executors.todo_list import todo  # noqa
from jarvis.executors.tv import television  # noqa
from jarvis.executors.unconditional import google_maps
from jarvis.executors.volume import volume  # noqa
from jarvis.executors.vpn_server import vpn_server  # noqa
from jarvis.executors.weather import weather  # noqa
from jarvis.executors.wiki import wikipedia_  # noqa
from jarvis.executors.word_match import word_match
from jarvis.modules.audio.voices import voice_changer  # noqa
from jarvis.modules.conditions import conversation  # noqa
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import StopSignal  # noqa
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.meetings.events import events  # noqa
from jarvis.modules.meetings.ics_meetings import meetings  # noqa
from jarvis.modules.transformer import gpt
from jarvis.modules.utils import shared, support  # noqa


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
    if not get_listener_state() and not shared.called_by_offline:  # Allow conditions during offline communication
        logger.info("Ignoring '%s' since listener is deactivated.", phrase)
        return False
    if "*" in phrase:
        abusive(phrase)
        return False

    # # Re-sort the keyword dict object per the order in base keywords - Required only if OrderedDict is removed in base
    # keyword_dict = {}
    # for key, value in keywords_base.keyword_mapping().items():
    #     keyword_dict[key] = existing_kw_dict[key]
    for category, identifiers in keywords.keywords.__dict__.items():
        if word_match(phrase=phrase, match_list=identifiers):

            # custom rules for additional keyword matching
            if category == "send_notification":
                if "send" not in phrase.lower():
                    continue
            if category in ("distance", "kill"):
                if word_match(phrase=phrase, match_list=keywords.keywords.avoid):
                    continue
            if category == "speed_test":
                if not ('internet' in phrase.lower() or 'connection' in phrase.lower() or 'run' in phrase.lower()):
                    continue

            # Stand alone - Internally used
            if category in ("avoid", "ok", "exit_", "avoid", "ngrok", "secrets"):
                continue

            modules = globals()  # load all imported function names
            if modules.get(category):  # keyword category matches function name
                modules[category](phrase)  # call function with phrase as arg by default
                if category in ("sleep_control", "sentry"):
                    return True  # repeat listeners are ended and wake word detection is activated
            else:
                # edge case scenario if a category has matched but the function name is incorrect or not imported
                warnings.warn("Condition matched for '%s' but there is not function to call." % category)
            return False
    pname = current_process().name
    if pname not in ('JARVIS', 'telegram_api', 'fast_api'):  # GPT instance available only for communicable processes
        logger.warning("%s reached unrecognized category", pname)
        return False
    logger.info("Received unrecognized lookup parameter: %s", phrase)
    Thread(target=support.unrecognized_dumper, args=[{'CONDITIONS': phrase}]).start()
    if not google_maps(query=phrase):
        gpt.instance.query(phrase=phrase)
