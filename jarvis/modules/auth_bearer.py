# noinspection PyUnresolvedReferences
"""Module to set up bearer authentication.

>>> AuthBearer

"""

from requests.auth import AuthBase
from requests.models import PreparedRequest


class BearerAuth(AuthBase):
    # This doc string has URL split into multiple lines
    """Instantiates ``BearerAuth`` object.

    >>> BearerAuth

    References:
        `New Forms of Authentication <https://requests.readthedocs.io/en/latest/user/authentication/#new
        -forms-of-authentication>`__
    """

    def __init__(self, token: str):
        """Initializes the class and assign object members.

        Args:
            token: Token for bearer auth.
        """
        self.token = token

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        """Override built-in.

        Args:
            request: Takes prepared request as an argument.

        Returns:
            PreparedRequest:
            Returns the request after adding the auth header.
        """
        request.headers["authorization"] = "Bearer " + self.token
        return request
