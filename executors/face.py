import os
import shutil
import sys
from datetime import datetime

from PIL import Image

from executors.logger import logger
from modules.audio import listener, speaker
from modules.exceptions import CameraError
from modules.face.facial_recognition import Face
from modules.utils import support


def face_detection() -> None:
    """Initiates face recognition script and looks for images stored in named directories within ``train`` directory."""
    support.flush_screen()
    train_dir = 'train'
    os.mkdir(train_dir) if not os.path.isdir(train_dir) else None
    speaker.speak(text='Initializing facial recognition. Please smile at the camera for me.', run=True)
    sys.stdout.write('\rLooking for faces to recognize.')
    try:
        result = Face().face_recognition()
    except CameraError:
        support.flush_screen()
        logger.error('Unable to access the camera.')
        speaker.speak(text="I was unable to access the camera. Facial recognition can work only when cameras are "
                           "present and accessible.")
        return
    if not result:
        sys.stdout.write('\rLooking for faces to detect.')
        speaker.speak(text="No faces were recognized. Switching on to face detection.", run=True)
        result = Face().face_detection()
        if not result:
            sys.stdout.write('\rNo faces were recognized nor detected.')
            speaker.speak(text='No faces were recognized. nor detected. Please check if your camera is working, '
                               'and look at the camera when you retry.')
            return
        sys.stdout.write('\rNew face has been detected. Like to give it a name?')
        speaker.speak(text='I was able to detect a face, but was unable to recognize it.')
        Image.open('cv2_open.jpg').show()
        speaker.speak(text="I've taken a photo of you. Preview on your screen. Would you like to give it a name, "
                           "so that I can add it to my database of known list? If you're ready, please tell me a name, "
                           "or simply say exit.", run=True)
        phrase = listener.listen(timeout=3, phrase_limit=5)
        if phrase == 'SR_ERROR' or 'exit' in phrase or 'quit' in phrase or 'Xzibit' in phrase:
            os.remove('cv2_open.jpg')
            speaker.speak(text="I've deleted the image.", run=True)
        else:
            phrase = phrase.replace(' ', '_')
            # creates a named directory if it is not found already
            if not os.path.exists(f'{train_dir}/{phrase}'):
                os.makedirs(f'{train_dir}/{phrase}')
            c_time = datetime.now().strftime("%I_%M_%p")
            img_name = f"{phrase}_{c_time}.jpg"  # adds current time to image name to avoid overwrite
            os.rename('cv2_open.jpg', img_name)  # renames the files
            shutil.move(src=img_name, dst=f'{train_dir}/{phrase}')  # move files into named directory within train_dir
            speaker.speak(text=f"Image has been saved as {img_name}. I will be able to recognize {phrase} in future.")
    else:
        speaker.speak(text=f'Hi {result}! How can I be of service to you?')
