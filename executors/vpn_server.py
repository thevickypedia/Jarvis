import os
from multiprocessing import Process
from threading import Thread

from vpn.controller import VPNServer

from modules.audio import speaker
from modules.models import models
from modules.utils import shared, support

env = models.env


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if status := shared.active_vpn:
        speaker.speak(
            text=f'VPN Server was recently {status}, and the process is still running {env.title}! '
                 'Please wait and retry.')
        return

    phrase = phrase.lower()
    if 'start' in phrase or 'trigger' in phrase or 'initiate' in phrase or 'enable' in phrase or 'spin up' in phrase:
        Process(target=vpn_server_switch, kwargs={'operation': 'START'}).start()
        speaker.speak(text=f'VPN Server has been initiated {env.title}! Login details will be sent to you shortly.')
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        if not os.path.isfile('vpn_info.json'):
            speaker.speak(text=f'Input file for VPN Server is missing {env.title}! '
                               'The VPN Server might have been shut down already.')
            return
        Process(target=vpn_server_switch, kwargs={'operation': 'STOP'}).start()
        speaker.speak(text=f'VPN Server will be shutdown {env.title}!')
    else:
        speaker.speak(text=f"I don't understand the request {env.title}! "
                           "You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}])


def vpn_server_switch(operation: str) -> None:
    """Automator to ``START`` or ``STOP`` the VPN portal.

    Args:
        operation: Takes ``START`` or ``STOP`` as an argument.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
    """
    vpn_object = VPNServer(vpn_username=env.vpn_username or env.root_user or 'openvpn',
                           vpn_password=env.vpn_password or env.root_pass or 'aws_vpn_2021',
                           gmail_user=env.alt_gmail_user or env.gmail_user,
                           gmail_pass=env.alt_gmail_pass or env.gmail_pass,
                           recipient=env.recipient or env.alt_gmail_user or env.gmail_user,
                           phone=env.phone_number, log='FILE')
    if operation == 'START':
        shared.active_vpn = 'enabled'
        vpn_object.create_vpn_server()
    elif operation == 'STOP':
        shared.active_vpn = 'disabled'
        vpn_object.delete_vpn_server()
    shared.active_vpn = False
