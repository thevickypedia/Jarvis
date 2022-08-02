import os
from multiprocessing import Process
from threading import Thread

from vpn.controller import VPNServer

from modules.audio import speaker
from modules.database import database
from modules.models import models
from modules.utils import support

env = models.env
fileio = models.FileIO()

db = database.Database(database=fileio.base_db)


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT state FROM vpn").fetchone()
    if state:
        speaker.speak(text=f'VPN Server was recently {state[0]}, and the process is still running {env.title}! '
                           'Please wait and retry.')
        return

    phrase = phrase.lower()
    if 'start' in phrase or 'trigger' in phrase or 'initiate' in phrase or 'enable' in phrase or 'spin up' in phrase:
        Process(target=vpn_server_switch, kwargs={'operation': 'enabled'}).start()
        speaker.speak(text=f'VPN Server has been initiated {env.title}! Login details will be sent to you shortly.')
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        if not os.path.isfile('vpn_info.json'):
            speaker.speak(text=f'Input file for VPN Server is missing {env.title}! '
                               'The VPN Server might have been shut down already.')
            return
        Process(target=vpn_server_switch, kwargs={'operation': 'disabled'}).start()
        speaker.speak(text=f'VPN Server will be shutdown {env.title}!')
    else:
        speaker.speak(text=f"I don't understand the request {env.title}! "
                           "You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}]).start()


def vpn_server_switch(operation: str) -> None:
    """Automator to ``create`` or ``destroy`` a VPN server.

    Args:
        operation: Takes ``enabled`` or ``disabled`` as an argument.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
    """
    vpn_object = VPNServer(vpn_username=env.vpn_username or env.root_user or 'openvpn',
                           vpn_password=env.vpn_password or env.root_pass or 'aws_vpn_2021',
                           gmail_user=env.alt_gmail_user, gmail_pass=env.alt_gmail_pass,
                           recipient=env.recipient or env.alt_gmail_user,
                           phone=env.phone_number, log='FILE')
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("INSERT or REPLACE INTO vpn (state) VALUES (?);", (operation,))
        db.connection.commit()
    if operation == 'enabled':
        vpn_object.create_vpn_server()
    elif operation == 'disabled':
        vpn_object.delete_vpn_server()
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute(f"DELETE FROM vpn WHERE state='{operation}'")
        db.connection.commit()
