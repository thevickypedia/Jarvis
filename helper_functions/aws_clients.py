import sys

from boto3 import client


def gatherer():
    """Uses the name of the function that called the gatherer as param name and returns the param value."""
    # noinspection PyUnresolvedReferences,PyProtectedMember
    return client('ssm').get_parameter(Name=f'/Jarvis/{sys._getframe(1).f_code.co_name}',
                                       WithDecryption=True)['Parameter']['Value']


class AWSClients:
    """All the required oauth and api keys are stored in ssm parameters and are fetched where ever required.

    >>> AWSClients

    """

    @staticmethod
    def weather_api():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def news_api():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def robinhood_user():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def robinhood_pass():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def robinhood_qr():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def icloud_pass():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def icloud_recovery():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def icloud_user():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def gmail_user():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def gmail_pass():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def phone():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def maps_api():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def git_user():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def git_pass():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def tv_mac():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def tv_client_key():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def birthday():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def offline_receive_user():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def offline_receive_pass():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def offline_sender():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def think_id():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()

    @staticmethod
    def router_pass():
        """Calls gatherer which uses the caller func name to return the param value.

        Returns:
            Parameter value received from gatherer.

        """
        return gatherer()
