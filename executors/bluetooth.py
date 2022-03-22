import json
import re
import subprocess
import sys
import time
import unicodedata

from modules.audio import speaker
from modules.models import models
from modules.utils import support

env = models.env


def connector(phrase: str, targets: dict) -> bool:
    """Scans bluetooth devices in range and establishes connection with the matching device in phrase.

    Args:
        phrase: Takes the spoken phrase as an argument.
        targets: Takes a dictionary of scanned devices as argument.

    Returns:
        bool:
        Boolean True or False based on connection status.
    """
    connection_attempt = False
    for target in targets:
        if target['name']:
            target['name'] = unicodedata.normalize("NFKD", target['name'])
            if any(re.search(line, target['name'], flags=re.IGNORECASE) for line in phrase.split()):
                connection_attempt = True
                if 'disconnect' in phrase:
                    output = subprocess.getoutput(cmd=f"blueutil --disconnect {target['address']}")
                    if not output:
                        time.sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                        speaker.speak(text=f"Disconnected from {target['name']} {env.title}!")
                    else:
                        speaker.speak(text=f"I was unable to disconnect {target['name']} {env.title}!. "
                                           f"Perhaps it was never connected.")
                elif 'connect' in phrase:
                    output = subprocess.getoutput(cmd=f"blueutil --connect {target['address']}")
                    if not output:
                        time.sleep(2)  # included a sleep here, so it avoids voice swapping between devices
                        speaker.speak(text=f"Connected to {target['name']} {env.title}!")
                    else:
                        speaker.speak(text=f"Unable to connect {target['name']} {env.title}!, "
                                           "please make sure the device is turned on and ready to pair.")
                break
    return connection_attempt


def bluetooth(phrase: str) -> None:
    """Find and connect to bluetooth devices nearby.

    Args:
        phrase: Takes the voice recognized statement as argument.
    """
    if not env.mac:
        support.missing_windows_features()
        return
    phrase = phrase.lower()
    if 'turn off' in phrase or 'power off' in phrase:
        subprocess.call("blueutil --power 0", shell=True)
        sys.stdout.write('\rBluetooth has been turned off')
        speaker.speak(text=f"Bluetooth has been turned off {env.title}!")
    elif 'turn on' in phrase or 'power on' in phrase:
        subprocess.call("blueutil --power 1", shell=True)
        sys.stdout.write('\rBluetooth has been turned on')
        speaker.speak(text=f"Bluetooth has been turned on {env.title}!")
    elif 'disconnect' in phrase and ('bluetooth' in phrase or 'devices' in phrase):
        subprocess.call("blueutil --power 0", shell=True)
        time.sleep(2)
        subprocess.call("blueutil --power 1", shell=True)
        speaker.speak(text=f"All bluetooth devices have been disconnected {env.title}!")
    else:
        sys.stdout.write('\rScanning paired Bluetooth devices')
        paired = subprocess.getoutput(cmd="blueutil --paired --format json")
        paired = json.loads(paired)
        if not connector(phrase=phrase, targets=paired):
            sys.stdout.write('\rScanning UN-paired Bluetooth devices')
            speaker.speak(text=f"No connections were established {env.title}, looking for un-paired devices.", run=True)
            unpaired = subprocess.getoutput(cmd="blueutil --inquiry --format json")
            unpaired = json.loads(unpaired)
            connector(phrase=phrase, targets=unpaired) if unpaired else \
                speaker.speak(text=f"No un-paired devices found {env.title}! You may want to be more precise.")
