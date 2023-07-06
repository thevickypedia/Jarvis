import os
import shutil
import time
from datetime import datetime
from multiprocessing import Process
from threading import Thread, Timer
from typing import NoReturn, Tuple, Union

import gmailconnector
import jinja2

from jarvis.executors import communicator, word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.facenet import face
from jarvis.modules.logger.config import multiprocessing_logger
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import shared, support, util

db = database.Database(database=models.fileio.base_db)
TRACE = {"status": False}


def get_state(log: bool = True) -> Tuple[int, str]:
    """Reads the state of guard column in the base db.

    Args:
        log: Boolean flag whether to log state.

    Returns:
        int:
        0 or 1 to indicate if the security mode is enabled.
    """
    with db.connection:
        cursor = db.connection.cursor()
        state = cursor.execute("SELECT state, trigger FROM guard").fetchone()
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
            if shared.called_by_offline:
                trigger = "GUARD_OFFLINE"
            else:
                trigger = "GUARD_VOICE"
            logger.info("Enabling security mode.")
            cursor.execute("INSERT or REPLACE INTO guard (state, trigger) VALUES (?,?);", (1, trigger))
        else:
            logger.info("Disabling security mode.")
            cursor.execute("DELETE FROM guard WHERE state = 1")
        db.connection.commit()
    time.sleep(0.5)


def stop_and_respond(stop: bool) -> NoReturn:
    """Stops security mode and responds accordingly.

    Args:
        stop: Boolean flag to stop or simply repsond.
    """
    if stop:
        put_state(state=False)
    text = f'Welcome back {models.env.title}! Good {util.part_of_day()}.'
    if [file for file in os.listdir('threat') if file.endswith('.jpg')]:
        text += f" We had a potential threat {models.env.title}! Please check your email, or the " \
                "threat directory to confirm."
    speaker.speak(text=text)
    new_dir = os.path.join('threat', datetime.now().strftime('%b_%d_%y'))
    if not os.path.isdir(new_dir):
        os.mkdir(new_dir)
    for file in os.listdir('threat'):
        threat_file = os.path.join('threat', file)
        if os.path.isfile(threat_file):
            shutil.move(src=threat_file, dst=os.path.join(new_dir, file))
    speaker.speak(run=True)


def politely_disable() -> NoReturn:
    """Disable security mode in the background without any response."""
    if get_state(log=False):
        logger.debug("Security mode is still enabled.")
        put_state(state=False)


def guard_disable(*args) -> NoReturn:
    """Checks the state of security mode, sets flag to False if currently enabled.

    See Also:
        Informs if a threat was detected during its runtime.
    """
    if state := get_state():
        if state[1] == "GUARD_OFFLINE":  # enabled via offline communicator
            if shared.called_by_offline:  # disabled via offline communicator
                stop_and_respond(stop=True)
            else:
                stop_and_respond(stop=False)
                Timer(interval=3, function=politely_disable).start()
            return
        if state[1] == "GUARD_VOICE":
            if shared.called_by_offline:
                stop_and_respond(stop=False)
                Timer(interval=3, function=politely_disable).start()
            else:
                stop_and_respond(stop=True)
    else:
        if TRACE["status"]:
            TRACE["status"] = False
        else:
            speaker.speak(text=f"Security mode was never enabled {models.env.title}!")


def security_runner(offline: bool = True) -> NoReturn:
    """Enables microphone and camera to watch and listen for potential threats. Notifies if any."""
    if offline:
        multiprocessing_logger(filename=os.path.join('logs', 'guardian_mode_%d-%m-%Y.log'))
    notified, converted = None, None
    face_object = face.FaceNet()
    while True:
        # Listens for any recognizable speech and saves it to a notes file
        support.write_screen(text="SECURITY MODE")
        converted = listener.listen(sound=False)
        face_detected = datetime.now().strftime('%B_%d_%Y_%I_%M_%S_%p.jpg')
        if not get_state(log=False) or word_match.word_match(phrase=converted,
                                                             match_list=keywords.keywords['guard_disable']):
            guard_disable()
            break
        elif converted:
            logger.info("Conversation::%s", converted)
        try:
            if not models.env.debug:  # Skip face recognition when DEBUG mode is enabled
                if recognized := face_object.face_recognition(location=os.path.realpath("train"), retry_count=1):
                    logger.warning("Located '%s' when guardian mode was enabled.", recognized)
                    continue
            if not face_object.face_detection(filename=face_detected, mirror=True):
                face_detected = None
        except Exception as error:  # Catch wide exceptions here to prevent guardian mode from getting disabled
            logger.error(error)
            continue
        if not any((face_detected, converted)):
            continue
        elif face_detected:
            shutil.move(src=face_detected, dst=os.path.join('threat', face_detected))
            face_detected = os.path.join('threat', face_detected)

        # if no notification was sent yet or if a phrase or face is detected notification thread will be triggered
        if not notified or float(time.time() - notified) > 300:
            notified = time.time()
            Thread(target=threat_notify, args=(converted, face_detected,)).start()


def guard_enable(*args) -> NoReturn:
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
        if models.settings.os == models.supported_platforms.linux:
            pname = (models.settings.pname or "offline communicator").replace('_', ' ')
            speaker.speak(text=f"Security mode cannot be enabled via {pname}, as the host "
                               "machine is running on Linux OS")
            return
        process = Process(target=security_runner)
        process.start()
        with db.connection:
            cursor = db.connection.cursor()
            cursor.execute("UPDATE children SET guard=null")
            cursor.execute("INSERT or REPLACE INTO children (guard) VALUES (?);", (process.pid,))
            db.connection.commit()
        return
    TRACE["status"] = True
    speaker.speak(run=True)
    security_runner(offline=False)


def threat_notify(converted: str, face_detected: Union[str, None]) -> NoReturn:
    """Sends an SMS and email notification in case of a threat.

    References:
        Uses `gmail-connector <https://pypi.org/project/gmail-connector/>`__ to send the SMS and email.

    Args:
        converted: Takes the voice recognized statement as argument.
        face_detected: Name of the attachment file which is the picture of the intruder.
    """
    recipient = models.env.recipient or models.env.open_gmail_user
    if converted and face_detected:
        communicator.send_sms(user=models.env.open_gmail_user, password=models.env.open_gmail_pass,
                              number=models.env.phone_number, subject="!!INTRUDER ALERT!!",
                              body=f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}\nINTRUDER SPOKE: {converted}\n\n"
                                   f"Intruder picture has been sent to {recipient}")
        rendered = jinja2.Template(templates.email.threat_image_audio).render(CONVERTED=converted)
    elif face_detected:
        communicator.send_sms(user=models.env.open_gmail_user, password=models.env.open_gmail_pass,
                              number=models.env.phone_number, subject="!!INTRUDER ALERT!!",
                              body=f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}\n"
                                   "Check your email for more information.")
        rendered = jinja2.Template(templates.email.threat_image).render()
    elif converted:
        communicator.send_sms(user=models.env.open_gmail_user, password=models.env.open_gmail_pass,
                              number=models.env.phone_number, subject="!!INTRUDER ALERT!!",
                              body=f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}\n"
                                   "Check your email for more information.")
        rendered = jinja2.Template(templates.email.threat_audio).render(CONVERTED=converted)
    else:
        logger.warning("Un-processable arguments received.")
        return

    kwargs = {"recipient": recipient,
              "html_body": rendered,
              "subject": f"Intruder Alert on {datetime.now().strftime('%B %d, %Y %I:%M %p')}"}

    if face_detected:
        kwargs["attachment"] = face_detected

    response_ = gmailconnector.SendEmail(gmail_user=models.env.open_gmail_user,
                                         gmail_pass=models.env.open_gmail_pass).send_email(**kwargs)
    if response_.ok:
        logger.info('Email has been sent!')
    else:
        logger.error("Email dispatch failed with response: %s", response_.body)
