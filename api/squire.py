import base64
import logging
import os
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import Queue
from typing import (ByteString, Callable, Iterable, List, NoReturn, Optional,
                    Tuple, Union)

import cv2
import numpy
import requests
import yaml
from bs4 import BeautifulSoup
from pydantic import EmailStr
from webull import webull

from api.settings import stock_monitor, surveillance
from modules.camera.camera import Camera
from modules.database import database
from modules.exceptions import CameraError
from modules.logger import config
from modules.logger.custom_logger import logger
from modules.models import models

api_config = config.APIConfig()
config.multiprocessing_logger(filename=api_config.DEFAULT_LOG_FILENAME,
                              log_format=logging.Formatter(api_config.DEFAULT_LOG_FORMAT))
stock_db = database.Database(database=models.fileio.stock_db)


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
        if not success:
            logger.error(f"Failed to capture frames from [{index}]: {available_cameras[index]}")
            logger.info(f"Releasing camera: {available_cameras[index]}")
            camera.release()
            break
        frame = cv2.flip(src=frame, flipCode=1)  # mirrors the frame
        ret, buffer = cv2.imencode(ext='.jpg', img=frame)
        frame = buffer.tobytes()
        manager.put(frame)


def streamer() -> Iterable[ByteString]:
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


def ticker_gatherer(character: str) -> NoReturn:
    """Gathers the stock ticker in NASDAQ. Runs on ``multi-threading`` which drops run time by ~7 times.

    Args:
        character: ASCII character (alphabet) with which the stock ticker name starts.
    """
    url = f'https://www.eoddata.com/stocklist/NASDAQ/{character}.htm'
    response = requests.get(url=url)
    scrapped = BeautifulSoup(response.text, "html.parser")
    d1 = scrapped.find_all('tr', {'class': 'ro'})
    d2 = scrapped.find_all('tr', {'class': 're'})
    for link in d1:
        stock_monitor.stock_list.append(f"{(link.get('onclick').split('/')[-1]).split('.')[0]}")
    for link in d2:
        stock_monitor.stock_list.append(f"{(link.get('onclick').split('/')[-1]).split('.')[0]}")


def thread_worker(function_to_call: Callable, iterable: Union[List, Iterable], workers: int = None) -> NoReturn:
    """Initiates ``ThreadPoolExecutor`` with in a dedicated thread.

    Args:
        function_to_call: Takes the function/method that has to be called as an argument.
        iterable: List or iterable to be used as args.
        workers: Maximum number of workers to be spun up.
    """
    if not workers:
        workers = len(iterable)

    futures = {}
    executor = ThreadPoolExecutor(max_workers=workers)
    with executor:
        for iterator in iterable:
            future = executor.submit(function_to_call, iterator)
            futures[future] = iterator

    thread_except = 0
    for future in as_completed(futures):
        if future.exception():
            thread_except += 1
            logger.error(f'Thread processing for {iterator} received an exception: {future.exception()}')
    if thread_except > (len(iterable) * 10 / 100):  # Use backup file if more than 10% of the requests fail
        with open(models.fileio.stock_list_backup) as file:
            stock_monitor.stock_list = yaml.load(stream=file, Loader=yaml.FullLoader)


def nasdaq() -> NoReturn:
    """Get all stock tickers available. Creates/Updates backup file to be used."""
    if os.path.isfile(models.fileio.stock_list_backup):
        modified = int(os.stat(models.fileio.stock_list_backup).st_mtime)
        if int(time.time()) - modified < 86_400:  # Gathers new stock list only if the file is older than a day
            try:
                with open(models.fileio.stock_list_backup) as file:
                    stock_monitor.stock_list = yaml.load(stream=file, Loader=yaml.FullLoader)
            except yaml.YAMLError as error:
                logger.error(error)
            if len(stock_monitor.stock_list) > 5_000:
                logger.info(f"{models.fileio.stock_list_backup} generated on "
                            f"{datetime.fromtimestamp(modified).strftime('%c')} looks re-usable.")
                return
    logger.info("Gathering stock list from webull.")
    try:
        stock_monitor.stock_list = [ticker.get('symbol') for ticker in webull().get_all_tickers()]
    except Exception as error:
        logger.error(error)
    if stock_monitor.stock_list:
        os.remove('did.bin') if os.path.isfile('did.bin') else None  # Created by webull module
    else:
        logger.info("Gathering stock list from eoddata.")
        thread_worker(function_to_call=ticker_gatherer, iterable=string.ascii_uppercase)
    logger.info(f"Total tickers gathered: {len(stock_monitor.stock_list)}")
    # Writes to a backup file
    with open(models.fileio.stock_list_backup, 'w') as file:
        yaml.dump(stream=file, data=stock_monitor.stock_list)


def cleanup_stock_userdata() -> NoReturn:
    """Delete duplicates tuples within the database."""
    data = get_stock_userdata()
    dupes = [x for n, x in enumerate(data) if x in data[:n]]
    if dupes:
        logger.info(f"{len(dupes)} duplicate entries found.")
        cleaned = list(set(data))
        with stock_db.connection:
            cursor = stock_db.connection.cursor()
            cursor.execute("DELETE FROM stock")
            for record in cleaned:
                cursor.execute(f"INSERT or REPLACE INTO stock {stock_monitor.user_info} "
                               f"VALUES {stock_monitor.values};", record)
            stock_db.connection.commit()


def insert_stock_userdata(entry: Tuple[str, EmailStr, Union[int, float], Union[int, float], int]) -> NoReturn:
    """Inserts new entry into the stock database.

    Args:
        entry: Tuple of information that has to be inserted.
    """
    with stock_db.connection:
        cursor = stock_db.connection.cursor()
        cursor.execute(f"INSERT or REPLACE INTO stock {stock_monitor.user_info} VALUES {stock_monitor.values};",
                       entry)
        stock_db.connection.commit()


def get_stock_userdata(email: Optional[Union[EmailStr, str]] = None) -> \
        List[Tuple[str, EmailStr, Union[int, float], Union[int, float], int]]:
    """Reads the stock database to get all the user data.

    Returns:
        list:
        List of tuple of user information.
    """
    with stock_db.connection:
        cursor = stock_db.connection.cursor()
        if email:
            data = cursor.execute("SELECT * FROM stock WHERE email=(?)", (email,)).fetchall()
        else:
            data = cursor.execute("SELECT * FROM stock").fetchall()
    return data


def delete_stock_userdata(data: Tuple[str, EmailStr, Union[int, float], Union[int, float], int]) -> NoReturn:
    """Delete particular user data from stock database.

    Args:
        data: Tuple of user information to be deleted.
    """
    with stock_db.connection:
        cursor = stock_db.connection.cursor()
        cursor.execute("DELETE FROM stock WHERE ticker=(?) AND email=(?) AND max=(?) AND min=(?) AND correction=(?);",
                       data)
        stock_db.connection.commit()
