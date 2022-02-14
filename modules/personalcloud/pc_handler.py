# noinspection PyUnresolvedReferences
"""Controller for `Personal Cloud <https://github.com/thevickypedia/personal_cloud>`__.

>>> PersonalCloud

References:
    `PersonalCloud README.md <https://github.com/thevickypedia/personal_cloud/blob/main/README.md>`__

See Also:
    PersonalCloud integration requires Admin previleages for the default ``Terminal``.

    Step 1:
        - macOS 10.14.* and higher - System Preferences -> Security & Privacy -> Privacy -> Full Disk Access
        - macOS 10.13.* and lower - System Preferences -> Security & Privacy -> Privacy -> Accessibility
    Step 2:
        Unlock for admin privileges. Click on the "+" icon. Select Applications -> Utilities -> Terminal
"""

import contextlib
import os
import random
from pathlib import Path
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from string import ascii_letters, digits
from subprocess import check_output
from time import sleep

from aeosa.aem.aemsend import EventError
from appscript import app as apple_script
from appscript.reference import CommandError

from executors.custom_logger import logger
from executors.sms import notify


def get_port() -> int:
    """Chooses a PORT number dynamically that is not being used to ensure we don't rely on a single port.

    Instead of binding to a specific port, ``sock.bind(('', 0))`` is used to bind to 0.

    See Also:
        - The port number chosen can be found using ``sock.getsockname()[1]``
        - Passing it on to the slaves so that they can connect back.
        - ``sock`` is the socket that was created, returned by socket.socket.

    Notes:
        - Well-Known ports: 0 to 1023
        - Registered ports: 1024 to 49151
        - Dynamically available: 49152 to 65535
        - The OS will then pick an available port.

    Returns:
        int:
        Randomly chosen port number that is not in use.
    """
    with contextlib.closing(socket(AF_INET, SOCK_STREAM)) as sock:
        sock.bind(('', 0))
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def delete_repo(target_path: str) -> None:
    """Called during enable and disable to delete any existing bits for a clean start next time."""
    os.system(f"rm -rf {target_path}/personal_cloud")  # delete repo for a fresh start


def enable(target_path: str, recipient: str, username: str, password: str, phone_number: str) -> None:
    """Enables `personal cloud <https://github.com/thevickypedia/personal_cloud>`__.

    Args:
        target_path: Path where the repository should be cloned.
        recipient: Email address to which the notification has to be sent.
        username: Username to authenticate ``gmail-connector``.
        password: Password to authenticate ``gmail-connector``.
        phone_number: Phone number to which the SMS has to be sent.

    Notes:
        - Clones ``personal_cloud`` repo in a dedicated Terminal.
        - Creates a virtual env and installs the requirements within it (ETA: ~20 seconds)
        - If ``personal_cloud_host`` env var is provided, Jarvis will mount the drive if connected to the device.
        - Sets env vars required for the personal cloud.
        - Generates random username and passphrase for login info.
        - Triggers personal cloud using another Terminal session.
        - Sends an SMS with ``endpoint``, ``username`` and ``password`` to the ``phone_number``.
    """
    delete_repo(target_path=target_path)
    initial_script = f"cd {target_path} && git clone -q https://github.com/thevickypedia/personal_cloud.git && " \
                     f"cd personal_cloud && python3 -m venv venv && source venv/bin/activate && " \
                     f"pip install -r requirements.txt"

    try:
        apple_script('Terminal').do_script(initial_script)
    except (CommandError, EventError) as ps_error:
        logger.error(ps_error)
        notify(user=username, password=password, number=phone_number,
               body="Sir! I was unable to trigger your personal cloud due to lack of permissions.\n"
                    "Please check the log file.")
        return

    pc_port = get_port()
    pc_username = ''.join(random.choices(ascii_letters, k=10))
    pc_password = ''.join(random.choices(ascii_letters + digits, k=10))
    pc_host = f"'{os.environ.get('personal_cloud_host')}'"

    # export PORT for both ngrok and exec scripts as they will be running in different Terminal sessions
    ngrok_script = f"cd {target_path}/personal_cloud && export port={pc_port} && source venv/bin/activate && " \
                   f"cd helper_functions && python3 ngrok.py"

    exec_script = f"export host_path='{pc_host}'" if pc_host and os.path.isdir(pc_host) else ''
    exec_script += f"export port={pc_port} && " \
                   f"export username={pc_username} && " \
                   f"export password={pc_password} && " \
                   f"export gmail_user={username} && " \
                   f"export gmail_pass={password} && " \
                   f"export recipient={recipient} && " \
                   f"cd {target_path}/personal_cloud && source venv/bin/activate && python3 authserver.py"

    cloned_path = f'{target_path}/personal_cloud'

    while True:
        packages = [path_.stem.split('-')[0] for path_ in Path(cloned_path).glob('**/site-packages/*')]
        if 'requests' in packages and 'gmail_connector' in packages:
            apple_script('Terminal').do_script(exec_script)
            break

    while True:
        packages = [path_.stem.split('-')[0] for path_ in Path(cloned_path).glob('**/site-packages/*')]
        if 'pyngrok' in packages:
            apple_script('Terminal').do_script(ngrok_script)
            break

    while True:  # wait for the endpoint url (as file) to get generated within personal_cloud
        if os.path.exists(f'{cloned_path}/helper_functions/url'):
            sleep(2)
            with open(f'{cloned_path}/helper_functions/url', 'r') as file:
                url = file.read()  # commit # dfc37853dfe232e268843cbe53719bd9a09903c4 on personal_cloud
            break

    logger.info(f'Personal Cloud is being served at: {url}')
    logger.info(f'Username: {pc_username}')
    logger.info(f'Password: {pc_password}')

    if not all([username, password, phone_number, recipient]):
        logger.error('Args for notifications are not configured.')
        return

    if url.startswith('http'):
        notify(user=username, password=password, number=phone_number,
               body=f"URL: {url}\nUsername: {pc_username}\nPassword: {pc_password}")
    else:
        notify(user=username, password=password, number=phone_number,
               body="Unable to start ngrok! Please check the logs for more information.")


def disable(target_path: str) -> None:
    """Kills `authserver.py <https://git.io/JchR5>`__ and `ngrok.py <https://git.io/JchBu>`__ to stop hosting.

    This eliminates the hassle of passing args and handling threads.
    """
    pid_check = check_output("ps -ef | grep 'authserver.py\\|ngrok.py'", shell=True)
    pid_list = pid_check.decode('utf-8').split('\n')
    for pid_info in pid_list:
        if pid_info and 'Library' in pid_info and ('/bin/sh' not in pid_info or 'grep' not in pid_info):
            os.system(f'kill -9 {pid_info.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout
    delete_repo(target_path=target_path)
