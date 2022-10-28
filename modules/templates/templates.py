import os

from modules.models import models


class RobinhoodTemplate:
    """Initiates ``RobinhoodTemplate`` object to load the robinhood report template.

    >>> RobinhoodTemplate

    """

    if models.settings.bot != 'sphinx-build':
        _source = os.path.join(models.fileio.templates, 'robinhood.html')
        with open(_source) as file:
            source = file.read().strip()


class ThreatNotificationTemplates:
    """Initiates ``ThreatNotificationTemplates`` object to load the threat email templates.

    >>> ThreatNotificationTemplates

    """

    if models.settings.bot != 'sphinx-build':
        _threat_audio = os.path.join(models.fileio.templates, 'threat_audio.html')
        with open(_threat_audio) as file:
            threat_audio = file.read()

        _threat_no_audio = os.path.join(models.fileio.templates, 'threat_no_audio.html')
        with open(_threat_no_audio) as file:
            threat_no_audio = file.read()


class Surveillance:
    """Initiates ``Surveillance`` object to load the video surveilance template.

    >>> Surveillance

    """

    if models.settings.bot != 'sphinx-build':
        with open(os.path.join(models.fileio.templates, 'surveillance.html')) as file:
            source = file.read()


class StockMonitor:
    """Initiates ``StockMonitor`` object to load the stock-monitor email template.

    >>> Surveillance

    """

    if models.settings.bot != 'sphinx-build':
        with open(os.path.join(models.fileio.templates, 'stock_monitor.html')) as file:
            source = file.read()
