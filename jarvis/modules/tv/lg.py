# noinspection PyUnresolvedReferences
"""Module for LG tv operations.

>>> LG

"""

import socket
import time
from collections.abc import Generator
from typing import List, NoReturn

from playsound import playsound
from pywebostv.connection import WebOSClient
from pywebostv.controls import (ApplicationControl, AudioOutputSource,
                                MediaControl, SourceControl, SystemControl)

from jarvis.modules.exceptions import TVError
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import shared, util


class LGWebOS:
    """Wrapper for ``LGWebOS`` TVs.

    >>> LGWebOS

    """

    _init_status = False
    _reconnect = False

    def __init__(self, ip_address: str, client_key: str):
        """Instantiates the ``WebOSClient`` and connects to the TV.

        Using TV's ip makes the initial response much quicker, but it can also scan the network for the TV's ip.

        Args:
            ip_address: IP address of the TV.
            client_key: Client Key to authenticate connection.

        Raises:
            TVError:
            - If unable to connect to the TV.
            - If no TV was found in the IP range.
            - If a connection timeout occurs (usually because of unstable internet or multiple connection types)
        """
        store = {'client_key': client_key} if client_key else {}

        try:
            self.client = WebOSClient(ip_address)
            self.client.connect()
        except (socket.gaierror, ConnectionRefusedError) as error:
            logger.error(error)
            self._reconnect = True
            if not shared.called_by_offline:
                playsound(sound=models.indicators.tv_scan, block=False)
            if discovered := WebOSClient.discover():
                self.client = discovered[0]
                try:
                    self.client.connect()
                except (TimeoutError, BrokenPipeError) as error:
                    logger.error(error)
                    raise TVError
            else:
                raise TVError
        except (TimeoutError, BrokenPipeError) as error:
            logger.error(error)
            raise TVError

        for status in self.client.register(store):
            if status == WebOSClient.REGISTERED and not self._init_status:
                util.write_screen(text='Connected to the TV.')
                break
            elif status == WebOSClient.PROMPTED:
                playsound(sound=models.indicators.tv_connect, block=False)
                self._reconnect = True
                util.write_screen(text='Please accept the connection request on your TV.')

        if self._reconnect:
            self._reconnect = False
            logger.critical("ATTENTION::Client key has been generated. Store it in '%s' to re-use." %
                            models.fileio.smart_devices)
            logger.critical(str(store))

        self.system = SystemControl(self.client)
        self.system.notify("Jarvis is controlling the TV now.") if not self._init_status else None
        self.media = MediaControl(self.client)
        self.app = ApplicationControl(self.client)
        self.source_control = SourceControl(self.client)
        self._init_status = True

    def increase_volume(self) -> NoReturn:
        """Increases the volume by ``10`` units."""
        for _ in range(10):
            self.media.volume_up()
        self.system.notify(f"Jarvis::Increased Volume: {self.media.get_volume()['volume']}%")

    def decrease_volume(self) -> NoReturn:
        """Decreases the volume by ``10`` units."""
        for _ in range(10):
            self.media.volume_down()
        self.system.notify(f"Jarvis::Decreased Volume: {self.media.get_volume()['volume']}%")

    def get_volume(self) -> int:
        """Get volume status.

        Returns:
            int:
            Volume level.
        """
        self.system.notify(f"Jarvis::Current Volume: {self.media.get_volume()['volume']}%")
        return self.media.get_volume()['volume']

    def set_volume(self, target: int) -> NoReturn:
        """The argument is an integer from 1 to 100.

        Args:
            target: Takes an integer as argument to set the volume.
        """
        self.system.notify(f"Jarvis::Volume has been set to: {self.media.get_volume()['volume']}%")
        self.media.set_volume(target)

    def mute(self) -> NoReturn:
        """Mutes the TV."""
        self.system.notify("Jarvis::Muted")
        self.media.mute(True)

    def play(self) -> NoReturn:
        """Plays the paused content on the TV."""
        self.system.notify("Jarvis::Play")
        self.media.play()

    def pause(self) -> NoReturn:
        """Pauses the playing content on TV."""
        self.system.notify("Jarvis::Paused")
        self.media.pause()

    def stop(self) -> NoReturn:
        """Stop the playing content on TV."""
        self.system.notify("Jarvis::Stop")
        self.media.stop()

    def rewind(self) -> NoReturn:
        """Rewinds the playing content on TV."""
        self.system.notify("Jarvis::Rewind")
        self.media.rewind()

    def forward(self) -> NoReturn:
        """Forwards the playing content on TV."""
        self.system.notify("Jarvis::Forward")
        self.media.fast_forward()

    def get_apps(self) -> Generator[str]:
        """Checks the applications installed on the TV.

        Yields:
            str:
            Yields available apps on the TV.
        """
        for app in self.app.list_apps():
            yield app["title"]

    def launch_app(self, app_name: str) -> NoReturn:
        """Launches an application.

        Args:
            app_name: Takes the application name as argument.
        """
        app_launcher = [x for x in self.app.list_apps() if app_name.lower() in x["title"].lower()][0]
        self.app.launch(app_launcher, content_id=None)

    def close_app(self, app_name: str) -> NoReturn:
        """Closes a particular app using the launch_info received from launch_app method.

        Args:
            app_name: Application name that has to be closed.
        """
        self.app.close(self.launch_app(app_name))

    def get_sources(self) -> Generator[str]:
        """Checks for the input sources on the TV.

        Yields:
            str:
            Yields ``InputSource`` instance.
        """
        for source in self.source_control.list_sources():
            yield source['label']

    def set_source(self, val: str) -> NoReturn:
        """Sets an ``InputSource`` instance.

        Args:
            val: Takes the input source instance value as argument.
        """
        sources = self.source_control.list_sources()
        index = list(self.get_sources()).index(val)
        self.source_control.set_source(sources[index])

    def current_app(self) -> str:
        """Scans the current application running in foreground.

        Returns:
            str:
            Title of the current app that is running
        """
        app_id = self.app.get_current()
        return [x for x in self.app.list_apps() if app_id == x["id"]][0]['title']

    def audio_output(self) -> AudioOutputSource:
        """Returns the currently used audio output source as AudioOutputSource instance."""
        return self.media.get_audio_output()

    def audio_output_source(self) -> List[AudioOutputSource]:
        """Checks the list of audio output sources available.

        Returns:
            list:
            List of ``AudioOutputSource`` instances.
        """
        return self.media.list_audio_output_sources()

    def set_audio_output_source(self) -> NoReturn:
        """Sets to a particular AudioOutputSource instance."""
        self.media.set_audio_output(self.audio_output_source[0])  # noqa

    def shutdown(self) -> NoReturn:
        """Notifies the TV about shutdown and shuts down after 3 seconds."""
        self.system.notify('Jarvis::SHUTTING DOWN now')
        time.sleep(3)
        self.system.power_off()
