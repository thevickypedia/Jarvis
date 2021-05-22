from socket import gaierror
from sys import stdout
from time import sleep

from pywebostv.connection import WebOSClient
from pywebostv.controls import SystemControl, MediaControl, ApplicationControl, SourceControl

from helper_functions.logger import logger
from helper_functions.put_param import put_parameters


class TV:
    """All the TV controls wrapped in individual functions."""
    _init_status = False
    reconnect = False

    def __init__(self, ip_address=None, client_key=None):
        """Client key will be logged and stored as SSM param when you accept the connection for the first time.
        Store the dict value as an env variable and use it as below. Using TV's ip makes the initial
        response much quicker but it looks for the TV's ip if an ip is not found."""

        store = {'client_key': client_key}

        try:
            self.client = WebOSClient(ip_address)
            self.client.connect()
        except (gaierror, ConnectionRefusedError):  # this is reached only when the IP address is None or incorrect
            TV.reconnect = True
            stdout.write(f"\rThe TV's IP has either changed or unreachable. Scanning your IP range..")
            self.client = WebOSClient.discover()[0]
            self.client.connect()
        except (TimeoutError, BrokenPipeError):
            logger.error('\rOperation timed out. The TV might be turned off.')

        for status in self.client.register(store):
            if status == WebOSClient.REGISTERED and not TV._init_status:
                stdout.write('\rConnected to the TV.')
            elif status == WebOSClient.PROMPTED:
                TV.reconnect = True
                from playsound import playsound
                stdout.write('\rPlease accept the connection request on your TV.')
                playsound('mp3/tv_connect.mp3')

        if TV.reconnect:
            TV.reconnect = False
            put_parameters(name='/Jarvis/tv_client_key', value=store.get('client_key'))
            logger.warning(f'Store client key as ENV-VAR:\n{store}')  # store client_key as local env var

        self.system = SystemControl(self.client)
        self.system.notify("Jarvis is controlling the TV now.") if not TV._init_status else None
        self.media = MediaControl(self.client)
        self.app = ApplicationControl(self.client)
        self.source_control = SourceControl(self.client)
        TV._init_status = True

    def increase_volume(self):
        """Increases the volume by 10 units. Doesn't return anything"""
        for _ in range(10):
            self.media.volume_up()
        self.system.notify(f"Jarvis::Increased Volume: {self.media.get_volume()['volume']}%")

    def decrease_volume(self):
        """Decreases the volume by 10 units. Doesn't return anything"""
        for _ in range(10):
            self.media.volume_down()
        self.system.notify(f"Jarvis::Decreased Volume: {self.media.get_volume()['volume']}%")

    def get_volume(self):
        """Get volume status. Returns: {'scenario': 'mastervolume_tv_speaker', 'volume': 9, 'muted': False}"""
        self.system.notify(f"Jarvis::Current Volume: {self.media.get_volume()['volume']}%")
        return self.media.get_volume()['volume']

    def set_volume(self, target):
        """The argument is an integer from 1 to 100. Doesn't return anything."""
        self.media.set_volume(target)
        self.system.notify(f"Jarvis::Volume has been set to: {self.media.get_volume()['volume']}%")

    def mute(self):
        """status=True mutes the TV. status=False un-mutes it."""
        self.system.notify(f"Jarvis::Muted")
        self.media.mute(True)

    def play(self):
        self.system.notify(f"Jarvis::Play")
        self.media.play()

    def pause(self):
        self.system.notify(f"Jarvis::Paused")
        self.media.pause()

    def stop(self):
        self.system.notify(f"Jarvis::Stop")
        self.media.stop()

    def rewind(self):
        self.system.notify(f"Jarvis::Rewind")
        self.media.rewind()

    def forward(self):
        self.system.notify(f"Jarvis::Forward")
        self.media.fast_forward()

    def audio_output(self):
        """Returns the currently used audio output source as AudioOutputSource instance"""
        media_output_source = self.media.get_audio_output()
        stdout.write(f'{media_output_source}')

    def audio_output_source(self):
        """Returns a list of AudioOutputSource instances"""
        audio_outputs = self.media.list_audio_output_sources()
        stdout.write(f'{audio_outputs}')
        return audio_outputs

    def set_audio_output_source(self):
        """AudioOutputSource instance"""
        # noinspection PyUnresolvedReferences
        self.media.set_audio_output(audio_output_source[0])

    def list_apps(self):
        """Returns the list of available apps on the TV"""
        apps = self.app.list_apps()
        app_list = [app["title"] for app in apps]
        return app_list

    def launch_app(self, app_name):
        """launches an application"""
        app_launcher = [x for x in self.app.list_apps() if app_name.lower() in x["title"].lower()][0]
        return self.app.launch(app_launcher, content_id=None)

    def close_app(self, app_name):
        """closes a particular app using the launch_info received from launch_app()"""
        self.app.close(TV().launch_app(app_name))

    def source(self):
        """Returns a list of InputSource instances"""
        sources = self.source_control.list_sources()
        sources_list = [source['label'] for source in sources]
        return sources_list

    def set_source(self, val):
        """Accepts an InputSource instance"""
        sources = self.source_control.list_sources()
        index = TV().source().index(val)
        self.source_control.set_source(sources[index])
        return sources

    def current_app(self):
        """Returns the title of te current app that is running"""
        app_id = self.app.get_current()  # Returns the application ID (string) of the
        foreground_app = [x for x in self.app.list_apps() if app_id == x["id"]][0]
        return foreground_app['title']

    def shutdown(self):
        """Notifies the TV about shutdown and shuts down after 3 seconds"""
        self.system.notify(f'Jarvis::SHUTTING DOWN now')
        sleep(3)
        self.system.power_off()
