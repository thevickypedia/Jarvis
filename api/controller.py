from logging import Filter, LogRecord
from os import remove
from sys import path
from time import sleep


class EndpointFilter(Filter):
    """Class to initiate endpoint filter in logs while preserving other access logs.

    >>> EndpointFilter

    """

    def filter(self, record: LogRecord) -> bool:
        """Filter out the mentioned ``/endpoint`` from log streams.

        Args:
            record: ``LogRecord`` represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.
        """
        return record.getMessage().find("/docs") == -1


def startup():
    """Calls ``Keywords`` class to get the return values of methods that are compatible with ``offline_communicator``.

    See Also:
        - ``offline_communicator`` cannot process commands that require an interaction with the user.
        - This is because ``speaker.stop()`` will stop the ``speaker.runAndWait()`` in an interaction.
        - This action will raise a ``RuntimeError`` since the ``speaker.endLoop()`` would have already started.

    Returns:
        list:
        Flat list from a matrix (list of lists) after removing the duplicates.
    """
    path.append('..')
    from helper_functions.keywords import Keywords
    path.remove('..')
    keywords = Keywords
    offline_words = [keywords.sleep(),
                     keywords.exit(),
                     keywords.alarm(),
                     keywords.restart(),
                     keywords.time(),
                     keywords.apps(),
                     keywords.distance(),
                     keywords.face_detection(),
                     keywords.facts(),
                     keywords.weather(),
                     keywords.flip_a_coin(),
                     keywords.jokes(),
                     keywords.list_todo(),
                     keywords.geopy(),
                     keywords.gmail(),
                     keywords.google_home(),
                     keywords.guard_enable(),
                     keywords.guard_disable(),
                     keywords.lights(),
                     keywords.robinhood(),
                     keywords.date(),
                     keywords.ip_info(),
                     keywords.brightness(),
                     keywords.news(),
                     keywords.location(),
                     keywords.personal_cloud(),
                     keywords.vpn_server(),
                     keywords.reminder(),
                     keywords.system_info(),
                     keywords.system_vitals(),
                     keywords.volume(),
                     keywords.meaning(),
                     keywords.meetings()]
    matrix_to_list = sum(offline_words, []) or [item for sublist in offline_words for item in sublist]
    return [i.strip() for n, i in enumerate(matrix_to_list) if i not in matrix_to_list[n + 1:]]


def delete_offline_response(flag: bool = False) -> None:
    """Delete the ``offline_response`` file created by Jarvis after 2 seconds.

    Args:
        flag: Flag set to False by default. Decides whether or not to delete the ``offline_response`` file.
    """
    if flag:
        sleep(2)
        remove('../offline_response')
