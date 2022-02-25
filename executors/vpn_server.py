from multiprocessing import Process
from threading import Thread

from vpn.controller import VPNServer

from modules.audio import speaker
from modules.utils import globals, support

env = globals.ENV


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if status := globals.vpn_status['active']:
        speaker.speak(
            text=f'VPN Server was recently {status}, and the process is still running sir! Please wait and retry.')
        return

    phrase = phrase.lower()
    if 'start' in phrase or 'trigger' in phrase or 'initiate' in phrase or 'enable' in phrase or 'spin up' in phrase:
        Process(target=vpn_server_switch, kwargs={'operation': 'START'}).start()
        speaker.speak(text='VPN Server has been initiated sir! Login details will be sent to you shortly.')
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        Process(target=vpn_server_switch, kwargs={'operation': 'STOP'}).start()
        speaker.speak(text='VPN Server will be shutdown sir!')
    else:
        speaker.speak(text="I don't understand the request sir! You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}])


def vpn_server_switch(operation: str) -> None:
    """Automator to ``START`` or ``STOP`` the VPN portal.

    Args:
        operation: Takes ``START`` or ``STOP`` as an argument.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
    """
    vpn_object = VPNServer(vpn_username=env.vpn_username or env.root_user or 'openvpn',
                           vpn_password=env.vpn_password or 'aws_vpn_2021', log='FILE',
                           gmail_user=env.alt_gmail_user, gmail_pass=env.alt_gmail_pass,
                           phone=env.phone_number, recipient=env.recipient)
    if operation == 'START':
        globals.vpn_status['active'] = 'enabled'
        vpn_object.create_vpn_server()
    elif operation == 'STOP':
        globals.vpn_status['active'] = 'disabled'
        vpn_object.delete_vpn_server()
    globals.vpn_status['active'] = False
