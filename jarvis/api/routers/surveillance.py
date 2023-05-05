import asyncio
import mimetypes
import os
import secrets
import time
from datetime import datetime
from http import HTTPStatus
from multiprocessing import Process, Queue
from threading import Thread, Timer

import gmailconnector
import jinja2
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse

from jarvis.api.modals.authenticator import SURVEILLANCE_PROTECTOR
from jarvis.api.modals.models import CameraIndexModal
from jarvis.api.modals.settings import (ConnectionManager, stock_monitor,
                                        surveillance)
from jarvis.api.squire import surveillance_squire, timeout_otp
from jarvis.api.squire.logger import logger
from jarvis.modules.database import database
from jarvis.modules.exceptions import APIResponse, CameraError
from jarvis.modules.models import models
from jarvis.modules.templates import templates
from jarvis.modules.utils import support, util

router = APIRouter()
db = database.Database(database=models.fileio.base_db)
stock_db = database.Database(database=models.fileio.stock_db)
stock_db.create_table(table_name="stock", columns=stock_monitor.user_info)

# Get websocket loaded
ws_manager = ConnectionManager()

# Conditional endpoint: Condition matches without env vars during docs generation
if os.environ.get('pre_commit') or models.env.surveillance_endpoint_auth:
    @router.post(path="/surveillance-authenticate", dependencies=SURVEILLANCE_PROTECTOR)
    async def authenticate_surveillance(cam: CameraIndexModal):
        """Tests the given camera index, generates a token for the endpoint to authenticate.

        Args:

            cam: Index number of the chosen camera.

        Raises:

            APIResponse:
            - 200: If initial auth is successful and single use token is successfully sent via email.
            - 503: If failed to send the single use token via email.

        See Also:

            If basic auth (stored as an env var SURVEILLANCE_ENDPOINT_AUTH) succeeds:

            - Sends a token for MFA via email.
            - Also stores the token in the Surveillance object which is verified in the /surveillance endpoint.
            - The token is nullified in the object as soon as it is verified, making it single use.
        """
        surveillance.camera_index = cam.index
        try:
            surveillance_squire.test_camera()
        except CameraError as error:
            logger.error(error)
            raise APIResponse(status_code=HTTPStatus.NOT_ACCEPTABLE.real, detail=str(error))

        mail_obj = gmailconnector.SendEmail(gmail_user=models.env.open_gmail_user,
                                            gmail_pass=models.env.open_gmail_pass)
        auth_stat = mail_obj.authenticate
        if not auth_stat.ok:
            logger.error(auth_stat.json())
            raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real, detail=auth_stat.body)
        surveillance.token = util.keygen_uuid(length=16)
        rendered = jinja2.Template(templates.email.one_time_passcode).render(ENDPOINT="'surveillance' endpoint",
                                                                             TOKEN=surveillance.token,
                                                                             EMAIL=models.env.recipient)
        mail_stat = mail_obj.send_email(recipient=models.env.recipient, sender='Jarvis API',
                                        subject=f"Surveillance Token - {datetime.now().strftime('%c')}",
                                        html_body=rendered)
        if mail_stat.ok:
            logger.debug(mail_stat.body)
            logger.info("Token will be reset in 5 minutes.")
            Timer(function=timeout_otp.reset_surveillance, interval=300).start()
            raise APIResponse(status_code=HTTPStatus.OK.real,
                              detail="Authentication success. Please enter the OTP sent via email:")
        else:
            logger.error(mail_stat.json())
            raise APIResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE.real, detail=mail_stat.body)

# Conditional endpoint: Condition matches without env vars during docs generation
if os.environ.get('pre_commit') or models.env.surveillance_endpoint_auth:
    @router.get('/surveillance')
    async def monitor(token: str = None):
        """Serves the monitor page's frontend after updating it with video origin and websocket origins.

        Args:

            - request: Takes the Request class as an argument.
            - token: Takes custom auth token as an argument.

        Raises:

            APIResponse:
            - 307: If token matches the auto-generated value.
            - 401: If token is null.
            - 417: If token doesn't match the auto-generated value.

        Returns:

            HTMLResponse:
            Renders the html page.

        See Also:

            - This endpoint is secured behind single use token sent via email as MFA (Multi-Factor Authentication)
            - Initial check is done by authenticate_surveillance behind the path "/surveillance-authenticate"
            - Once the auth succeeds, a one-time usable hex-uuid is generated and stored in the Surveillance object.
            - This UUID is sent via email to the env var RECIPIENT, which should be entered as query string.
            - The UUID is deleted from the object as soon as the argument is checked for the last time.
            - Page refresh is useless because the value in memory is cleared as soon as the video is rendered.
        """
        if not token:
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.phrase)
        # token might be present because its added as headers but surveillance.token will be cleared after one time auth
        if surveillance.token and secrets.compare_digest(token, surveillance.token):
            surveillance.client_id = int(''.join(str(time.time()).split('.')))  # include milliseconds to avoid dupes
            rendered = jinja2.Template(templates.endpoint.surveillance).render(CLIENT_ID=surveillance.client_id)
            content_type, _ = mimetypes.guess_type(rendered)
            return HTMLResponse(status_code=HTTPStatus.TEMPORARY_REDIRECT.real,
                                content=rendered, media_type=content_type)
        else:
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')

# Conditional endpoint: Condition matches without env vars during docs generation
if os.environ.get('pre_commit') or models.env.surveillance_endpoint_auth:
    @router.get('/video-feed')
    async def video_feed(request: Request, token: str = None):
        """Authenticates the request, and returns the frames generated as a StreamingResponse.

        Raises:

            APIResponse:
            - 307: If token matches the auto-generated value.
            - 401: If token is null.
            - 417: If token doesn't match the auto-generated value.

        Args:

            - request: Takes the Request class as an argument.
            - token: Token generated in /surveillance-authenticate endpoint to restrict direct access.

        Returns:

            StreamingResponse:
            StreamingResponse with a collective of each frame.
        """
        logger.debug("Connection received from %s via %s using %s" %
                     (request.client.host, request.headers.get('host'), request.headers.get('user-agent')))

        if not token:
            logger.warning('/video-feed was accessed directly.')
            raise APIResponse(status_code=HTTPStatus.UNAUTHORIZED.real,
                              detail=HTTPStatus.UNAUTHORIZED.phrase)
        if token != surveillance.token:
            raise APIResponse(status_code=HTTPStatus.EXPECTATION_FAILED.real,
                              detail='Requires authentication since endpoint uses single-use token.')
        surveillance.token = None
        surveillance.queue_manager[surveillance.client_id] = Queue()
        process = Process(target=surveillance_squire.gen_frames,
                          kwargs={"manager": surveillance.queue_manager[surveillance.client_id],
                                  "index": surveillance.camera_index,
                                  "available_cameras": surveillance.available_cameras})
        process.start()
        # Insert process IDs into the children table to kill it in case, Jarvis is stopped during an active session
        with db.connection:
            cursor = db.connection.cursor()
            cursor.execute("INSERT INTO children (surveillance) VALUES (?);", (process.pid,))
            db.connection.commit()
        surveillance.processes[surveillance.client_id] = process
        return StreamingResponse(content=surveillance_squire.streamer(),
                                 media_type='multipart/x-mixed-replace; boundary=frame',
                                 status_code=HTTPStatus.PARTIAL_CONTENT.real)

# Conditional endpoint: Condition matches without env vars during docs generation
if os.environ.get('pre_commit') or models.env.surveillance_endpoint_auth:
    @router.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: int):
        """Initiates a websocket connection.

        Args:

            websocket: WebSocket.
            client_id: Epoch time generated when each user renders the video file.

        See Also:

            - Websocket checks the frontend and kills the backend process to release the camera if connection is closed.
            - Closing the multiprocessing queue is not required as the backend process will be terminated anyway.

        Notes:

            - Closing queue before process termination will raise ValueError as the process is still updating the queue.
            - Closing queue after process termination will raise EOFError as the queue will not be available to close.
        """
        await ws_manager.connect(websocket)
        try:
            while True:
                try:
                    data = await asyncio.wait_for(fut=websocket.receive_text(), timeout=5)
                except asyncio.TimeoutError:
                    data = None
                if data:
                    logger.info("Client [%d] sent %s", client_id, data)
                    if data == "Healthy":
                        surveillance.session_manager[client_id] = time.time()
                        timestamp = surveillance.session_manager[client_id] + models.env.surveillance_session_timeout
                        logger.info("Surveillance session will expire at %s",
                                    datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))
                    if data == "IMG_ERROR":
                        logger.info("Sending error image frame to client.")
                        bytes_, tmp_file = surveillance_squire.generate_error_frame(
                            dimension=surveillance.frame,
                            text="Unable to get image frame from "
                                 f"{surveillance.available_cameras[surveillance.camera_index]}")
                        await websocket.send_bytes(data=bytes_)
                        Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': tmp_file},
                               daemon=True).start()
                        raise WebSocketDisconnect  # Raise error to release camera after a failed read
                if surveillance.session_manager.get(client_id, time.time()) + \
                        models.env.surveillance_session_timeout <= time.time():
                    logger.info("Sending session timeout to client: %d", client_id)
                    bytes_, tmp_file = surveillance_squire.generate_error_frame(
                        dimension=surveillance.frame,
                        text="SESSION EXPIRED! Re-authenticate to continue live stream.")
                    await websocket.send_bytes(data=bytes_)
                    Thread(target=support.remove_file, kwargs={'delay': 2, 'filepath': tmp_file}, daemon=True).start()
                    raise WebSocketDisconnect  # Raise error to release camera after a failed read
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
            logger.info("Client [%d] disconnected.", client_id)
            if ws_manager.active_connections:
                if process := surveillance.processes.get(int(client_id)):
                    support.stop_process(pid=process.pid)
            else:
                logger.info("No active connections found.")
                for client_id, process in surveillance.processes.items():
                    support.stop_process(pid=process.pid)
