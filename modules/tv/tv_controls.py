import os
import socket
import sys
import time

from dotenv import set_key
from playsound import playsound
from pywebostv.connection import WebOSClient
from pywebostv.controls import (ApplicationControl, MediaControl,
                                SourceControl, SystemControl)

from executors.logger import logger
from modules.exceptions import TVError
from modules.models import models
from modules.utils import shared

env = models.env
indicators = models.Indicators()


class TV:
    """All the TV controls wrapped in dedicated methods.

    >>> TV

    """

    _init_status = False
    reconnect = False

    def __init__(self, ip_address: str = None, client_key: str = None):
        """Client key will be logged and stored as SSM param when you accept the connection for the first time.

        Store the dict value as an env variable and use it as below. Using TV's ip makes the initial
        response much quicker, but it also scans the network for the TV's ip if ip arg is not received.

        Args:
            ip_address: IP address of the TV.
            client_key: Client Key to authenticate connection.
        """
        store = {'client_key': client_key} if client_key else {}

        try:
            self.client = WebOSClient(ip_address)
            self.client.connect()
        except (socket.gaierror, ConnectionRefusedError) as error:
            logger.error(error)
            self.reconnect = True
            if not shared.called_by_offline:
                playsound(sound=indicators.tv_scan, block=False)
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
                sys.stdout.write('\rConnected to the TV.')
                break
            elif status == WebOSClient.PROMPTED:
                playsound(sound=indicators.tv_connect, block=False)
                self.reconnect = True
                sys.stdout.write('\rPlease accept the connection request on your TV.')

        if self.reconnect:
            self.reconnect = False
            if os.path.isfile('.env') and env.tv_client_key != store.get('client_key'):
                set_key(dotenv_path='.env', key_to_set='TV_CLIENT_KEY', value_to_set=store.get('client_key'))
            else:
                logger.critical('Client key has been generated. Store it in env vars to re-use.')
                logger.critical(f"TV_CLIENT_KEY: {store.get('client_key')}")

        self.system = SystemControl(self.client)
        self.system.notify("Jarvis is controlling the TV now.") if not self._init_status else None
        self.media = MediaControl(self.client)
        self.app = ApplicationControl(self.client)
        self.source_control = SourceControl(self.client)
        self._init_status = True

    def increase_volume(self) -> None:
        """Increases the volume by ``10`` units."""
        for _ in range(10):
            self.media.volume_up()
        self.system.notify(f"Jarvis::Increased Volume: {self.media.get_volume()['volume']}%")

    def decrease_volume(self) -> None:
        """Decreases the volume by ``10`` units."""
        for _ in range(10):
            self.media.volume_down()
        self.system.notify(f"Jarvis::Decreased Volume: {self.media.get_volume()['volume']}%")

    def get_volume(self) -> dict:
        """Get volume status.

        Returns:
            dict:
            A dictionary with key value pairs of scenario, volume and mute status.
        """
        self.system.notify(f"Jarvis::Current Volume: {self.media.get_volume()['volume']}%")
        return self.media.get_volume()['volume']

    def set_volume(self, target: int) -> None:
        """The argument is an integer from 1 to 100.

        Args:
            target: Takes an integer as argument to set the volume.
        """
        self.system.notify(f"Jarvis::Volume has been set to: {self.media.get_volume()['volume']}%")
        self.media.set_volume(target)

    def mute(self) -> None:
        """Mutes the TV."""
        self.system.notify("Jarvis::Muted")
        self.media.mute(True)

    def play(self) -> None:
        """Plays the paused content on the TV."""
        self.system.notify("Jarvis::Play")
        self.media.play()

    def pause(self) -> None:
        """Pauses the playing content on TV."""
        self.system.notify("Jarvis::Paused")
        self.media.pause()

    def stop(self) -> None:
        """Stop the playing content on TV."""
        self.system.notify("Jarvis::Stop")
        self.media.stop()

    def rewind(self) -> None:
        """Rewinds the playing content on TV."""
        self.system.notify("Jarvis::Rewind")
        self.media.rewind()

    def forward(self) -> None:
        """Forwards the playing content on TV."""
        self.system.notify("Jarvis::Forward")
        self.media.fast_forward()

    def get_apps(self) -> list:
        """Checks the applications installed on the TV.

        Returns:
            list:
            List of available apps on the TV.
        """
        return [app["title"] for app in self.app.list_apps()]

    def launch_app(self, app_name: str) -> None:
        """Launches an application.

        Args:
            app_name: Takes the application name as argument.
        """
        app_launcher = [x for x in self.app.list_apps() if app_name.lower() in x["title"].lower()][0]
        self.app.launch(app_launcher, content_id=None)

    def close_app(self, app_name: str) -> None:
        """Closes a particular app using the launch_info received from launch_app method.

        Args:
            app_name: Application name that has to be closed.
        """
        self.app.close(self.launch_app(app_name))

    def get_sources(self) -> list:
        """Checks for the input sources on the TV.

        Returns:
            list:
            List of ``InputSource`` instances.
        """
        return [source['label'] for source in self.source_control.list_sources()]

    def set_source(self, val: str) -> None:
        """Sets an ``InputSource`` instance.

        Args:
            val: Takes the input source instance value as argument.
        """
        sources = self.source_control.list_sources()
        index = self.get_sources().index(val)
        self.source_control.set_source(sources[index])

    def current_app(self) -> str:
        """Scans the current application running in foreground.

        Returns:
            str:
            Title of the current app that is running
        """
        app_id = self.app.get_current()
        return [x for x in self.app.list_apps() if app_id == x["id"]][0]['title']

    def audio_output(self) -> None:
        """Writes the currently used audio output source as AudioOutputSource instance on the screen."""
        media_output_source = self.media.get_audio_output()
        sys.stdout.write(f'{media_output_source}')

    def audio_output_source(self) -> list:
        """Checks the list of audio output sources available.

        Returns:
            list:
            List of ``AudioOutputSource`` instances.
        """
        audio_outputs = self.media.list_audio_output_sources()
        sys.stdout.write(f'{audio_outputs}')
        return audio_outputs

    def set_audio_output_source(self) -> None:
        """Sets to a particular AudioOutputSource instance."""
        self.media.set_audio_output(self.audio_output_source[0])  # noqa

    def shutdown(self) -> None:
        """Notifies the TV about shutdown and shuts down after 3 seconds."""
        self.system.notify('Jarvis::SHUTTING DOWN now')
        time.sleep(3)
        self.system.power_off()
