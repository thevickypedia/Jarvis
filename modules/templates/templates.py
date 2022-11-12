import os

from modules.models import models


class EmailTemplates:
    """HTML templates used to send outbound email.

    >>> EmailTemplates

    """

    if models.settings.bot != 'sphinx-build':
        _threat_audio = os.path.join(models.fileio.templates, 'email_threat_audio.html')
        with open(_threat_audio) as file:
            threat_audio = file.read()

        _threat_no_audio = os.path.join(models.fileio.templates, 'email_threat_no_audio.html')
        with open(_threat_no_audio) as file:
            threat_no_audio = file.read()

        with open(os.path.join(models.fileio.templates, 'email_stock_alert.html')) as file:
            stock_alert = file.read()

        with open(os.path.join(models.fileio.templates, 'email_OTP.html')) as file:
            one_time_passcode = file.read()


class OriginTemplates:
    """HTML templates used for hosting endpoints.

    >>> OriginTemplates

    """

    if models.settings.bot != 'sphinx-build':
        with open(os.path.join(models.fileio.templates, 'robinhood.html')) as file:
            robinhood = file.read().strip()

        with open(os.path.join(models.fileio.templates, 'surveillance.html')) as file:
            surveillance = file.read()
