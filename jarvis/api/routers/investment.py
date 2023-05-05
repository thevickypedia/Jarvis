import mimetypes
import os
import secrets
from datetime import datetime
from http import HTTPStatus
from threading import Timer

import gmailconnector
import jinja2
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from jarvis.api.modals.authenticator import ROBINHOOD_PROTECTOR
from jarvis.api.modals.settings import robinhood
from jarvis.api.squire import timeout_otp
from jarvis.api.squire.logger import logger
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import util

router = APIRouter()

# Conditional endpoint: Condition matches without env vars during docs generation
if os.environ.get('pre_commit') or all([models.env.robinhood_user, models.env.robinhood_pass,
                                        models.env.robinhood_pass, models.env.robinhood_endpoint_auth]):
    @router.post(path="/robinhood-authenticate", dependencies=ROBINHOOD_PROTECTOR)
    async def authenticate_robinhood():
        """Authenticates the request and generates single use token.

        Raises:

            APIResponse:
            - 200: If initial auth is successful and single use token is successfully sent via email.
            - 503: If failed to send the single use token via email.

        See Also:

            If basic auth (stored as an env var robinhood_endpoint_auth) succeeds:

            - Sends a token for MFA via email.
            - Also stores the token in the Robinhood object which is verified in the /investment endpoint.
            - The token is nullified in the object as soon as it is verified, making it single use.
        """
        mail_obj = gmailconnector.SendEmail(gmail_user=models.env.open_gmail_user,
                                            gmail_pass=models.env.open_gmail_pass)
        auth_stat = mail_obj.authenticate
        if not auth_stat.ok:
            raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real, detail=auth_stat.body)
        robinhood.token = util.keygen_uuid(length=16)
        rendered = jinja2.Template(templates.email.one_time_passcode).render(ENDPOINT="'robinhood' endpoint",
                                                                             TOKEN=robinhood.token,
                                                                             EMAIL=models.env.recipient)
        mail_stat = mail_obj.send_email(recipient=models.env.recipient, sender='Jarvis API',
                                        subject=f"Robinhood Token - {datetime.now().strftime('%c')}",
                                        html_body=rendered)
        if mail_stat.ok:
            logger.debug(mail_stat.body)
            logger.info("Token will be reset in 5 minutes.")
            Timer(function=timeout_otp.reset_robinhood, interval=300).start()
            raise APIResponse(status_code=HTTPStatus.OK.real,
                              detail="Authentication success. Please enter the OTP sent via email:")
        else:
            logger.error(mail_stat.json())
            raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real, detail=mail_stat.body)

# Conditional endpoint: Condition matches without env vars during docs generation
if os.environ.get('pre_commit') or all([models.env.robinhood_user, models.env.robinhood_pass,
                                        models.env.robinhood_pass, models.env.robinhood_endpoint_auth]):
    @router.get(path="/investment", response_class=HTMLResponse)
    async def robinhood_path(request: Request, token: str = None):
        """Serves static file.

        Args:

            - request: Takes the Request class as an argument.
            - token: Takes custom auth token as an argument.

        Raises:

            APIResponse:
            - 403: If token is null.
            - 404: If the HTML file is not found.
            - 417: If token doesn't match the auto-generated value.

        Returns:

            HTMLResponse:
            Renders the html page.

        See Also:

            - This endpoint is secured behind single use token sent via email as MFA (Multi-Factor Authentication)
            - Initial check is done by the function authenticate_robinhood behind the path "/robinhood-authenticate"
            - Once the auth succeeds, a one-time usable hex-uuid is generated and stored in the Robinhood object.
            - This UUID is sent via email to the env var RECIPIENT, which should be entered as query string.
            - The UUID is deleted from the object as soon as the argument is checked for the first time.
            - Page refresh is useless because the value in memory is cleared as soon as it is authed once.
        """
        logger.debug("Connection received from %s via %s using %s" %
                     (request.client.host, request.headers.get('host'), request.headers.get('user-agent')))

        if not token:
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.phrase)
        # token might be present because its added as headers but robinhood.token will be cleared after one time auth
        if robinhood.token and secrets.compare_digest(token, robinhood.token):
            robinhood.token = None
            if not os.path.isfile(models.fileio.robinhood):
                raise APIResponse(status_code=HTTPStatus.NOT_FOUND.real, detail='Static file was not found on server.')
            with open(models.fileio.robinhood) as static_file:
                html_content = static_file.read()
            content_type, _ = mimetypes.guess_type(html_content)
            return HTMLResponse(status_code=HTTPStatus.TEMPORARY_REDIRECT.real,
                                content=html_content, media_type=content_type)  # serves as a static webpage
        else:
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')
