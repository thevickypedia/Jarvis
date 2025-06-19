import os
from collections.abc import Generator
from multiprocessing import Process
from threading import Thread

import vpn

from jarvis.executors import communicator
from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import models
from jarvis.modules.utils import support, util

available_regions = {"regions": []}


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
    if not available_regions["regions"]:
        available_regions["regions"] = list(vpn.util.available_regions())
    for region in available_regions["regions"]:
        if region.replace("-", " ") in phrase:
            logger.info("Custom region chosen: %s", region)
            return region


def vpn_server(phrase: str) -> None:
    """Enables or disables VPN server.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if not all((models.env.vpn_username, models.env.vpn_password)):
        speaker.speak(
            text="VPN username and password are required for any VPN server related operations."
        )
        return

    with models.db.connection as connection:
        cursor = connection.cursor()
        state = cursor.execute("SELECT state FROM vpn").fetchone()
    if state:
        speaker.speak(
            text=f"VPN Server was recently {state[0]}, and the process is still running {models.env.title}! "
            "Please wait and retry."
        )
        return

    phrase = phrase.lower()
    if (
        "start" in phrase
        or "trigger" in phrase
        or "initiate" in phrase
        or "enable" in phrase
        or "spin up" in phrase
    ):
        if custom_region := extract_custom_region(phrase=phrase):
            process = Process(
                target=vpn_server_switch,
                kwargs={"operation": "enabled", "custom_region": custom_region},
            )
            text = (
                f"VPN Server has been initiated in {custom_region} {models.env.title}! "
                "Login details will be sent to you shortly."
            )
        else:
            process = Process(target=vpn_server_switch, kwargs={"operation": "enabled"})
            text = f"VPN Server has been initiated {models.env.title}! Login details will be sent to you shortly."
        speaker.speak(text=text)
    elif (
        "stop" in phrase or "shut" in phrase or "close" in phrase or "disable" in phrase
    ):
        if not os.path.isfile(models.env.vpn_info_file):
            speaker.speak(
                text=f"Input file for VPN Server is missing {models.env.title}! "
                "The VPN Server might have been shut down already."
            )
            return
        process = Process(target=vpn_server_switch, kwargs={"operation": "disabled"})
        speaker.speak(text=f"VPN Server will be shutdown {models.env.title}!")
    else:
        speaker.speak(
            text=f"I don't understand the request {models.env.title}! "
            "You can ask me to enable or disable the VPN server."
        )
        Thread(target=support.unrecognized_dumper, args=[{"VPNServer": phrase}]).start()
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
    log_file = multiprocessing_logger(
        filename=os.path.join("logs", "vpn_server_%d_%m_%Y_%H_%M.log")
    )
    kwargs = dict(
        vpn_username=models.env.vpn_username,
        vpn_password=models.env.vpn_password,
        vpn_info=models.env.vpn_info_file,
        subdomain=models.env.vpn_subdomain,
        logger=logger,
    )
    if models.env.vpn_hosted_zone:
        kwargs["hosted_zone"] = models.env.vpn_hosted_zone
    if models.env.vpn_key_pair:
        kwargs["key_pair"] = models.env.vpn_key_pair
    if models.env.vpn_security_group:
        kwargs["security_group"] = models.env.vpn_security_group

    if custom_region:
        kwargs["aws_region_name"] = custom_region
        success_subject = (
            f"VPN Server on {custom_region!r} has been configured successfully!"
        )
        fail_subject = f"Failed to create VPN Server on {custom_region!r}!"
    else:
        success_subject = "VPN Server has been configured successfully!"
        fail_subject = "Failed to create VPN Server!"
    vpn_object = vpn.VPNServer(**kwargs)
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT or REPLACE INTO vpn (state) VALUES (?);", (operation,))
        connection.commit()
    if operation == "enabled":
        if vpn_data := vpn_object.create_vpn_server():
            entrypoint = vpn_data.get("entrypoint") or vpn_data.get("public_dns")
            communicator.send_email(
                subject=success_subject,
                body=f"Entrypoint: {entrypoint}",
                title="VPN Server",
                recipient=models.env.recipient,
                attachment=models.env.vpn_info_file,
            )
        else:
            communicator.send_email(
                subject=fail_subject,
                recipient=models.env.recipient,
                title="VPN Server",
                attachment=log_file,
                body="Failed to initiate VPN server. "
                "Please check the logs (attached) for more information.",
            )
    elif operation == "disabled":
        vpn_object.delete_vpn_server()
    with models.db.connection as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM vpn WHERE state=?", (operation,))
        connection.commit()
