import string
from datetime import datetime

from jarvis.executors import communicator, weather
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models


def monitor() -> None:
    """Weather monitoring system to trigger notifications for high, low weather and severe weather alert."""
    condition, high, low, temp_f, alert = weather.weather(monitor=True)
    if not any((high >= 100, low <= 36, alert)):
        logger.info(dict(condition=condition, high=high, low=low, temperature=temp_f, alert=alert))
        logger.info("No alerts to report")
        return
    subject = f"Weather Alert {datetime.now().strftime('%c')}"
    sender = "Jarvis Weather Alert System"
    body = f"Highest Temperature: {high}\N{DEGREE SIGN}F\n" \
           f"Lowest Temperature: {low}\N{DEGREE SIGN}F\n" \
           f"Current Temperature: {temp_f}\N{DEGREE SIGN}F\n" \
           f"Current Condition: {string.capwords(condition)}"
    email_args = dict(body=body, recipient=models.env.recipient, subject=subject, sender=sender,
                      gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
    phone_args = dict(user=models.env.open_gmail_user, password=models.env.open_gmail_pass,
                      body=body, number=models.env.phone_number, subject=subject)
    if high >= 100:
        email_args['title'] = "High weather alert!"
        email_args['body'] = email_args['body'].replace('\n', '<br>')
        logger.info("%s: %s", email_args['title'], email_args['body'])
        communicator.send_email(**email_args)
        phone_args['body'] = "High weather alert!\n" + phone_args['body']
        communicator.send_sms(**phone_args)
        return
    if low <= 36:
        email_args['title'] = "Low weather alert!"
        email_args['body'] = email_args['body'].replace('\n', '<br>')
        logger.info("%s: %s", email_args['title'], email_args['body'])
        communicator.send_email(**email_args)
        phone_args['body'] = "Low weather alert!\n" + phone_args['body']
        communicator.send_sms(**phone_args)
        return
    if alert:
        email_args['title'] = "Critical weather alert!"
        email_args['body'] = email_args['body'].replace('\n', '<br>')
        logger.info("%s: %s", email_args['title'], email_args['body'])
        communicator.send_email(**email_args)
        phone_args['body'] = "Critical weather alert!\n" + phone_args['body']
        communicator.send_sms(**phone_args)
        return
