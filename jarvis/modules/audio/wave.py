from threading import Thread

import requests
from playsound import playsound
from pydantic import PositiveFloat, PositiveInt

from jarvis.api.routers import routes
from jarvis.modules.auth_bearer import BearerAuth
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, support


class Spectrum:
    """Spectrum class to handle listener spectrum activation and deactivation.

    >>> Spectrum

    """

    SESSION = requests.Session()
    SESSION.auth = BearerAuth(token=models.env.listener_spectrum_key)
    BASE_PATH = f"http://{models.env.offline_host}:{models.env.offline_port}"
    ACTIVATE = BASE_PATH + routes.APIPath.listener_spectrum_wave.format(command="start")
    DEACTIVATE = BASE_PATH + routes.APIPath.listener_spectrum_wave.format(
        command="stop"
    )

    def make_request(self, url: str) -> None:
        """Make a request to the given URL with the session.

        Args:
            url: The URL to make the request to.
        """
        try:
            response = self.SESSION.post(url=url, timeout=2)
            response.raise_for_status()
            assert response.ok, f"[{response.status_code}]: {response.text}"
        except (*EgressErrors, AssertionError) as error:
            logger.error(f"Error making request to {url}: {error}")

    def activate(
        self,
        sound: bool,
        timeout: PositiveInt | PositiveFloat,
        phrase_time_limit: PositiveInt | PositiveFloat,
    ) -> None:
        """Activate the listener spectrum by making a request to the activate URL.

        Args:
            sound: Flag whether to play the listener indicator sound. Defaults to True unless set to False.
            timeout: Custom timeout for functions expecting a longer wait time.
            phrase_time_limit: Custom time limit for functions expecting a longer user input.
        """
        if models.env.listener_spectrum_key and not shared.called_by_offline:
            Thread(target=self.make_request, args=(self.ACTIVATE,), daemon=True).start()
        if sound:
            playsound(sound=models.indicators.start, block=False)
        support.write_screen(
            text=f"Listener activated [{timeout}: {phrase_time_limit}]"
        )

    def deactivate(self, sound: bool) -> None:
        """Deactivate the listener spectrum by making a request to the deactivate URL.

        Args:
            sound: Flag whether to play the listener indicator sound. Defaults to True unless set to False.
        """
        if models.env.listener_spectrum_key and not shared.called_by_offline:
            Thread(
                target=self.make_request, args=(self.DEACTIVATE,), daemon=True
            ).start()
        if sound:
            playsound(sound=models.indicators.end, block=False)
        support.flush_screen()
