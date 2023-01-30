import os
import shutil
import sys
import time
import warnings
from datetime import datetime
from multiprocessing import Process
from threading import Thread
from typing import NoReturn, Union

import jinja2
from gmailconnector.send_email import SendEmail

from jarvis.executors import communicator
from jarvis.executors.word_match import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.facenet import face
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import shared, util

db = database.Database(database=models.fileio.base_db)


def get_state(log: bool = True) -> int:
    """Reads the state of guard column in the base db.

    Args:
        log: Boolean flag whether to log state.

    Returns:
        int:
        0 or 1 to indicate if the security mode is enabled.
    """
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT state FROM guard").fetchone()
    if state:
        logger.info("Security mode is currently enabled") if log else None
        return state
    else:
        logger.info("Security mode is currently disabled") if log else None


def put_state(state: bool) -> NoReturn:
    """Updates the state of guard column in the base db.

    Args:
        state: True or False flag to stop the security mode.
    """
    with db.connection:
        cursor = db.connection.cursor()
        if state is True:
            logger.info("Enabling security mode.")
            cursor.execute("INSERT or REPLACE INTO guard (state) VALUES (?);", (1,))
        else:
            logger.info("Disabling security mode.")
            cursor.execute("DELETE FROM guard WHERE state = 1")
        db.connection.commit()
    time.sleep(0.5)


def guard_disable() -> NoReturn:
    """Checks the state of security mode, sets flag to False if currently enabled.

    See Also:
        Informs if a threat was detected during its runtime.
    """
    if get_state():
        put_state(state=False)
        text = f'Welcome back {models.env.title}! Good {util.part_of_day()}.'
        if [file for file in os.listdir('threat') if file.endswith('.jpg')]:
            text += f" We had a potential threat {models.env.title}! Please check your email, or the " \
                    "threat directory to confirm."
        speaker.speak(text=text)
    else:
        speaker.speak(text=f"Security mode was never enabled {models.env.title}!")


def security_runner() -> NoReturn:
    """Enables microphone and camera to watch and listen for potential threats. Notifies if any."""
    notified, converted = None, None
    face_object = face.FaceNet()
    while True:
        # Listens for any recognizable speech and saves it to a notes file
        sys.stdout.write("\rSECURITY MODE")
        converted = listener.listen(sound=False)
        face_detected = datetime.now().strftime('%B_%d_%Y_%I_%M_%S_%p.jpg')
        if not get_state(log=False) or word_match(phrase=converted, match_list=keywords.keywords.guard_disable):
            guard_disable()
            break
        elif converted:
            logger.info(f'Conversation::{converted}')
        try:
            recognized = face_object.face_recognition(location=os.path.realpath("train"), retry_count=1)
            if recognized:
                logger.warning(f"Located {recognized!r} when guardian mode was enabled.")
                continue
            if not face_object.face_detection(filename=face_detected, mirror=True):
                face_detected = None
        except Exception as error:  # Catch wide exceptions here to prevent guardian mode from getting disabled
            logger.error(error)
            warnings.warn(error.__str__())
            continue
        if not any((face_detected, converted)):
            continue
        elif face_detected:
            shutil.move(src=face_detected, dst=os.path.join('threat', face_detected))
            face_detected = os.path.join('threat', face_detected)

        # if no notification was sent yet or if a phrase or face is detected notification thread will be triggered
        if not notified or float(time.time() - notified) > 300:
            notified = time.time()
            Thread(target=threat_notify, kwargs=({"converted": converted, "face_detected": face_detected})).start()


def guard_enable() -> NoReturn:
    """Security Mode will enable camera and microphone in the background.

    Notes:
        - If any speech is recognized or a face is detected, there will another thread triggered to send notifications.
        - Notifications will be triggered only after 5 minutes of previous notification.
    """
    if get_state():
        speaker.speak(text=f"Security mode is already active {models.env.title}!")
        return
    if not os.path.isdir('threat'):
        os.mkdir('threat')
    logger.info('Enabled Security Mode')
    put_state(state=True)
    speaker.speak(text=f"Enabled security mode {models.env.title}! I will look out for potential threats and keep you "
                       f"posted. Have a nice {util.part_of_day()}, and enjoy yourself {models.env.title}!")
    if shared.called_by_offline:
        process = Process(target=security_runner)
        process.start()
        with db.connection:
            cursor = db.connection.cursor()
            cursor.execute("UPDATE children SET guard=null")
            cursor.execute("INSERT or REPLACE INTO children (guard) VALUES (?);", (process.pid,))
            db.connection.commit()
        return
    speaker.speak(run=True)
    security_runner()


def threat_notify(converted: str, face_detected: Union[str, None]) -> NoReturn:
    """Sends an SMS and email notification in case of a threat.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS and email.

    Args:
        converted: Takes the voice recognized statement as argument.
        face_detected: Name of the attachment file which is the picture of the intruder.
    """
    recipient = models.env.recipient or models.env.alt_gmail_user
    if converted and face_detected:
        communicator.send_sms(user=models.env.gmail_user, password=models.env.gmail_pass,
                              number=models.env.phone_number, subject="!!INTRUDER ALERT!!",
                              body=f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}\nINTRUDER SPOKE: {converted}\n\n"
                                   f"Intruder picture has been sent to {recipient}")
        rendered = jinja2.Template(templates.email.threat_audio).render(CONVERTED=converted)
    elif face_detected:
        communicator.send_sms(user=models.env.gmail_user, password=models.env.gmail_pass,
                              number=models.env.phone_number, subject="!!INTRUDER ALERT!!",
                              body=f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}\n"
                                   "Check your email for more information.")
        rendered = jinja2.Template(templates.email.threat_no_audio).render()
    else:
        logger.warning("Un-processable arguments received.")
        return

    kwargs = {"recipient": recipient,
              "html_body": rendered,
              "subject": f"Intruder Alert on {datetime.now().strftime('%B %d, %Y %I:%M %p')}"}

    if face_detected:
        kwargs["attachment"] = face_detected

    response_ = SendEmail(gmail_user=models.env.gmail_user, gmail_pass=models.env.gmail_pass).send_email(**kwargs)
    if response_.ok:
        logger.info('Email has been sent!')
    else:
        logger.error(f"Email dispatch failed with response: {response_.body}\n")
