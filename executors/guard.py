import os
import sys
import time
from datetime import datetime
from threading import Thread
from typing import NoReturn, Union

import cv2
from gmailconnector.send_email import SendEmail

from executors import communicator
from executors.logger import logger
from modules.audio import listener, speaker
from modules.conditions import keywords
from modules.models import models
from modules.utils import support

env = models.env


def guard_enable() -> None:
    """Security Mode will enable camera and microphone in the background.

    Notes:
        - If any speech is recognized or a face is detected, there will another thread triggered to send notifications.
        - Notifications will be triggered only after 5 minutes of previous notification.
    """
    logger.info('Enabled Security Mode')
    speaker.speak(text=f"Enabled security mode {env.title}! I will look out for potential threats and keep you posted. "
                       f"Have a nice {support.part_of_day()}, and enjoy yourself {env.title}!", run=True)

    cam_source, cam = None, None
    for i in range(0, 3):
        cam = cv2.VideoCapture(i)  # tries thrice to choose the camera for which Jarvis has access
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            pass
        else:
            cam_source = i  # source for security cam is chosen
            cam.release()
            break
    if cam_source is None:
        cam_error = 'Guarding mode disabled as I was unable to access any of the cameras.'
        logger.error(cam_error)
        communicator.notify(user=env.gmail_user, password=env.gmail_pass, number=env.phone_number, body=cam_error,
                            subject="IMPORTANT::Guardian mode faced an exception.")
        return

    scale_factor = 1.1  # Parameter specifying how much the image size is reduced at each image scale.
    min_neighbors = 5  # Parameter specifying how many neighbors each candidate rectangle should have, to retain it.
    notified, date_extn, converted = None, None, None

    while True:
        # Listens for any recognizable speech and saves it to a notes file
        sys.stdout.write("\rSECURITY MODE")
        converted = listener.listen(timeout=3, phrase_limit=10, sound=False)
        if converted == 'SR_ERROR':
            continue

        if converted and any(word.lower() in converted.lower() for word in keywords.guard_disable):
            speaker.speak(text=f'Welcome back {env.title}! Good {support.part_of_day()}.')
            if os.path.exists(f'threat/{date_extn}.jpg'):
                speaker.speak(text=f"We had a potential threat {env.title}! Please check your email to confirm.")
            speaker.speak(run=True)
            logger.info('Disabled security mode')
            sys.stdout.write('\rDisabled Security Mode')
            break
        elif converted:
            logger.info(f'Conversation::{converted}')

        if cam_source is not None:
            # Capture images and keeps storing it to a folder
            validation_video = cv2.VideoCapture(cam_source)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            ignore, image = validation_video.read()
            scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(scale, scale_factor, min_neighbors)
            date_extn = f"{datetime.now().strftime('%B_%d_%Y_%I_%M_%S_%p')}"
            try:
                if faces:
                    pass
            except ValueError:
                # log level set to critical because this is a known exception when try check 'if faces'
                cv2.imwrite(f'threat/{date_extn}.jpg', image)
                logger.info(f'Image of detected face stored as {date_extn}.jpg')

        if not os.path.exists(f'threat/{date_extn}.jpg'):
            date_extn = None

        # if no notification was sent yet or if a phrase or face is detected notification thread will be triggered
        if (not notified or float(time.time() - notified) > 300) and (converted or date_extn):
            notified = time.time()
            Thread(target=threat_notify, kwargs=({"converted": converted, "phone_number": env.phone_number,
                                                  "gmail_user": env.gmail_user, "gmail_pass": env.gmail_pass,
                                                  "recipient": env.recipient or env.alt_gmail_user or env.gmail_user,
                                                  "date_extn": date_extn})).start()


def threat_notify(converted: str, date_extn: Union[str, None], gmail_user: str, gmail_pass: str,
                  phone_number: str, recipient: str) -> NoReturn:
    """Sends an SMS and email notification in case of a threat.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS and email.

    Args:
        converted: Takes the voice recognized statement as argument.
        date_extn: Name of the attachment file which is the picture of the intruder.
        gmail_user: Email address for the gmail account.
        gmail_pass: Password of the gmail account.
        phone_number: Phone number to send SMS.
        recipient: Email address of the recipient.
    """
    dt_string = f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    title_ = f'Intruder Alert on {dt_string}'

    if converted:
        communicator.notify(user=gmail_user, password=gmail_pass, number=phone_number, subject="!!INTRUDER ALERT!!",
                            body=f"{dt_string}\n{converted}")
        body_ = f"""<html><head></head><body><h2>Conversation of Intruder:</h2><br>{converted}<br><br>
                                    <h2>Attached is a photo of the intruder.</h2>"""
    else:
        communicator.notify(user=gmail_user, password=gmail_pass, number=phone_number, subject="!!INTRUDER ALERT!!",
                            body=f"{dt_string}\nCheck your email for more information.")
        body_ = """<html><head></head><body><h2>No conversation was recorded,
                                but attached is a photo of the intruder.</h2>"""
    if date_extn:
        attachment_ = f'threat/{date_extn}.jpg'
        response_ = SendEmail(gmail_user=gmail_user, gmail_pass=gmail_pass,
                              recipient=recipient, subject=title_, body=body_, attachment=attachment_).send_email()
        if response_.ok:
            logger.info('Email has been sent!')
        else:
            logger.error(f"Email dispatch failed with response: {response_.body}\n")
