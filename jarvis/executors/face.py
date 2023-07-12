import glob
import os
import shutil
from datetime import datetime
from typing import NoReturn

from PIL import Image

from jarvis.executors import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.exceptions import CameraError
from jarvis.modules.facenet.face import FaceNet
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import support

TRAINING_DIR = os.path.realpath("train")
FACE_DETECTION_TEMP_FILE = 'cv2_open.jpg'


def detected_face() -> NoReturn:
    """Captures a picture, shows a preview and stores it for future recognition."""
    support.write_screen(text='New face has been detected. Like to give it a name?')
    speaker.speak(text='I was able to detect a face, but was unable to recognize it.')
    Image.open(FACE_DETECTION_TEMP_FILE).show()
    speaker.speak(text=f"I've taken a photo of you. Preview on your screen {models.env.title}! "
                       "Please tell me a name if you'd like to recognize this face in the future, or simply say exit.",
                  run=True)
    phrase = listener.listen()
    if not phrase or 'exit' in phrase or 'quit' in phrase or 'Xzibit' in phrase:
        os.remove('cv2_open.jpg')
        speaker.speak(text="I've deleted the image.", run=True)
    else:
        phrase = phrase.replace(' ', '_')
        # creates a named directory if it is not found already
        if not os.path.exists(os.path.join(TRAINING_DIR, phrase)):
            os.makedirs(os.path.join(TRAINING_DIR, phrase))
        img_name = f"{phrase}_{datetime.now().strftime('%B_%d_%Y_%I-%M_%p')}.jpg"  # adds datetime to image name
        os.rename(FACE_DETECTION_TEMP_FILE, img_name)  # renames the files
        shutil.move(src=img_name, dst=os.path.join(TRAINING_DIR, phrase))  # move under TRAINING_DIR -> named directory
        speaker.speak(text=f"Image has been added to known database. I will be able to recognize {phrase} in future.")


def faces(phrase: str) -> None:
    """Initiates face recognition script and looks for images stored in named directories within ``train`` directory."""
    support.flush_screen()
    if word_match.word_match(phrase=phrase, match_list=("detect", "detection", "faces", "look")):
        if FaceNet().face_detection(retry_count=5):
            detected_face()
    else:
        if os.path.isdir(TRAINING_DIR) and \
                set(os.path.dirname(p) for p in glob.glob(os.path.join(TRAINING_DIR, "*", ""), recursive=True)):
            speaker.speak(text='Initializing facial recognition. Please smile at the camera for me.', run=True)
            support.write_screen(text='Looking for faces to recognize.')
            try:
                result = FaceNet().face_recognition(location=TRAINING_DIR)
            except CameraError:
                support.flush_screen()
                logger.error('Unable to access the camera.')
                speaker.speak(text="I was unable to access the camera. Facial recognition can work only when a camera "
                                   "is present and accessible.")
                return
            if result:
                speaker.speak(text=f'Hi {result}! How can I be of service to you?')
                return
            speaker.speak(text="No faces were recognized. Switching to face detection.", run=True)
        else:
            os.mkdir(TRAINING_DIR) if not os.path.isdir(TRAINING_DIR) else None
            speaker.speak(text=f"No named training modules were found {models.env.title}. Switching to face detection",
                          run=True)
        if FaceNet().face_detection(filename=FACE_DETECTION_TEMP_FILE):
            detected_face()
        else:
            speaker.speak(text='No faces were recognized. nor detected. Please check if your camera is working, '
                               'and look at the camera when you retry.')
