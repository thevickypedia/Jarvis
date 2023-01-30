import os
from multiprocessing import Process
from threading import Thread

from vpn.controller import VPNServer

from jarvis.modules.audio import speaker
from jarvis.modules.database import database
from jarvis.modules.models import models
from jarvis.modules.utils import support

db = database.Database(database=models.fileio.base_db)


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT state FROM vpn").fetchone()
    if state:
        speaker.speak(text=f'VPN Server was recently {state[0]}, and the process is still running {models.env.title}! '
                           'Please wait and retry.')
        return

    phrase = phrase.lower()
    if 'start' in phrase or 'trigger' in phrase or 'initiate' in phrase or 'enable' in phrase or 'spin up' in phrase:
        Process(target=vpn_server_switch, kwargs={'operation': 'enabled'}).start()
        speaker.speak(text=f'VPN Server has been initiated {models.env.title}! '
                           'Login details will be sent to you shortly.')
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        if not os.path.isfile('vpn_info.json'):
            speaker.speak(text=f'Input file for VPN Server is missing {models.env.title}! '
                               'The VPN Server might have been shut down already.')
            return
        Process(target=vpn_server_switch, kwargs={'operation': 'disabled'}).start()
        speaker.speak(text=f'VPN Server will be shutdown {models.env.title}!')
    else:
        speaker.speak(text=f"I don't understand the request {models.env.title}! "
                           "You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}]).start()


def vpn_server_switch(operation: str) -> None:
    """Automator to ``create`` or ``destroy`` a VPN server.

    Args:
        operation: Takes ``enabled`` or ``disabled`` as an argument.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
    """
    vpn_object = VPNServer(vpn_username=models.env.vpn_username or models.env.root_user,
                           vpn_password=models.env.vpn_password or models.env.root_password,
                           domain=models.env.vpn_domain, record_name=models.env.vpn_record_name,
                           gmail_user=models.env.alt_gmail_user, gmail_pass=models.env.alt_gmail_pass,
                           recipient=models.env.recipient or models.env.gmail_user,
                           phone=models.env.phone_number, log='FILE')
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
        cursor.execute("DELETE FROM vpn WHERE state=?", (operation,))
        db.connection.commit()
