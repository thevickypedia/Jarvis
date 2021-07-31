import sys

from boto3 import client


def gatherer() -> str:
    """Uses the name of the function that called the gatherer as param name and returns the param value.

    Returns:
        str:
        A a decrypted secure string of the caller function name.

    """
    # noinspection PyUnresolvedReferences,PyProtectedMember
    return client('ssm').get_parameter(Name=f'/Jarvis/{sys._getframe(1).f_code.co_name}',
                                       WithDecryption=True)['Parameter']['Value']


class AWSClients:
    """All the required oauth and api keys are stored in ssm parameters and are fetched where ever required.

    >>> AWSClients

    """

    @staticmethod
    def weather_api() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def news_api() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def robinhood_user() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def robinhood_pass() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def robinhood_qr() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def icloud_pass() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def icloud_recovery() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def icloud_user() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def gmail_user() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def gmail_pass() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def phone_number() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def maps_api() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def git_user() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def git_pass() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def tv_mac() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def tv_client_key() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def birthday() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def offline_receive_user() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def offline_receive_pass() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def offline_phrase() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def think_id() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def router_pass() -> str:
        """Calls `gatherer` which uses the caller func name to return the param value.

        Returns:
            str:
            Parameter value received from gatherer.

        """
        return gatherer()
