import os

from jarvis.modules.models import models


class EmailTemplates:
    """HTML templates used to send outbound email.

    >>> EmailTemplates

    """

    if models.settings.bot != 'sphinx-build':
        _threat_audio = os.path.join(os.path.dirname(__file__), 'email_threat_audio.html')
        with open(_threat_audio) as file:
            threat_audio = file.read()

        _threat_no_audio = os.path.join(os.path.dirname(__file__), 'email_threat_no_audio.html')
        with open(_threat_no_audio) as file:
            threat_no_audio = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email_stock_alert.html')) as file:
            stock_alert = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email_OTP.html')) as file:
            one_time_passcode = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'stock_monitor_OTP.html')) as file:
            stock_monitor_otp = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'email.html')) as file:
            notification = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'car_report.html')) as file:
            car_report = file.read()


class OriginTemplates:
    """HTML templates used for hosting endpoints.

    >>> OriginTemplates

    """

    if models.settings.bot != 'sphinx-build':
        with open(os.path.join(os.path.dirname(__file__), 'robinhood.html')) as file:
            robinhood = file.read()

        with open(os.path.join(os.path.dirname(__file__), 'surveillance.html')) as file:
            surveillance = file.read()


class GenericTemplates:
    """HTML templates used for generic purposes.

    >>> GenericTemplates

    """

    if models.settings.bot != 'sphinx-build':
        with open(os.path.join(os.path.dirname(__file__), 'win_wifi_config.xml')) as file:
            win_wifi_xml = file.read()


email = EmailTemplates
origin = OriginTemplates
generic = GenericTemplates
