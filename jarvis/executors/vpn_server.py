import os
from collections.abc import Generator
from multiprocessing import Process
from threading import Thread

from botocore.exceptions import (BotoCoreError, ClientError,
                                 EndpointConnectionError, SSLError)

from jarvis.modules.audio import speaker
from jarvis.modules.database import database
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support, util

db = database.Database(database=models.fileio.base_db)

try:
    import vpn

    VPN_PRE_CHECK = True
except (EndpointConnectionError, ClientError, SSLError, BotoCoreError) as error:
    VPN_PRE_CHECK = False
    logger.error(error)


def regional_phrase(phrase: str) -> Generator[str]:
    """Converts alphabetical numbers into actual numbers.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Yields:
        str:
        Yields the word.
    """
    for word in phrase.split():
        if num := util.words_to_number(input_=word):
            yield str(num)
        else:
            yield word


def extract_custom_region(phrase: str) -> str:
    """Tries to find region name in the phrase.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        str:
        Region name if a match is found.
    """
    phrase = " ".join(regional_phrase(phrase=phrase))
    for region in vpn.settings.available_regions:
        if region.replace('-', ' ') in phrase:
            logger.info("Custom region chosen: %s", region)
            return region


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not VPN_PRE_CHECK:
        speaker.speak("VPN server requires an active A.W.S configuration. Please check the logs for more information.")
        logger.error("Please refer to the following URLs to configure AWS CLI, to use VPN features.")
        logger.error("AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        logger.error("AWS configure: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html")
        return
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT state FROM vpn").fetchone()
    if state:
        speaker.speak(text=f'VPN Server was recently {state[0]}, and the process is still running {models.env.title}! '
                           'Please wait and retry.')
        return

    phrase = phrase.lower()
    if 'start' in phrase or 'trigger' in phrase or 'initiate' in phrase or 'enable' in phrase or 'spin up' in phrase:
        if custom_region := extract_custom_region(phrase=phrase):
            process = Process(target=vpn_server_switch, kwargs={'operation': 'enabled', 'custom_region': custom_region})
            text = f'VPN Server has been initiated in {custom_region} {models.env.title}! ' \
                   'Login details will be sent to you shortly.'
        else:
            process = Process(target=vpn_server_switch, kwargs={'operation': 'enabled'})
            text = f'VPN Server has been initiated {models.env.title}! Login details will be sent to you shortly.'
        speaker.speak(text=text)
    elif 'stop' in phrase or 'shut' in phrase or 'close' in phrase or 'disable' in phrase:
        if not os.path.isfile(vpn.INFO_FILE):
            speaker.speak(text=f'Input file for VPN Server is missing {models.env.title}! '
                               'The VPN Server might have been shut down already.')
            return
        process = Process(target=vpn_server_switch, kwargs={'operation': 'disabled'})
        speaker.speak(text=f'VPN Server will be shutdown {models.env.title}!')
    else:
        speaker.speak(text=f"I don't understand the request {models.env.title}! "
                           "You can ask me to enable or disable the VPN server.")
        Thread(target=support.unrecognized_dumper, args=[{'VPNServer': phrase}]).start()
        return
    process.name = "vpn_server"
    process.start()


def vpn_server_switch(operation: str, custom_region: str = None) -> None:
    """Automator to ``create`` or ``destroy`` a VPN server.

    Args:
        operation: Takes ``enabled`` or ``disabled`` as argument.
        custom_region: Takes a custom AWS region as argument.

    See Also:
        - Check Read Me in `vpn-server <https://git.io/JzCbi>`__ for more information.
    """
    config.multiprocessing_logger(filename=os.path.join('logs', 'vpn_server_%d_%m_%Y_%H_%M.log'))
    kwargs = dict(vpn_username=models.env.vpn_username or models.env.root_user,
                  vpn_password=models.env.vpn_password or models.env.root_password,
                  domain=models.env.vpn_domain, record_name=models.env.vpn_record_name,
                  gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass,
                  recipient=models.env.recipient or models.env.gmail_user,
                  phone=models.env.phone_number, logger=logger)
    if custom_region:
        kwargs['aws_region_name'] = custom_region
    vpn_object = vpn.VPNServer(**kwargs)
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
