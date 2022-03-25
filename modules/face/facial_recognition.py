import os
import sys
from typing import Union

from cv2 import (COLOR_BGR2GRAY, CascadeClassifier, VideoCapture, cvtColor,
                 data, imwrite)
from face_recognition import (compare_faces, face_encodings, face_locations,
                              load_image_file)

from modules.exceptions import CameraError


class Face:
    """Module for ``face recognition`` script using defined tolerance level and specific model.

    >>> Face

    """

    def __init__(self):
        self.training_dataset = "train"  # main dir within which training images are placed under named directories
        self.learning_rate = 0.6  # tolerance level - keep switching this until you find perfection in recognition
        self.model = "hog"  # model using which the images are matched
        source = None
        for i in range(0, 3):
            cam = VideoCapture(i)
            if cam is None or not cam.isOpened() or cam.read() == (False, None):
                pass
            else:
                source = i
                break
        if source is None:
            sys.stdout.write('\rNo cameras were found.')
            raise CameraError(
                "No cameras were found."
            )
        self.validation_video = VideoCapture(source)  # camera id - depends on installed camera applications
        self.train_faces, self.train_names = [], []
        for character_dir in os.listdir(self.training_dataset):  # loads the training dataset
            try:
                for file_name in os.listdir(f'{self.training_dataset}/{character_dir}'):
                    if file_name.startswith('.'):
                        continue
                    # loads all the files within the named repo
                    img = load_image_file(f'{self.training_dataset}/{character_dir}/{file_name}')
                    encoded = face_encodings(img)[0]  # generates face encoding matrix
                    self.train_faces.append(encoded)  # loads ended values to match
                    self.train_names.append(character_dir)  # loads the names of each named sub directories
            except (IndexError, NotADirectoryError):
                pass

    def face_recognition(self) -> Union[None, str]:
        """Recognizes faces from the training dataset - images in the ``train`` directory.

        Returns:
            None or str:
            str - Name of the person in case of a recognized face.
            None - NoneType if no face was recognized.

        """
        for _ in range(20):
            ret, img = self.validation_video.read()  # reads video from web cam
            identifier = face_locations(img, model=self.model)  # gets image from the video read above
            encoded_ = face_encodings(img, identifier)  # creates an encoding for the image
            for face_encoding, face_location in zip(encoded_, identifier):
                # using learning_rate, the encoding is matched against the encoded matrix for images in named directory
                results = compare_faces(self.train_faces, face_encoding, self.learning_rate)
                if True in results:  # if a match is found the directory name is rendered and returned as match value
                    match = self.train_names[results.index(True)]
                    return match

    def face_detection(self) -> bool:
        """Detects faces by converting it to grayscale and neighbor match method.

        Returns:
            bool:
            A boolean value if not a face was detected.

        """
        cascade = CascadeClassifier(data.haarcascades + "haarcascade_frontalface_default.xml")
        for _ in range(20):
            ignore, image = self.validation_video.read()  # reads video from web cam
            scale = cvtColor(image, COLOR_BGR2GRAY)  # convert the captured image to grayscale
            scale_factor = 1.1  # specify how much the image size is reduced at each image scale
            min_neighbors = 5  # specify how many neighbors each candidate rectangle should have to retain it
            faces = cascade.detectMultiScale(scale, scale_factor, min_neighbors)  # faces are listed as tuple here
            # This is a hacky way to solve the problem. The problem when using "if faces:":
            # ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
            # When used either of the suggestion:
            # AttributeError: 'tuple' object has no attribute 'any' / 'all'
            # But happens only when the value is true so ¯\_(ツ)_/¯
            try:
                if faces:
                    pass
            except ValueError:
                imwrite('cv2_open.jpg', image)
                self.validation_video.release()
                return True


if __name__ == '__main__':
    sys.stdout.write(Face().face_recognition())
