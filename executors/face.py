import os
import shutil
import sys
from datetime import datetime
from typing import NoReturn

from PIL import Image

from executors.word_match import word_match
from modules.audio import listener, speaker
from modules.exceptions import CameraError
from modules.facenet.face import FaceNet
from modules.logger.custom_logger import logger
from modules.models import models
from modules.utils import support

TRAINING_DIR = os.path.realpath("train")


def detected_face() -> NoReturn:
    """Captures a picture, shows a preview and stores it for future recognition."""
    sys.stdout.write('\rNew face has been detected. Like to give it a name?')
    speaker.speak(text='I was able to detect a face, but was unable to recognize it.')
    Image.open('cv2_open.jpg').show()
    speaker.speak(text=f"I've taken a photo of you. Preview on your screen {models.env.title}!"
                       "Would you like to give it a name, so that I can add it to my database of known list?"
                       "If you're ready, please tell me a name, or simply say exit.", run=True)
    phrase = listener.listen(timeout=3, phrase_limit=5)
    if not phrase or 'exit' in phrase or 'quit' in phrase or 'Xzibit' in phrase:
        os.remove('cv2_open.jpg')
        speaker.speak(text="I've deleted the image.", run=True)
    else:
        phrase = phrase.replace(' ', '_')
        # creates a named directory if it is not found already
        if not os.path.exists(os.path.join(TRAINING_DIR, phrase)):
            os.makedirs(os.path.join(TRAINING_DIR, phrase))
        img_name = f"{phrase}_{datetime.now().strftime('%I_%M_%p')}.jpg"  # adds time to image name to avoid overwrite
        os.rename('cv2_open.jpg', img_name)  # renames the files
        shutil.move(src=img_name, dst=os.path.join(TRAINING_DIR, phrase))  # move under TRAINING_DIR -> named directory
        speaker.speak(text=f"Image has been saved as {img_name}. I will be able to recognize {phrase} in future.")


def faces(phrase: str) -> None:
    """Initiates face recognition script and looks for images stored in named directories within ``train`` directory."""
    support.flush_screen()
    if word_match(phrase=phrase, match_list=["detect", "detection", "faces", "look"]):
        if FaceNet().face_detection(retry_count=5):
            detected_face()
    else:
        os.mkdir(TRAINING_DIR) if not os.path.isdir(TRAINING_DIR) else None
        speaker.speak(text='Initializing facial recognition. Please smile at the camera for me.', run=True)
        sys.stdout.write('\rLooking for faces to recognize.')
        try:
            result = FaceNet().face_recognition(location=TRAINING_DIR)
        except CameraError:
            support.flush_screen()
            logger.error('Unable to access the camera.')
            speaker.speak(text="I was unable to access the camera. Facial recognition can work only when cameras are "
                               "present and accessible.")
            return
        if result:
            speaker.speak(text=f'Hi {result}! How can I be of service to you?')
            return
        sys.stdout.write('\rLooking for faces to detect.')
        speaker.speak(text="No faces were recognized. Switching on to face detection.", run=True)
        result = FaceNet().face_detection()
        if not result:
            sys.stdout.write('\rNo faces were recognized nor detected.')
            speaker.speak(text='No faces were recognized. nor detected. Please check if your camera is working, '
                               'and look at the camera when you retry.')
            return
