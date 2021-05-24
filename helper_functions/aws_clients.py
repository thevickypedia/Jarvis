import sys

from boto3 import client


def gatherer():
    """Uses the name of the function that called the gatherer as param name and returns the param value."""
    # noinspection PyUnresolvedReferences,PyProtectedMember
    return client('ssm').get_parameter(Name=f'/Jarvis/{sys._getframe(1).f_code.co_name}',
                                       WithDecryption=True)['Parameter']['Value']


class AWSClients:
    """All the required oauth and api keys are stored in ssm parameters and are fetched where ever required."""

    @staticmethod
    def weather_api():
        return gatherer()

    @staticmethod
    def news_api():
        return gatherer()

    @staticmethod
    def robinhood_user():
        return gatherer()

    @staticmethod
    def robinhood_pass():
        return gatherer()

    @staticmethod
    def robinhood_qr():
        return gatherer()

    @staticmethod
    def icloud_pass():
        return gatherer()

    @staticmethod
    def icloud_recovery():
        return gatherer()

    @staticmethod
    def icloud_user():
        return gatherer()

    @staticmethod
    def gmail_user():
        return gatherer()

    @staticmethod
    def gmail_pass():
        return gatherer()

    @staticmethod
    def phone():
        return gatherer()

    @staticmethod
    def maps_api():
        return gatherer()

    @staticmethod
    def git_user():
        return gatherer()

    @staticmethod
    def git_pass():
        return gatherer()

    @staticmethod
    def tv_mac():
        return gatherer()

    @staticmethod
    def tv_client_key():
        return gatherer()

    @staticmethod
    def birthday():
        return gatherer()

    @staticmethod
    def offline_receive_user():
        return gatherer()

    @staticmethod
    def offline_receive_pass():
        return gatherer()

    @staticmethod
    def offline_sender():
        return gatherer()

    @staticmethod
    def think_id():
        return gatherer()

    @staticmethod
    def router_pass():
        return gatherer()
