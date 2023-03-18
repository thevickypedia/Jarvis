import base64
import string
from multiprocessing import Queue
from typing import AsyncIterable, List, NoReturn, Tuple

import cv2
import numpy

from jarvis.api.modals.settings import surveillance
from jarvis.api.squire.logger import logger
from jarvis.modules.camera.camera import Camera
from jarvis.modules.exceptions import CameraError


def generate_error_frame(text: str, dimension: Tuple[int, int, int]) -> Tuple[bytes, str]:
    """Generates a single frame for error image.

    Args:
        text: Text that should be in the image.
        dimension: Dimension (Height x Width x Channel) of the frame.

    Returns:
        numpy.ndarray:

    See Also:
        - Creates a black image.
        - Gets coordinates based on boundaries of the text to center the text in image.
    """
    image = numpy.zeros(dimension, numpy.uint8)

    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1  # this value can be from 0 to 1 (0,1] to change the size of the text relative to the image
    font_color = (255, 255, 255)
    thickness = 1

    line_type = 2
    text_size = cv2.getTextSize(text, font, 1, 2)[0]

    text_x = int((image.shape[1] - text_size[0]) / 2)
    text_y = int((image.shape[0] + text_size[1]) / 2)

    cv2.putText(img=image,
                text=text,
                org=(text_x, text_y),
                fontFace=font,
                fontScale=font_scale,
                color=font_color,
                thickness=thickness,
                lineType=line_type)
    filename = text.translate(str.maketrans('', '', string.punctuation)).lower()
    filename = filename.replace(' ', '_') + '.jpg'
    cv2.imwrite(filename=filename, img=image)
    with open(filename, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string, filename


def test_camera() -> NoReturn:
    """Tests a camera connected on the index number provided by the user.

    Raises:
        CameraError:
        If unable to connect to the camera.
    """
    camera_object = Camera()
    available_cameras = camera_object.list_cameras()

    if not available_cameras:
        raise CameraError("No available cameras to monitor.")

    if surveillance.camera_index is None \
            or surveillance.camera_index == "" \
            or not str(surveillance.camera_index).isdigit():  # Initial value is string while calls will be integer
        logger.info("Camera index received: %s", surveillance.camera_index)
        logger.info("Available cameras: %s", available_cameras)
        raise CameraError(f"Available cameras:\n{camera_object.get_index()}")

    surveillance.camera_index = int(surveillance.camera_index)

    if surveillance.camera_index >= len(available_cameras):
        logger.info("Available cameras: %s", available_cameras)
        raise CameraError(f"Camera index [{surveillance.camera_index}] is out of range.\n\n"
                          f"Available cameras:\n{camera_object.get_index()}")
    camera = cv2.VideoCapture(surveillance.camera_index)
    error = CameraError(f"Unable to read the camera index [{surveillance.camera_index}] - "
                        f"{available_cameras[surveillance.camera_index]}")
    if camera is None or not camera.isOpened():
        raise error
    success, frame = camera.read()
    if not success:
        raise error
    surveillance.frame = frame.shape
    if camera.isOpened():
        camera.release()
    logger.info("%s is ready to use.", available_cameras[surveillance.camera_index])
    surveillance.available_cameras = available_cameras


def gen_frames(manager: Queue, index: int, available_cameras: List[str]) -> NoReturn:
    """Generates frames from the camera, flips the image and stores the frame in a multiprocessing queue.

    Args:
        manager: Multiprocessing queues.
        index: Index of the camera.
        available_cameras: List of available cameras.
    """
    camera = cv2.VideoCapture(index)
    logger.info("Capturing frames from %s", available_cameras[index])
    while True:
        success, frame = camera.read()
        if not success:
            logger.error("Failed to capture frames from [%d]: %s", index, available_cameras[index])
            logger.info("Releasing camera: %s", available_cameras[index])
            camera.release()
            break
        frame = cv2.flip(src=frame, flipCode=1)  # mirrors the frame
        ret, buffer = cv2.imencode(ext='.jpg', img=frame)
        frame = buffer.tobytes()
        manager.put(frame)


def streamer() -> AsyncIterable[bytes]:
    """Yields bytes string extracted from the multiprocessing queue, until the queue_manager is alive.

    Yields:
        ByteString:
        Concat frame one by one and yield the result.

    Warnings:
        - | When pushing large items onto a multiprocess queue, the items are essentially buffered, despite the
          | immediate return of the queue’s put function. This may increase the latency during live feed.
    """
    queue = surveillance.queue_manager[surveillance.client_id]
    try:
        while queue:
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(queue.get()) + b'\r\n'
    except (GeneratorExit, EOFError) as error:
        logger.error(error)
