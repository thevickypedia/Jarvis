from socket import gaierror
from sys import stdout
from time import sleep

from pywebostv.connection import WebOSClient
from pywebostv.controls import (ApplicationControl, MediaControl,
                                SourceControl, SystemControl)

from helper_functions.logger import logger
from helper_functions.put_param import AWSClient


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
        store = {'client_key': client_key}

        try:
            self.client = WebOSClient(ip_address)
            self.client.connect()
        except (gaierror, ConnectionRefusedError):  # this is reached only when the IP address is None or incorrect
            self.reconnect = True
            stdout.write("\rThe TV's IP has either changed or unreachable. Scanning your IP range..")
            self.client = WebOSClient.discover()[0]
            self.client.connect()
        except (TimeoutError, BrokenPipeError):
            logger.error('\rOperation timed out. The TV might be turned off.')

        for status in self.client.register(store):
            if status == WebOSClient.REGISTERED and not self._init_status:
                stdout.write('\rConnected to the TV.')
            elif status == WebOSClient.PROMPTED:
                self.reconnect = True
                from playsound import playsound
                stdout.write('\rPlease accept the connection request on your TV.')
                playsound('mp3/tv_connect.mp3')

        if self.reconnect:
            self.reconnect = False
            AWSClient().put_parameters(name='/Jarvis/tv_client_key', value=store.get('client_key'))
            logger.warning(f'Store client key as ENV-VAR:\n{store}')  # store client_key as local env var

        self.system = SystemControl(self.client)
        self.system.notify("Jarvis is controlling the TV now.") if not self._init_status else None
        self.media = MediaControl(self.client)
        self.app = ApplicationControl(self.client)
        self.source_control = SourceControl(self.client)
        self._init_status = True

    def increase_volume(self):
        """Increases the volume by 10 units."""
        for _ in range(10):
            self.media.volume_up()
        self.system.notify(f"Jarvis::Increased Volume: {self.media.get_volume()['volume']}%")

    def decrease_volume(self):
        """Decreases the volume by 10 units. Doesn't return anything."""
        for _ in range(10):
            self.media.volume_down()
        self.system.notify(f"Jarvis::Decreased Volume: {self.media.get_volume()['volume']}%")

    def get_volume(self):
        """Get volume status.

        Returns: {'scenario': 'mastervolume_tv_speaker', 'volume': 9, 'muted': False}

        """
        self.system.notify(f"Jarvis::Current Volume: {self.media.get_volume()['volume']}%")
        return self.media.get_volume()['volume']

    def set_volume(self, target: int):
        """The argument is an integer from 1 to 100.

        Args:
            target: Takes an integer as argument to set the volume.

        """
        self.media.set_volume(target)
        self.system.notify(f"Jarvis::Volume has been set to: {self.media.get_volume()['volume']}%")

    def mute(self):
        """Mutes the TV.

        status=True mutes the TV. status=False un-mutes it.
        """
        self.system.notify("Jarvis::Muted")
        self.media.mute(True)

    def play(self):
        """Plays the paused content on the TV."""
        self.system.notify("Jarvis::Play")
        self.media.play()

    def pause(self):
        """Pauses the playing content on TV."""
        self.system.notify("Jarvis::Paused")
        self.media.pause()

    def stop(self):
        """Stop the playing content on TV."""
        self.system.notify("Jarvis::Stop")
        self.media.stop()

    def rewind(self):
        """Rewinds the playing content on TV."""
        self.system.notify("Jarvis::Rewind")
        self.media.rewind()

    def forward(self):
        """Forwards the playing content on TV."""
        self.system.notify("Jarvis::Forward")
        self.media.fast_forward()

    def audio_output(self):
        """Writes the currently used audio output source as AudioOutputSource instance on the screen."""
        media_output_source = self.media.get_audio_output()
        stdout.write(f'{media_output_source}')

    def audio_output_source(self):
        """Checks the list of audio output sources available.

        Returns: List of AudioOutputSource instances.

        """
        audio_outputs = self.media.list_audio_output_sources()
        stdout.write(f'{audio_outputs}')
        return audio_outputs

    def set_audio_output_source(self):
        """Sets to a particular AudioOutputSource instance."""
        # noinspection PyUnresolvedReferences
        self.media.set_audio_output(self.audio_output_source[0])

    def list_apps(self):
        """Checks the applications installed on the TV.

        Returns: List of available apps on the TV.

        """
        apps = self.app.list_apps()
        app_list = [app["title"] for app in apps]
        return app_list

    def launch_app(self, app_name: str):
        """Launches an application.

        Args:
            app_name: Takes the application name as argument.

        Returns: A call to the launch module.

        """
        app_launcher = [x for x in self.app.list_apps() if app_name.lower() in x["title"].lower()][0]
        return self.app.launch(app_launcher, content_id=None)

    def close_app(self, app_name: str):
        """Closes a particular app using the launch_info received from launch_app method."""
        self.app.close(TV().launch_app(app_name))

    def source(self):
        """Checks for the input sources on the TV.

        Returns: List of InputSource instances.

        """
        sources = self.source_control.list_sources()
        sources_list = [source['label'] for source in sources]
        return sources_list

    def set_source(self, val: str):
        """Sets an InputSource instance.

        Args:
            val: Takes the input source instance value as argument.

        Returns: List of sources.

        """
        sources = self.source_control.list_sources()
        index = TV().source().index(val)
        self.source_control.set_source(sources[index])
        return sources

    def current_app(self):
        """Scans the current application running in foreground.

        Returns: Title of te current app that is running

        """
        app_id = self.app.get_current()  # Returns the application ID (string) of the
        foreground_app = [x for x in self.app.list_apps() if app_id == x["id"]][0]
        return foreground_app['title']

    def shutdown(self):
        """Notifies the TV about shutdown and shuts down after 3 seconds."""
        self.system.notify('Jarvis::SHUTTING DOWN now')
        sleep(3)
        self.system.power_off()
