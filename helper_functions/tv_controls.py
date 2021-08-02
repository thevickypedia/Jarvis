from socket import gaierror
from sys import stdout
from threading import Thread
from time import sleep

from dotenv import set_key
from playsound import playsound
from pywebostv.connection import WebOSClient
from pywebostv.controls import (ApplicationControl, MediaControl,
                                SourceControl, SystemControl)

from helper_functions.logger import logger


class TV:
    """All the TV controls wrapped in individual functions.

    >>> TV

    """

    _init_status = False
    reconnect = False

    def __init__(self, ip_address: str = None, client_key: str = None):
        """Client key will be logged and stored as SSM param when you accept the connection for the first time.

        Store the dict value as an env variable and use it as below. Using TV's ip makes the initial
        response much quicker but it looks for the TV's ip if an ip is not found.

        Args:
            ip_address: IP address of the TV.
            client_key: Client Key to authenticate connection.
        """
        store = {'client_key': client_key} if client_key else {}

        try:
            self.client = WebOSClient(ip_address)
            self.client.connect()
        except (gaierror, ConnectionRefusedError, ConnectionResetError):  # when IP or client key is None or incorrect
            self.reconnect = True
            Thread(target=playsound, args=['indicators/tv_scan.mp3']).start()
            stdout.write("\rThe TV's IP has either changed or unreachable. Scanning your IP range.")
            self.client = WebOSClient.discover()[0]
            self.client.connect()
        except (TimeoutError, BrokenPipeError):
            logger.error('\rOperation timed out. The TV might be turned off.')

        for status in self.client.register(store):
            if status == WebOSClient.REGISTERED and not self._init_status:
                stdout.write('\rConnected to the TV.')
            elif status == WebOSClient.PROMPTED:
                Thread(target=playsound, args=['indicators/tv_connect.mp3']).start()
                self.reconnect = True
                stdout.write('\rPlease accept the connection request on your TV.')

        if self.reconnect:
            self.reconnect = False
            set_key(dotenv_path='.env', key_to_set='tv_client_key', value_to_set=store.get('client_key'))

        self.system = SystemControl(self.client)
        self.system.notify("Jarvis is controlling the TV now.") if not self._init_status else None
        self.media = MediaControl(self.client)
        self.app = ApplicationControl(self.client)
        self.source_control = SourceControl(self.client)
        self._init_status = True

    def increase_volume(self) -> None:
        """Increases the volume by 10 units."""
        for _ in range(10):
            self.media.volume_up()
        self.system.notify(f"Jarvis::Increased Volume: {self.media.get_volume()['volume']}%")

    def decrease_volume(self) -> None:
        """Decreases the volume by 10 units. Doesn't return anything."""
        for _ in range(10):
            self.media.volume_down()
        self.system.notify(f"Jarvis::Decreased Volume: {self.media.get_volume()['volume']}%")

    def get_volume(self) -> dict:
        """Get volume status.

        Returns:
            dict:
            {
            'scenario': 'mastervolume_tv_speaker',
            'volume': 9,
            'muted': False
            }

        """
        self.system.notify(f"Jarvis::Current Volume: {self.media.get_volume()['volume']}%")
        return self.media.get_volume()['volume']

    def set_volume(self, target: int) -> None:
        """The argument is an integer from 1 to 100.

        Args:
            target: Takes an integer as argument to set the volume.

        """
        self.media.set_volume(target)
        self.system.notify(f"Jarvis::Volume has been set to: {self.media.get_volume()['volume']}%")

    def mute(self) -> None:
        """Mutes the TV.

        status=True mutes the TV. status=False un-mutes it.
        """
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

    def list_apps(self) -> list:
        """Checks the applications installed on the TV.

        Returns:
            list:
            List of available apps on the TV.

        """
        apps = self.app.list_apps()
        app_list = [app["title"] for app in apps]
        return app_list

    def launch_app(self, app_name: str) -> dict:
        """Launches an application.

        Args:
            app_name: Takes the application name as argument.

        Returns:
            dict:
            Makes call to the launch module and returns a dictionary of appId and sessionId.

        """
        app_launcher = [x for x in self.app.list_apps() if app_name.lower() in x["title"].lower()][0]
        return self.app.launch(app_launcher, content_id=None)

    def close_app(self, app_name: str) -> None:
        """Closes a particular app using the launch_info received from launch_app method."""
        self.app.close(self.launch_app(app_name))

    def source(self) -> list:
        """Checks for the input sources on the TV.

        Returns:
            list:
            List of InputSource instances.

        """
        sources = self.source_control.list_sources()
        sources_list = [source['label'] for source in sources]
        return sources_list

    def set_source(self, val: str) -> list:
        """Sets an InputSource instance.

        Args:
            val: Takes the input source instance value as argument.

        Returns:
            list:
            List of sources.

        """
        sources = self.source_control.list_sources()
        index = self.source().index(val)
        self.source_control.set_source(sources[index])
        return sources

    def current_app(self) -> str:
        """Scans the current application running in foreground.

        Returns:
            str:
            Title of te current app that is running

        """
        app_id = self.app.get_current()  # Returns the application ID (string) of the
        foreground_app = [x for x in self.app.list_apps() if app_id == x["id"]][0]
        return foreground_app['title']

    def audio_output(self) -> None:
        """Writes the currently used audio output source as AudioOutputSource instance on the screen."""
        media_output_source = self.media.get_audio_output()
        stdout.write(f'{media_output_source}')

    def audio_output_source(self) -> list:
        """Checks the list of audio output sources available.

        Returns:
            list:
            List of AudioOutputSource instances.

        """
        audio_outputs = self.media.list_audio_output_sources()
        stdout.write(f'{audio_outputs}')
        return audio_outputs

    def set_audio_output_source(self) -> None:
        """Sets to a particular AudioOutputSource instance."""
        # noinspection PyUnresolvedReferences
        self.media.set_audio_output(self.audio_output_source[0])

    def shutdown(self) -> None:
        """Notifies the TV about shutdown and shuts down after 3 seconds."""
        self.system.notify('Jarvis::SHUTTING DOWN now')
        sleep(3)
        self.system.power_off()
