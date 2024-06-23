import base64
import string
from multiprocessing import Queue
from typing import AsyncIterable, List, Tuple

import cv2
import numpy as np

from jarvis.api.logger import logger
from jarvis.api.models import settings
from jarvis.modules.camera import camera
from jarvis.modules.exceptions import CameraError


def generate_error_frame(
    text: str, dimension: Tuple[int, int, int]
) -> Tuple[bytes, str]:
    """Generates a single frame for error image.

    Args:
        text: Text that should be in the image.
        dimension: Dimension (Height x Width x Channel) of the frame.

    Returns:
        Tuple[bytes, str]:
        Returns a tuple of the numpy array and the filename.

    See Also:
        - Creates a black image.
        - Gets coordinates based on boundaries of the text to center the text in image.
    """
    image = np.zeros(dimension, np.uint8)

    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1  # this value can be from 0 to 1 (0,1] to change the size of the text relative to the image
    font_color = (255, 255, 255)
    thickness = 1

    line_type = 2
    text_size = cv2.getTextSize(text, font, 1, 2)[0]

    text_x = int((image.shape[1] - text_size[0]) / 2)
    text_y = int((image.shape[0] + text_size[1]) / 2)

    cv2.putText(
        img=image,
        text=text,
        org=(text_x, text_y),
        fontFace=font,
        fontScale=font_scale,
        color=font_color,
        thickness=thickness,
        lineType=line_type,
    )
    filename = text.translate(str.maketrans("", "", string.punctuation)).lower()
    filename = filename.replace(" ", "_") + ".jpg"
    cv2.imwrite(filename=filename, img=image)
    with open(filename, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string, filename


def test_camera() -> None:
    """Tests a camera connected on the index number provided by the user.

    Raises:
        CameraError:
        If unable to connect to the camera.
    """
    camera_object = camera.Camera()
    available_cameras = camera_object.list_cameras()

    if not available_cameras:
        raise CameraError("No available cameras to monitor.")

    # Initial value is str but requests will be int
    if (
        settings.surveillance.camera_index is None
        or settings.surveillance.camera_index == ""
        or not str(settings.surveillance.camera_index).isdigit()
    ):
        logger.info("Camera index received: %s", settings.surveillance.camera_index)
        logger.info("Available cameras: %s", available_cameras)
        raise CameraError(f"Available cameras:\n{camera_object.get_index()}")

    settings.surveillance.camera_index = int(settings.surveillance.camera_index)

    if settings.surveillance.camera_index >= len(available_cameras):
        logger.info("Available cameras: %s", available_cameras)
        raise CameraError(
            f"Camera index [{settings.surveillance.camera_index}] is out of range.\n\n"
            f"Available cameras:\n{camera_object.get_index()}"
        )
    cam = cv2.VideoCapture(settings.surveillance.camera_index)
    error = CameraError(
        f"Unable to read the camera index [{settings.surveillance.camera_index}] - "
        f"{available_cameras[settings.surveillance.camera_index]}"
    )
    if cam is None or not cam.isOpened():
        raise error
    success, frame = cam.read()
    if not success:
        raise error
    settings.surveillance.frame = frame.shape
    if cam.isOpened():
        cam.release()
    logger.info(
        "%s is ready to use.", available_cameras[settings.surveillance.camera_index]
    )
    settings.surveillance.available_cameras = available_cameras


def gen_frames(manager: Queue, index: int, available_cameras: List[str]) -> None:
    """Generates frames from the camera, flips the image and stores the frame in a multiprocessing queue.

    Args:
        manager: Multiprocessing queues.
        index: Index of the camera.
        available_cameras: List of available cameras.
    """
    cam = cv2.VideoCapture(index)
    logger.info("Capturing frames from %s", available_cameras[index])
    while True:
        success, frame = cam.read()
        if not success:
            logger.error(
                "Failed to capture frames from [%d]: %s",
                index,
                available_cameras[index],
            )
            logger.info("Releasing camera: %s", available_cameras[index])
            cam.release()
            break
        # mirrors the frame
        frame = cv2.flip(src=frame, flipCode=1)
        ret, buffer = cv2.imencode(ext=".jpg", img=frame)
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
    queue = settings.surveillance.queue_manager[settings.surveillance.client_id]
    try:
        while queue:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + bytearray(
                queue.get()
            ) + b"\r\n"
    except (GeneratorExit, EOFError) as error:
        logger.error(error)
