from multiprocessing import Queue
from typing import ByteString, List, NoReturn

import cv2

from api.settings import surveillance
from modules.camera.camera import Camera
from modules.exceptions import CameraError
from modules.logger import config
from modules.logger.custom_logger import logger

config.multiprocessing_logger(filename=config.APIConfig().DEFAULT_LOG_FILENAME)


def test_camera() -> NoReturn:
    """Tests a camera connected on the index number provided by the user."""
    camera_object = Camera()
    available_cameras = camera_object.list_cameras()

    if not available_cameras:
        raise CameraError("No available cameras to monitor.")

    if surveillance.camera_index is None \
            or surveillance.camera_index == "" \
            or not str(surveillance.camera_index).isdigit():  # Initial value is string while calls will be integer
        logger.info(f"Camera index received: {surveillance.camera_index}")
        logger.info(f"Available cameras: {available_cameras}")
        raise CameraError(f"Available cameras:\n{camera_object.get_index()}")

    surveillance.camera_index = int(surveillance.camera_index)

    if surveillance.camera_index >= len(available_cameras):
        logger.info(f"Available cameras: {available_cameras}")
        raise CameraError(f"Camera index [{surveillance.camera_index}] is out of range.\n\n"
                          f"Available cameras:\n{camera_object.get_index()}")
    camera = cv2.VideoCapture(surveillance.camera_index)
    if camera is None or not camera.isOpened() or camera.read() == (False, None):
        raise CameraError(f"Unable to read the camera index [{surveillance.camera_index}] - "
                          f"{available_cameras[surveillance.camera_index]}")

    if camera.isOpened():
        camera.release()
    logger.info(f"{available_cameras[surveillance.camera_index]} is ready to use.")
    surveillance.available_cameras = available_cameras


def gen_frames(manager: Queue, index: int, available_cameras: List[str]) -> NoReturn:
    """Generates frames from the camera, flips the image and stores the frame in a multiprocessing queue.

    Args:
        manager: Multiprocessing queues.
        index: Index of the camera.
        available_cameras: List of available cameras.
    """
    camera = cv2.VideoCapture(index)
    logger.info(f"Capturing frames from {available_cameras[index]}")
    while True:
        success, frame = camera.read()
        frame = cv2.flip(src=frame, flipCode=1)  # mirrors the frame
        if not success:  # TODO: Test with if success to check behavior
            logger.error(f"Failed to capture frames from [{index}]: "
                         f"{available_cameras[index]}")
            logger.info(f"Releasing camera: {available_cameras[index]}")
            camera.release()
            raise CameraError(f"Failed to capture frames from [{index}]: "
                              f"{available_cameras[index]}")
        ret, buffer = cv2.imencode(ext='.jpg', img=frame)
        frame = buffer.tobytes()
        manager.put(frame)


def streamer() -> ByteString:
    """Yields bytes string extracted from the multiprocessing queue, until the queue_manager is alive.

    Yields:
        ByteString:
        Concat frame one by one and yield the result.

    Warnings:
        - | When pushing large items onto the queue, the items are essentially buffered, despite the immediate return
          | of the queue’s put function. This causes a delay of whopping ~20 seconds during live feed.
    """
    # TODO: Optimize queue utilization.
    try:
        while surveillance.queue_manager:
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(surveillance.queue_manager.get()) + b'\r\n'
    except GeneratorExit as error:
        logger.error(error)
