import os
import re
import smtplib
import socket
import subprocess
from typing import List, Union

from pydantic import EmailStr

from modules.logger.custom_logger import logger
from modules.utils import support


def get_mx_records(domain: str) -> List:
    """Get MX (Mail Exchange server) records for the given domain.

    Args:
        domain: FQDN (Fully Qualified Domain Name) extracted from the email address.

    Returns:
        list:
        List of IP addresses of all the mail exchange servers from authoritative/non-authoritative answer section.
    """
    try:
        output = subprocess.check_output(f'nslookup -q=mx {domain}', shell=True)
        result = [support.hostname_to_ip(hostname=line.split()[-1], localhost=False)
                  for line in output.decode().splitlines() if line.startswith(domain)]
        return support.remove_duplicates(input_=support.matrix_to_flat_list(input_=result))
    except subprocess.CalledProcessError as error:
        logger.error(error)


def validate(email: Union[EmailStr, str], check_smtp: bool = True, timeout: Union[int, float] = 3) -> Union[bool, None]:
    """Validates email address deliver-ability using SMTP.

    Args:
        email: Email address.
        timeout: Time in seconds to wait for a result.
        check_smtp: Boolean flag whether to use smtp connection.

    Warnings:
        - Timeout specified is to create a socket connection with each mail exchange server.
        - If a mail server has 10 mx records and timeout is set to 3, the total wait time will be 30 seconds.

    See Also:
        - This is not a perfect solution for validating email address.
        - Works perfect for gmail, but yahoo and related mail servers always returns OK even with garbage email address.
        - Works only if port 25 is not blocked by ISP.

    Returns:
        bool:
        Boolean flag to indicate if the email address is valid.
    """
    if not (mx_records := get_mx_records(domain=email.split('@')[-1])):
        return  # Invalid domain name

    logger.info(f"Found {len(mx_records)} mx records for the domain: {email.split('@')[-1]}")
    logger.debug(mx_records)

    if not check_smtp:
        return True  # SMTP check has been bypassed but domain seems to be legit

    server = smtplib.SMTP(timeout=timeout)
    for record in mx_records:
        logger.info(f"Trying {record}")
        try:
            server.connect(host=record)
        except socket.error as error:
            logger.error(error)
            continue
        server.ehlo_or_helo_if_needed()
        server.mail(sender=os.environ.get('GMAIL_USER'))
        code, msg = server.rcpt(recip=email)
        msg = re.sub(r"\d+.\d+.\d+", '', msg.decode(encoding='utf-8')).strip()
        msg = ' '.join(msg.splitlines()).replace('  ', ' ').strip()
        logger.info(f'{code}: {msg}')
        if code == 550:  # Definitely invalid email address
            return False
        if code < 400:  # Valid email address
            return True
    return False  # Invalid but may also be valid in case of a port filtering by ISP
