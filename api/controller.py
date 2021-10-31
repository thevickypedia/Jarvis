from hashlib import sha1
from logging import Filter, LogRecord
from sys import path
from uuid import UUID, uuid4


class EndpointFilter(Filter):
    """Class to initiate ``/docs`` filter in logs while preserving other access logs.

    >>> EndpointFilter

    """

    def filter(self, record: LogRecord) -> bool:
        """Filter out logging at ``/docs`` from log streams.

        Args:
            record: ``LogRecord`` represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.
        """
        return record.getMessage().find("/docs") == -1


class InvestmentFilter(Filter):
    """Class to initiate ``/investment`` filter in logs while preserving other access logs.

    >>> InvestmentFilter

    """

    def filter(self, record: LogRecord) -> bool:
        """Filter out logging at ``/investment?token=`` from log streams.

        Args:
            record: ``LogRecord`` represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.
        """
        return record.getMessage().find("/investment?token=") == -1


def offline_compatible() -> list:
    """Calls ``Keywords`` and ``Conversation`` classes to get the variables that are compatible.

    See Also:
        - ``offline_communicator`` cannot process commands that require an interaction with the user.
        - This is because ``speaker.stop()`` will stop the ``speaker.runAndWait()`` in an interaction.
        - This action will raise a ``RuntimeError`` since the ``speaker.endLoop()`` would have already started.

    Returns:
        list:
        Flat list from a matrix (list of lists) after removing the duplicates.
    """
    path.append('..')
    from helper_functions.conversation import Conversation
    from helper_functions.keywords import Keywords
    path.remove('..')
    keywords = Keywords
    conversation = Conversation
    offline_words = [keywords.sleep_control,
                     keywords.exit,
                     keywords.alarm,
                     keywords.restart_control,
                     keywords.current_time,
                     keywords.apps,
                     keywords.distance,
                     keywords.face_detection,
                     keywords.facts,
                     keywords.weather,
                     keywords.flip_a_coin,
                     keywords.jokes,
                     keywords.todo,
                     keywords.locate_places,
                     keywords.gmail,
                     keywords.google_home,
                     keywords.guard_enable,
                     keywords.guard_disable,
                     keywords.lights,
                     keywords.robinhood,
                     keywords.current_date,
                     keywords.ip_info,
                     keywords.brightness,
                     keywords.news,
                     keywords.location,
                     keywords.personal_cloud,
                     keywords.vpn_server,
                     keywords.reminder,
                     keywords.system_info,
                     keywords.system_vitals,
                     keywords.volume,
                     keywords.meaning,
                     keywords.meetings,
                     conversation.about_me,
                     conversation.capabilities,
                     conversation.form,
                     conversation.greeting,
                     conversation.languages,
                     conversation.what,
                     conversation.whats_up,
                     conversation.who]
    matrix_to_list = sum(offline_words, []) or [item for sublist in offline_words for item in sublist]
    return [i.strip() for n, i in enumerate(matrix_to_list) if i not in matrix_to_list[n + 1:]]  # remove dupes


def hashed(key: UUID) -> str:
    """Generates sha from UUID.

    Args:
        key: Takes the UUID generated as an argument.

    Returns:
        str:
        Hashed value of the UUID received.
    """
    return sha1(key.bytes + bytes(key.hex, "utf-8")).digest().hex()


def keygen() -> str:
    """Generates key using hashed uuid4.

    Returns:
        str:
        Returns hashed UUID as a string.
    """
    return hashed(key=uuid4())
