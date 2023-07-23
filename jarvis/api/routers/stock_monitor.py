import secrets
import string
from datetime import datetime
from http import HTTPStatus
from threading import Timer
from typing import Optional

import gmailconnector
import jinja2
import jwt
from fastapi import APIRouter, Header, Request
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


async def send_otp_stock_monitor(email_address: EmailStr, reset_timeout: int = 300):
    """Send one time password via email.

    Args:

        email_address: Email address to which the token has to be sent.
        reset_timeout: Seconds after which the token has to expire.

    Raises:

        - 200: If email delivery was successful.
        - 503: If failed to send an email.
    """
    mail_obj = gmailconnector.SendEmail(gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
    logger.info("Sending stock monitor token as OTP")
    stock_monitor_helper.otp_sent[email_address] = util.keygen_uuid(length=16)
    rendered = jinja2.Template(templates.email.one_time_passcode).render(
        TIMEOUT=support.pluralize(count=util.format_nos(input_=reset_timeout / 60), word="minute"),
        TOKEN=stock_monitor_helper.otp_sent[email_address], EMAIL=email_address,
        ENDPOINT="https://vigneshrao.com/stock-monitor"
    )
    mail_stat = mail_obj.send_email(recipient=email_address, sender='Jarvis API',
                                    subject=f"Stock Monitor - {datetime.now().strftime('%c')}",
                                    html_body=rendered)
    if mail_stat.ok:
        logger.debug(mail_stat.body)
        logger.info("Token will be reset in %s." %
                    support.pluralize(count=util.format_nos(input_=reset_timeout / 60), word='minute'))
        Timer(function=timeout_otp.reset_stock_monitor, args=(email_address,), interval=reset_timeout).start()
        raise APIResponse(status_code=HTTPStatus.OK.real,
                          detail="Please enter the OTP sent via email to verify email address:")
    else:
        logger.error(mail_stat.json())
        raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real, detail=mail_stat.body)


@router.post(path="/stock-monitor")
async def stock_monitor_api(request: Request, input_data: StockMonitorModal,
                            email_otp: Optional[str] = Header(None), apikey: Optional[str] = Header(None)):
    """`Stock monitor api endpoint <https://vigneshrao.com/stock-monitor>`__.

    Args:

        - request: Takes the Request class as an argument.
        - input_data: Takes the following arguments as OfflineCommunicatorModal class instead of a QueryString.
        - email_otp: One Time Passcode (OTP) received via email.

            - token: Authentication token.
            - email: Email to which the notifications have to be triggered.
            - request: Request type. Takes any of GET/PUT/DELETE
            - plaintext: Takes a boolean flag if a plain text response is expected for GET request.

    See Also:

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
    logger.debug("Connection received from %s via %s using %s" %
                 (request.client.host, request.headers.get('host'), request.headers.get('user-agent')))

    input_data.request = input_data.request.upper()
    if input_data.request not in ("GET", "PUT", "DELETE"):
        logger.warning("'%s' is not in the allowed request list.", input_data.request)
        raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real,
                          detail=HTTPStatus.UNPROCESSABLE_ENTITY.phrase)

    # apikey from user and env vars are present and it is allowed
    apikey = apikey or request.headers.get('apikey')
    if apikey and \
            models.env.stock_monitor_api.get(input_data.email) and \
            secrets.compare_digest(models.env.stock_monitor_api[input_data.email], apikey):
        logger.info("%s has been verified using apikey", input_data.email)
    elif apikey and models.env.stock_monitor_api.get(input_data.email):  # both vars are present but don't match
        logger.info("%s sent an invalid API key", input_data.email)
        raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.phrase)
    else:  # If apikey auth fails or unsupported
        sent_dict = stock_monitor_helper.otp_sent
        recd_dict = stock_monitor_helper.otp_recd
        email_otp = email_otp or request.headers.get('email-otp')  # variable will be _ but headers should always be `-`
        if email_otp:
            recd_dict[input_data.email] = email_otp
        if secrets.compare_digest(recd_dict.get(input_data.email, 'DO_NOT'), sent_dict.get(input_data.email, 'MATCH')):
            logger.info("%s has been verified.", input_data.email)
        else:
            result = gmailconnector.validate_email(email_address=input_data.email, smtp_check=False)
            logger.debug(result.body)
            if result.ok is False:
                raise APIResponse(status_code=HTTPStatus.UNPROCESSABLE_ENTITY.real, detail=result.body)
            await send_otp_stock_monitor(email_address=input_data.email)

    if input_data.request == "GET":
        logger.info("'%s' requested their data.", input_data.email)
        # Token is not required for GET method
        # if input_data.token:
        #     decoded = jwt.decode(jwt=input_data.token, options={"verify_signature": False}, algorithms="HS256")
        #     logger.warning("Unwanted information received: '%s'", decoded)
        if db_entry := stockmonitor_squire.get_stock_userdata(email=input_data.email):  # Filter data from DB by email
            logger.info(db_entry)
            if input_data.plaintext:
                raise APIResponse(status_code=HTTPStatus.OK.real,
                                  detail=[dict(zip(stock_monitor.user_info, each_entry)) for each_entry in db_entry])
            # Format as an HTML table to serve in https://vigneshrao.com/stock-monitor
            # This is a mess, yet required because JavaScript can't handle dataframes and
            # pandas to html can't include custom buttons
            html_data = """<table border="1" class="dataframe" id="dataframe"><tbody><tr><td><b>Selector</b></td>"""
            html_data += "<td><b>" + "</b></td><td><b>".join((string.capwords(p)
                                                              for p in stock_monitor.user_info)) + "</b></td></tr>"
            rows = ""
            for ind, each_entry in enumerate(db_entry):
                # give same name to all the radio buttons to enable single select
                row = f'<tr><td align="center"><input value="{ind}" id="radio_{ind}" type="radio" name="read"></td><td>'
                row += "</td><td>".join(str(i) for i in each_entry) + "</td>"
                rows += row
            html_data += rows + "</tr></tbody></table>"
            raise APIResponse(status_code=HTTPStatus.OK.real, detail=html_data)
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

    # Forms a tuple of the new entry provided by the user
    new_entry = (str(decoded['Ticker']), input_data.email, float(decoded['Max']), float(decoded['Min']),
                 int(decoded['Correction']),)

    # Deletes an entry that's present already when requested
    if input_data.request == "DELETE":
        logger.info("'%s' requested to delete '%s'", input_data.email, new_entry)
        if new_entry not in stockmonitor_squire.get_stock_userdata(email=input_data.email):  # Checks if entry exists
            raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail="Entry is not present in the database.")
        stockmonitor_squire.delete_stock_userdata(data=new_entry)
        raise APIResponse(status_code=HTTPStatus.OK.real, detail="Entry has been removed from the database.")

    # Check dupes and let know the user
    if new_entry in stockmonitor_squire.get_stock_userdata():
        raise APIResponse(status_code=HTTPStatus.CONFLICT.real, detail="Duplicate request!\nEntry exists in database.")

    logger.info("'%s' requested to add '%s'", input_data.email, new_entry)
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
                          detail=f"Failed to perform a price check on {decoded['Ticker']}\n\n{error.__str__()}")
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
