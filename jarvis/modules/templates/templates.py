# noinspection PyUnresolvedReferences
"""Module to read all HTML templates and store as members of an object.

>>> AudioHandler

"""

import os

from jarvis.modules.models import models


class EmailTemplates:
    """HTML templates used to send outbound email.

    >>> EmailTemplates

    """

    if models.settings.invoker != 'sphinx-build':
        with open(os.path.join(os.path.dirname(__file__), 'email_threat_audio.html')) as file:
            threat_audio = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email_threat_image.html')) as file:
            threat_image = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email_threat_image_audio.html')) as file:
            threat_image_audio = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email_stock_alert.html')) as file:
            stock_alert = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email_OTP.html')) as file:
            one_time_passcode = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email.html')) as file:
            notification = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'car_report.html')) as file:
            car_report = file.read()


class EndpointTemplates:
    """HTML templates used for hosting endpoints.

    >>> EndpointTemplates

    """

    if models.settings.invoker != 'sphinx-build':
        with open(os.path.join(os.path.dirname(__file__), 'robinhood.html')) as file:
            robinhood = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'surveillance.html')) as file:
            surveillance = file.read()


class GenericTemplates:
    """HTML templates used for generic purposes.

    >>> GenericTemplates

    """

    if models.settings.invoker != 'sphinx-build':
        with open(os.path.join(os.path.dirname(__file__), 'win_wifi_config.xml')) as file:
            win_wifi_xml = file.read()


email = EmailTemplates
generic = GenericTemplates
endpoint = EndpointTemplates
