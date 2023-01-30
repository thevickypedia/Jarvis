from datetime import datetime
from http import HTTPStatus
from threading import Thread
from typing import Optional

import jinja2
import jwt
import pandas
from fastapi import APIRouter, Header, Request
from gmailconnector.send_email import SendEmail
from gmailconnector.validator import validate_email
from pydantic import EmailStr
from webull import webull

from jarvis.api.modals.models import StockMonitorModal
from jarvis.api.modals.settings import stock_monitor, stock_monitor_helper
from jarvis.api.squire import stockmonitor_squire, timeout_otp
from jarvis.api.squire.logger import logger
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import support, util

router = APIRouter()


async def send_otp_stock_monitor(email_address: EmailStr, reset_timeout: int = 60):
    """Send one time password via email.

    Args:

        email_address: Email address to which the token has to be sent.
        reset_timeout: Seconds after which the token has to expire.

    Raises:

        - 200: If email delivery was successful.
        - 503: If failed to send an email.
    """
    mail_obj = SendEmail(gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
    logger.info("Setting stock monitor token")
    stock_monitor_helper.otp_sent[email_address] = util.keygen_uuid(length=16)
    rendered = jinja2.Template(templates.email.stock_monitor_otp).render(
        TIMEOUT=support.pluralize(count=util.format_nos(input_=reset_timeout / 60), word="minute"),
        TOKEN=stock_monitor_helper.otp_sent[email_address], EMAIL=email_address
    )
    mail_stat = mail_obj.send_email(recipient=email_address, sender='Jarvis API',
                                    subject=f"Stock Monitor - {datetime.now().strftime('%c')}",
                                    html_body=rendered)
    if mail_stat.ok:
        logger.debug(mail_stat.body)
        if models.env.debug:  # Why do all the conversions if it's not going to be logged anyway
            logger.debug(f"Token will be reset in "
                         f"{support.pluralize(count=util.format_nos(input_=reset_timeout / 60), word='minute')}.")
        Thread(target=timeout_otp.reset_stock_monitor, args=(email_address, reset_timeout)).start()
        raise APIResponse(status_code=HTTPStatus.OK.real,
                          detail="Please enter the OTP sent via email to verify email address:")
    else:
        logger.error(mail_stat.json())
        raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real, detail=mail_stat.body)


@router.post(path="/stock-monitor")
async def stock_monitor_api(request: Request, input_data: StockMonitorModal,
                            email_otp: Optional[str] = Header(None)):
    """`Stock monitor api endpoint <https://vigneshrao.com/stock-monitor>`__.

    Args:

        - request: Takes the Request class as an argument.
        - input_data: Takes the following arguments as OfflineCommunicatorModal class instead of a QueryString.

            - token: Authentication token.
            - email: Email to which the notifications have to be triggered.
            - request: Request type. Takes any of GET/PUT/DELETE
            - plaintext: Takes a boolean flag if a plain text response is expected for GET request.

        - email_otp: Received as argument when run on localhost, received as http headers when run with JavaScript.

            - token is not required for GET requests.
            - For PUT and DELETE requests, token should be a JWT of the following keys:
                - Ticker: Stock ticker.
                - Max: Max price for notification.
                - Min: Min price for notification.
                - Correction: Correction percentage.
            - Use `https://vigneshrao.com/jwt <https://vigneshrao.com/jwt>`__ for conversion.

    Raises:

        APIResponse:
        - 422: For any invalid entry made by the user.
        - 409: If current price is lesser than the minimum value or grater than the maximum value.
        - 404: If a delete request is made against an entry that is not available in the database.
        - 502: If price check fails.

    See Also:

        - This API endpoint is simply the backend for stock price monitoring.
        - This function validates the user information and stores it to a database.
    """
    logger.debug(f"Connection received from {request.client.host} via {request.headers.get('host')} using "
                 f"{request.headers.get('user-agent')}")

    input_data.request = input_data.request.upper()
    if input_data.request not in ("GET", "PUT", "DELETE"):
        logger.warning(f'{input_data.request!r} is not in the allowed request list.')
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=HTTPStatus.UNPROCESSABLE_ENTITY.__dict__['phrase'])

    sent_dict = stock_monitor_helper.otp_sent
    recd_dict = stock_monitor_helper.otp_recd
    email_otp = email_otp or request.headers.get('email_otp')
    if email_otp:
        recd_dict[input_data.email] = email_otp
    if recd_dict.get(input_data.email, 'DO_NOT') == sent_dict.get(input_data.email, 'MATCH'):
        logger.debug(f"{input_data.email} has been verified.")
    else:
        result = validate_email(email_address=input_data.email, smtp_check=False)
        logger.debug(result.body)
        if result.ok is False:
            raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                              detail=f"{input_data.email.split('@')[-1]!r} doesn't resolve to a valid mail server!")
        await send_otp_stock_monitor(email_address=input_data.email)

    if input_data.request == "GET":
        logger.info(f"{input_data.email!r} requested their data.")
        # Token is not required for GET method
        # if input_data.token:
        #     decoded = jwt.decode(jwt=input_data.token, options={"verify_signature": False}, algorithms="HS256")
        #     logger.warning(f"Unwanted information received: {decoded!r}")
        if data := stockmonitor_squire.get_stock_userdata(email=input_data.email):  # Filter data from DB by email
            data_dict = [dict(zip(stock_monitor.user_info, each_entry)) for each_entry in data]
            logger.info(data_dict)
            if input_data.plaintext:
                raise APIResponse(status_code=HTTPStatus.OK.real, detail=data_dict)
            # Customized UI with HTML and CSS can consume this dataframe into a table, comment it otherwise
            pandas.set_option('display.max_columns', None)
            data_frame = pandas.DataFrame(data=data_dict)
            raise APIResponse(status_code=HTTPStatus.OK.real, detail=data_frame.to_html())
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f"No entry found in database for {input_data.email!r}")

    try:
        decoded = jwt.decode(jwt=input_data.token, options={"verify_signature": False}, algorithms="HS256")
    except jwt.DecodeError as error:
        logger.error(error)
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail="Invalid JWT received. Please re-check the input and try-again.")
    # Validated individually
    # if any(map(lambda x: x is None, (decoded.get('Ticker'), decoded.get('Max'), decoded.get('Min')))):
    #     raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
    #                       detail="Keys 'Ticker', 'Max' and 'Min' are mandatory.")
    if not decoded.get('Ticker'):
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail="Cannot proceed without the key 'Ticker'")
    decoded['Ticker'] = decoded['Ticker'].upper()
    decoded['Max'] = util.extract_nos(input_=decoded['Max'], method=float)
    decoded['Min'] = util.extract_nos(input_=decoded['Min'], method=float)
    decoded['Correction'] = util.extract_nos(input_=decoded['Correction'], method=int)

    if decoded['Correction'] is None:  # Consider 0 as valid in case user doesn't want any correction value
        decoded['Correction'] = 5
    if decoded['Max'] is None or decoded['Min'] is None:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail="Minimum and maximum values should be integers. "
                                 "If you don't want a notification for any one of of it, please mark it as 0.")
    if decoded['Max'] and decoded['Max'] <= decoded['Min']:
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real,
                          detail="'Max' should be greater than the 'Min' value.\n\nSet 'Max' or 'Min' as 0, "
                                 "if you don't wish to receive a notification for it.")
    if decoded['Correction'] > 20:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail="Allowed correction values are only up to 20%\n\nFor anything greater, "
                                 "it is better to increase/decrease the Max/Min values.")

    if decoded['Ticker'] not in stock_monitor.stock_list:
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=f"{decoded['Ticker']!r} not a part of NASDAQ stock list [OR] Jarvis currently doesn't "
                                 f"support tracking prices for {decoded['Ticker']!r}")

    # Forms a tuple of the new entry provided by the user
    new_entry = (str(decoded['Ticker']), input_data.email, float(decoded['Max']), float(decoded['Min']),
                 int(decoded['Correction']),)

    # Deletes an entry that's present already when requested
    if input_data.request == "DELETE":
        logger.info(f"{input_data.email!r} requested to delete {new_entry!r}")
        if new_entry not in stockmonitor_squire.get_stock_userdata(email=input_data.email):  # Checks if entry exists
            raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail="Entry is not present in the database.")
        stockmonitor_squire.delete_stock_userdata(data=new_entry)
        raise APIResponse(status_code=HTTPStatus.OK.real, detail="Entry has been removed from the database.")

    # Check dupes and let know the user
    if new_entry in stockmonitor_squire.get_stock_userdata():
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real, detail="Duplicate request!\nEntry exists in database.")

    logger.info(f"{input_data.email!r} requested to add {new_entry!r}")
    try:
        price_check = webull().get_quote(decoded['Ticker'])
        current_price = price_check.get('close') or price_check.get('open')
        if current_price:
            current_price = float(current_price)
        else:
            raise ValueError(price_check)
    except ValueError as error:
        logger.error(error)
        raise APIResponse(status_code=HTTPStatus.BAD_GATEWAY.real,
                          detail=f"Failed to perform a price check on {decoded['Ticker']}\n\n{error}")
    if decoded['Max'] and current_price >= decoded['Max']:  # Ignore 0 which doesn't trigger a notification
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real,
                          detail=f"Current price of {decoded['Ticker']} is {current_price}.\n"
                                 "Please choose a higher 'Max' value or try at a later time.")
    if decoded['Min'] and current_price <= decoded['Min']:  # Ignore 0 which doesn't trigger a notification
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real,
                          detail=f"Current price of {decoded['Ticker']} is {current_price}.\n"
                                 "Please choose a lower 'Min' value or try at a later time.")

    stockmonitor_squire.insert_stock_userdata(entry=new_entry)  # Store it in database

    raise APIResponse(status_code=HTTPStatus.OK.real,
                      detail=f"Entry added to the database. Jarvis will notify you at {input_data.email!r} when a "
                             f"price change occurs in {decoded['Ticker']!r}.")
