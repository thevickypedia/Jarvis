# noinspection PyUnresolvedReferences
"""Module for face recognition, face detection and image capture.

>>> Face

"""

import imghdr
import os

import cv2
import face_recognition
from cv2.data import haarcascades
from PIL import Image, UnidentifiedImageError
from pydantic import FilePath

from jarvis.modules.logger import logger
from jarvis.modules.models import models


def verify_image(filename: str | FilePath) -> bool:
    """Verifies if a particular image can be used for training.

    Args:
        filename: Name/path of the file.

    Returns:
        bool:
        Returns a boolean flag to indicate whether the image is compatible.
    """
    try:
        Image.open(filename).verify()
    except UnidentifiedImageError as error:
        logger.error(error)
        return False
    if imghdr.what(file=filename).lower() in ("jpg", "png", "jpeg"):
        return True


def condition_check(filename: str | FilePath) -> bool:
    """Condition check to load the dataset.

    Args:
        filename: Name of the file to check.

    Returns:
        bool:
        Boolean flag whether the file can be considered for training.
    """
    if not os.path.isfile(filename):
        return False
    if os.path.split(filename)[-1].startswith("."):
        return False
    if not verify_image(filename):
        return False
    return True


class FaceNet:
    """Module for image capture, face recognition and detection using defined tolerance level and specific model.

    >>> FaceNet

    Raises:
        CameraError:
        If unable to connect to the camera.
    """

    LEARNING_RATE = 0.6  # tolerance level - keep switching this until you find perfection in recognition
    MODEL = "hog"  # model using which the images are matched

    def __init__(self):
        """Instantiates the ``Processor`` object and sources the camera hardware."""
        self.validation_video = cv2.VideoCapture(models.env.camera_index)
        self.train_faces, self.train_names = [], []

    def load_dataset(self, location: str) -> None:
        """Loads the dataset."""
        logger.debug("Loading dataset to classify existing images.")
        for char_dir in os.listdir(location):  # loads the training dataset
            if not os.path.isdir(os.path.join(location, char_dir)):
                continue
            for file_name in os.listdir(os.path.join(location, char_dir)):
                if not condition_check(
                    filename=os.path.join(location, char_dir, file_name)
                ):
                    continue
                # loads all the files within the named repo
                img = face_recognition.load_image_file(
                    os.path.join(location, char_dir, file_name)
                )
                # generates face encoding matrix
                if encoded := face_recognition.face_encodings(img):
                    encoded = encoded[0]
                    # loads ended values to match
                    self.train_faces.append(encoded)
                    # loads the names of each named subdirectories
                    self.train_names.append(char_dir)

    def face_recognition(
        self, location: str | FilePath, retry_count: int = 20
    ) -> str | None:
        """Recognizes faces from the training dataset - images in the ``train`` directory.

        Returns:
            retry_count: Number of trials to recognize a face before the function can quit.

        Returns:
            str:
            Name of the enclosing directory in case of a recognized face.
        """
        if not face_recognition:
            logger.error("Requirement unsatisfied!!")
            return
        logger.debug("Initiating face recognition.")
        self.load_dataset(location=location)
        for _ in range(retry_count):
            # reads video from web cam
            ret, img = self.validation_video.read()
            if not ret:
                logger.warning(
                    "Unable to read from camera index: %d", models.env.camera_index
                )
                continue
            # gets image from the video read above
            identifier = face_recognition.face_locations(img, model=self.MODEL)
            # creates an encoding for the image
            encoded_ = face_recognition.face_encodings(img, identifier)
            for face_encoding, face_location in zip(encoded_, identifier):
                # using learning_rate, the encoding is matched against the encoded matrix for images in named directory
                results = face_recognition.compare_faces(
                    self.train_faces, face_encoding, self.LEARNING_RATE
                )
                # if a match is found the directory name is rendered and returned as match value
                if True in results:
                    return self.train_names[results.index(True)]

    def face_detection(
        self,
        retry_count: int = 20,
        mirror: bool = False,
        filename: str = "cv2_open.jpg",
        display: bool = False,
    ) -> bool:
        """Detects faces by converting it to grayscale and neighbor match method.

        Args:
            retry_count: Number of trials to detect a face before the function can quit.
            mirror: Mirrors the live feed vertically.
            filename: Filename under which the detected face has to be stored.
            display: Only displays the live feed instead of saving it to a file.

        Notes:
            Filename should not include the file path but just the name.

        Returns:
            bool:
            A boolean value if not a face was detected.
        """
        logger.debug("Initiating face detection.")
        cv2_cascades = haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.isfile(cv2_cascades):
            logger.debug("Cascades not found at: %s", cv2_cascades)
            raise FileNotFoundError(cv2_cascades)
        cascade = cv2.CascadeClassifier(cv2_cascades)
        for _ in range(retry_count + 1):
            # reads video from web cam
            ret, image = self.validation_video.read()
            if not ret:
                continue
            try:
                # convert the captured image to grayscale
                img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            except cv2.error as error:
                logger.error(error)
                img = image  # proceed without performing grayscale
            scale_factor = (
                1.1  # specify how much the image size is reduced at each image scale
            )
            min_neighbors = 5  # specify how many neighbors each candidate rectangle should have to retain it
            img = cv2.flip(img, 1) if mirror else img
            faces = cascade.detectMultiScale(
                image=img, scaleFactor=scale_factor, minNeighbors=min_neighbors
            )
            if display:
                # Rectangle box around each face
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.imshow("img", img)
                k = cv2.waitKey(30) & 0xFF
                if k == 27:
                    break
                continue
            # Returns an empty tuple when no face is detected, returns a matrix when a face is detected
            if len(faces):
                self.capture_image(filename=filename)
                if os.path.isfile(filename):
                    return True

    def capture_image(self, filename: str = "cv2_open.jpg") -> None:
        """Captures an image and saves it locally.

        Args:
            filename: Name of the file to be saved.
        """
        ret, image = self.validation_video.read()
        if not ret:
            return
        cv2.imwrite(filename=filename, img=image)
        self.validation_video.release()
