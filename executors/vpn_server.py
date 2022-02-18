import os
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
        Thread(target=vpn_server_switch,
               kwargs={'operation': 'START', 'phone_number': env.phone_number, 'recipient': env.recipient}).start()
        speaker.speak(text='VPN Server has been initiated sir! Login details will be sent to you shortly.')
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        Thread(target=vpn_server_switch,
               kwargs={'operation': 'STOP', 'phone_number': env.phone_number, 'recipient': env.recipient}).start()
        speaker.speak(text='VPN Server will be shutdown sir!')
    else:
        speaker.speak(text="I don't understand the request sir! You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}])


def vpn_server_switch(operation: str, phone_number: str, recipient: str) -> None:
    """Automator to ``START`` or ``STOP`` the VPN portal.

    Args:
        operation: Takes ``START`` or ``STOP`` as an argument.
        phone_number: Phone number to which the notification has to be sent.
        recipient: Email address to which the notification has to be sent.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
    """
    vpn_object = VPNServer(vpn_username=os.environ.get('vpn_username', os.environ.get('USER', 'openvpn')),
                           vpn_password=os.environ.get('vpn_password', 'aws_vpn_2021'), log='FILE',
                           gmail_user=os.environ.get('alt_gmail_user', os.environ.get('gmail_user')),
                           gmail_pass=os.environ.get('alt_gmail_pass', os.environ.get('gmail_pass')),
                           phone=phone_number, recipient=recipient)
    if operation == 'START':
        globals.vpn_status['active'] = 'enabled'
        vpn_object.create_vpn_server()
    elif operation == 'STOP':
        globals.vpn_status['active'] = 'disabled'
        vpn_object.delete_vpn_server()
    globals.vpn_status['active'] = False
