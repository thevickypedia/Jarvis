import os
import sys

import cv2
import face_recognition


class Face:
    def __init__(self):
        try:
            self.training_dataset = "train"  # main dir within which training images are placed under named directories
            self.learning_rate = 0.6  # tolerance level - keep switching this until you find perfection in recognition
            self.model = "hog"  # model using which the images are matched
            source = None
            for i in range(0, 3):
                cap = cv2.VideoCapture(i)
                if cap is None or not cap.isOpened():
                    pass
                else:
                    source = i
                    break
            if source is None:
                sys.stdout.write('\rNo cameras were found.')
                raise BlockingIOError
            self.validation_video = cv2.VideoCapture(source)  # camera id - depends on installed camera applications
            self.train_faces, self.train_names = [], []
            for character_dir in os.listdir(self.training_dataset):  # loads the training dataset
                try:
                    for file_name in os.listdir(f'{self.training_dataset}/{character_dir}'):
                        # loads all the files within the named repo
                        img = face_recognition.load_image_file(f'{self.training_dataset}/{character_dir}/{file_name}')
                        encoded = face_recognition.face_encodings(img)[0]  # generates face encoding matrix
                        self.train_faces.append(encoded)  # loads ended values to match
                        self.train_names.append(character_dir)  # loads the names of each named sub directories
                except (IndexError, NotADirectoryError):
                    pass
        except FileNotFoundError:  # passes if "train" directory was not found
            pass

    def face_recognition(self):
        for _ in range(20):
            ret, img = self.validation_video.read()  # reads video from web cam
            identifier = face_recognition.face_locations(img, model=self.model)  # gets image from the video read above
            encoded_ = face_recognition.face_encodings(img, identifier)  # creates an encoding for the image
            for face_encoding, face_location in zip(encoded_, identifier):
                # using learning_rate, the encoding is matched against the encoded matrix for images in named directory
                results = face_recognition.compare_faces(self.train_faces, face_encoding, self.learning_rate)
                if True in results:  # if a match is found the directory name is rendered and returned as match value
                    match = self.train_names[results.index(True)]
                    return match

    def face_detection(self):
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        for _ in range(20):
            ignore, image = self.validation_video.read()  # reads video from web cam
            scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # convert the captured image to grayscale
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
                cv2.imwrite('cv2_open.jpg', image)
                self.validation_video.release()
                return True


if __name__ == '__main__':
    sys.stdout.write(Face().face_recognition())
