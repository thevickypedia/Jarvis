# noinspection PyUnresolvedReferences
"""Module to create a response object using a dictionary.

>>> Responder

"""


class Response:
    """Class to format the response, so that it can be accessed as an object variable.

    >>> Response

    """

    def __init__(self, dictionary: dict):
        """Extracts the property ``ok`` from a dictionary.

        Args:
            dictionary: Takes a dictionary of key-value pairs as an argument.
        """
        self.raw: dict = dictionary
        self._ok: bool = dictionary.get('ok')
        self._info: str = dictionary.get('msg')

    @property
    def ok(self) -> bool:
        """Returns the extracted class variable.

        Returns:
            bool:
            ``True`` or ``False`` based on the arg value received.
        """
        return self._ok

    @property
    def info(self) -> str:
        """Returns the extracted class variable.

        Returns:
            bool:
            ``True`` or ``False`` based on the arg value received.
        """
        return self._info
