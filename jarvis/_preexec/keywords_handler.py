import os
import warnings
from collections import OrderedDict

import yaml

from jarvis.modules.builtin_overrides import ordered_dump, ordered_load
from jarvis.modules.conditions import conversation, keywords
from jarvis.modules.models import enums, models
from jarvis.modules.utils import support


def load_ignores(data: dict) -> None:
    """Loads ``ignore_after`` and ``ignore_add`` list to avoid iterations on the same phrase."""
    # Keywords for which the ' after ' split should not happen.
    keywords.ignore_after = data["meetings"] + data["avoid"]
    # Keywords for which the ' and ' split should not happen.
    keywords.ignore_and = (
        data["send_notification"] + data["reminder"] + data["distance"] + data["avoid"]
    )


def rewrite_keywords() -> None:
    """Loads keywords.yaml file if available, else loads the base keywords module as an object."""
    keywords_src = OrderedDict(
        **keywords.keyword_mapping(), **conversation.conversation_mapping()
    )
    # WATCH OUT: for changes in keyword/function name
    if models.env.event_app:
        keywords_src["events"] = [
            models.env.event_app.lower(),
            support.ENGINE.plural(models.env.event_app),
        ]
    else:
        keywords_src["events"] = [
            enums.EventApp.CALENDAR.value,
            enums.EventApp.OUTLOOK.value,
        ]
    if os.path.isfile(models.fileio.keywords):
        with open(models.fileio.keywords) as dst_file:
            try:
                data = ordered_load(stream=dst_file, Loader=yaml.FullLoader) or {}
            except yaml.YAMLError as error:
                warnings.warn(message=str(error))
                data = None

        if not data:  # Either an error occurred when reading or a manual deletion
            if data is {}:
                warnings.warn(
                    f"\nSomething went wrong. {models.fileio.keywords!r} appears to be empty."
                    f"\nRe-sourcing {models.fileio.keywords!r} from base."
                )
        # compare as sorted, since this will allow changing the order of keywords in the yaml file
        elif (
            sorted(list(data.keys())) == sorted(list(keywords_src.keys()))
            and data.values()
            and all(data.values())
        ):
            keywords.keywords = data
            load_ignores(data)
            return
        else:  # Mismatch in keys
            warnings.warn(
                "\nData mismatch between base keywords and custom keyword mapping."
                "\nPlease note: This mapping file is only to change the value for keywords, not the key(s) itself."
                f"\nRe-sourcing {models.fileio.keywords!r} from base."
            )

    with open(models.fileio.keywords, "w") as dst_file:
        ordered_dump(keywords_src, stream=dst_file, indent=4)
    keywords.keywords = keywords_src
    load_ignores(keywords_src)


rewrite_keywords()
