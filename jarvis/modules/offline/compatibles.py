# noinspection PyUnresolvedReferences
"""Modules to store offline compatible words and wrap as a list.

>>> Compatibles

"""

from typing import List

from jarvis.modules.conditions import conversation
from jarvis.modules.conditions import keywords as keywords_mod
from jarvis.modules.utils import util


def offline_compatible() -> List[str]:
    """Calls ``Keywords`` and ``Conversation`` classes to get the variables that do not require user interaction.

    Returns:
        list:
        Flat list from a matrix (list of lists) after removing the duplicates.
    """
    keywords = keywords_mod.keywords
    offline_words = [keywords.sleep_control,
                     keywords.set_alarm,
                     keywords.current_time,
                     keywords.photo,
                     keywords.apps,
                     keywords.distance,
                     keywords.faces,
                     keywords.facts,
                     keywords.weather,
                     keywords.wikipedia_,
                     keywords.flip_a_coin,
                     keywords.jokes,
                     keywords.todo,
                     keywords.locate_places,
                     keywords.read_gmail,
                     keywords.google_home,
                     keywords.guard_enable,
                     keywords.guard_disable,
                     keywords.lights,
                     keywords.robinhood,
                     keywords.current_date,
                     keywords.ip_info,
                     keywords.brightness,
                     keywords.news,
                     keywords.listener_control,
                     keywords.location,
                     keywords.vpn_server,
                     keywords.reminder,
                     keywords.system_info,
                     keywords.system_vitals,
                     keywords.volume,
                     keywords.meaning,
                     keywords.meetings,
                     keywords.events,
                     keywords.car,
                     keywords.garage,
                     keywords.github,
                     keywords.speed_test,
                     keywords.ngrok,
                     keywords.locate,
                     keywords.send_notification,
                     keywords.television,
                     keywords.automation,
                     keywords.background_tasks,
                     keywords.version,
                     keywords.simulation,
                     conversation.age,
                     conversation.about_me,
                     conversation.capabilities,
                     conversation.form,
                     conversation.greeting,
                     conversation.languages,
                     conversation.what,
                     conversation.whats_up,
                     conversation.who]
    return util.remove_duplicates(input_=util.matrix_to_flat_list(input_=offline_words))
