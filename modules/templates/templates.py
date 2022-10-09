import os

from modules.models import models


class RobinhoodTemplate:
    """Initiates Template object to load the robinhood report template.

    >>> RobinhoodTemplate

    """

    if models.settings.bot != 'sphinx-build':
        _source = os.path.join(models.fileio.templates, 'robinhood.html')
        with open(_source) as file:
            source = file.read().strip()


class ThreatNotificationTemplates:
    """Initiates Template object to load the threat email templates.

    >>> ThreatNotificationTemplates

    """

    if models.settings.bot != 'sphinx-build':
        _threat_audio = os.path.join(models.fileio.templates, 'threat_audio.html')
        with open(_threat_audio) as file:
            threat_audio = file.read()

        _threat_no_audio = os.path.join(models.fileio.templates, 'threat_no_audio.html')
        with open(_threat_no_audio) as file:
            threat_no_audio = file.read()
