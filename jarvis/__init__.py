import os

from pynotification import pynotifier

version = "7.1.1"

try:
    import cv2  # noqa
    import face_recognition  # noqa
    import playsound  # noqa
    import pvporcupine  # noqa
    import pyaudio  # noqa
except ImportError as error:
    pynotifier(title="First time user?", dialog=True,
               message=f"Please run\n\n{os.path.join(os.path.dirname(__file__), 'lib', 'install.sh')}")
    raise UserWarning(f"{error.__str__()}\n\nPlease run\n\n"
                      f"{os.path.join(os.path.dirname(__file__), 'lib', 'install.sh')}")
else:
    from .main import start  # noqa
