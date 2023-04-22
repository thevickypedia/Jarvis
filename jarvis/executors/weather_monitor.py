import os
import string
from datetime import datetime

from jarvis.executors import communicator, weather
from jarvis.modules.logger import config, custom_logger
from jarvis.modules.models import models


def monitor() -> None:
    """Weather monitoring system to trigger notifications for high, low weather and severe weather alert."""
    logger = custom_logger.logger
    config.multiprocessing_logger(filename=os.path.join('logs', 'background_tasks_%d-%m-%Y.log'))
    low_threshold = 36
    high_threshold = 100
    condition, high, low, temp_f, alert = weather.weather(monitor=True)
    if not any((high >= high_threshold, low <= low_threshold, alert)):
        logger.info(dict(condition=condition, high=high, low=low, temperature=temp_f, alert=alert))
        logger.info("No alerts to report")
        return
    title = "Weather Alert"
    sender = "Jarvis Weather Alert System"
    subject = title + " " + datetime.now().strftime('%c')
    body = f"Highest Temperature: {high}\N{DEGREE SIGN}F\n" \
           f"Lowest Temperature: {low}\N{DEGREE SIGN}F\n" \
           f"Current Temperature: {temp_f}\N{DEGREE SIGN}F\n" \
           f"Current Condition: {string.capwords(condition)}"
    email_args = dict(body=body, recipient=models.env.recipient, subject=subject, sender=sender, title=title,
                      gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
    phone_args = dict(user=models.env.open_gmail_user, password=models.env.open_gmail_pass,
                      body=body, number=models.env.phone_number, subject=subject)
    if high >= high_threshold:
        if alert:
            email_args['body'] = f"High weather alert!\n{alert}\n\n" + email_args['body']
            phone_args['body'] = f"High weather alert!\n{alert}\n\n" + phone_args['body']
        else:
            email_args['body'] = "High weather alert!\n" + email_args['body']
            phone_args['body'] = "High weather alert!\n" + phone_args['body']
        logger.info("high temperature alert")
        email_args['body'] = email_args['body'].replace('\n', '<br>')
        communicator.send_email(**email_args)
        communicator.send_sms(**phone_args)
        return
    if low <= low_threshold:
        if alert:
            email_args['body'] = f"Low weather alert!\n{alert}\n\n" + email_args['body']
            phone_args['body'] = f"Low weather alert!\n{alert}\n\n" + phone_args['body']
        else:
            email_args['body'] = "Low weather alert!\n" + email_args['body']
            phone_args['body'] = "Low weather alert!\n" + phone_args['body']
        logger.info("low temperature alert")
        email_args['body'] = email_args['body'].replace('\n', '<br>')
        communicator.send_email(**email_args)
        communicator.send_sms(**phone_args)
        return
    if alert:
        email_args['body'] = f"Critical weather alert!\n{alert}\n\n" + email_args['body']
        phone_args['body'] = "Critical weather alert!\n" + phone_args['body']
        logger.info("critical weather alert")
        email_args['body'] = email_args['body'].replace('\n', '<br>')
        communicator.send_email(**email_args)
        communicator.send_sms(**phone_args)
        return
