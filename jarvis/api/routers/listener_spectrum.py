import socket
from http import HTTPStatus
from typing import Dict, NoReturn

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

from jarvis.api.logger import logger
from jarvis.api.models import settings
from jarvis.modules.exceptions import CONDITIONAL_ENDPOINT_RESTRICTION, APIResponse
from jarvis.modules.models import models
from jarvis.modules.templates import templates


async def check_internal(host_ip: str) -> None | NoReturn:
    """Check if the incoming request's IP address is internal or hosted by offline communicator.

    Args:
        host_ip: Incoming request's IP address.
    """
    if host_ip not in (
        models.env.offline_host,
        socket.gethostbyname("localhost"),
        "0.0.0.0",
    ):
        logger.warning("%s is not internal", host_ip)
        raise APIResponse(
            status_code=HTTPStatus.UNAUTHORIZED.real,
            detail=HTTPStatus.UNAUTHORIZED.description,
        )


async def load_index(request: Request) -> HTMLResponse:
    """Loads the HTML index path for listener spectrum file.

    Args:
        request: Request object from FastAPI.

    Returns:
        HTMLResponse:
        Returns the HTML response for listener spectrum.
    """
    await check_internal(request.client.host)
    if not models.env.listener_spectrum_key:
        raise CONDITIONAL_ENDPOINT_RESTRICTION
    with open(templates.listener_spectrum.html, "r", encoding="utf-8") as file:
        html = file.read()
    return HTMLResponse(html)


async def get_listener_spectrum_js(request: Request) -> FileResponse:
    """Returns the JavaScript for listener spectrum.

    Args:
        request: Request object from FastAPI.

    Returns:
        FileResponse:
        Returns the loaded JavaScript as FileResponse.
    """
    await check_internal(request.client.host)
    if not models.env.listener_spectrum_key:
        raise CONDITIONAL_ENDPOINT_RESTRICTION
    logger.warning("Responding to JS file request")
    return FileResponse(
        templates.listener_spectrum.javascript, media_type="application/javascript"
    )


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Websocket endpoint for listener spectrum display.

    Args:
        websocket: Websocket object.
    """
    await check_internal(websocket.client.host)
    if not models.env.listener_spectrum_key:
        raise CONDITIONAL_ENDPOINT_RESTRICTION
    await settings.ws_manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client but can handle if needed
            data = await websocket.receive_text()
            # For demo, echo back or ignore
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        await settings.ws_manager.disconnect(websocket)


async def send_wave_command(request: Request, command: str) -> Dict[str, str]:
    """Function to send wave commands to 'start' or 'stop' the spectrum.

    Args:
        request: Request object from FastAPI.
        command: Start or Stop command.

    Returns:
        Dict[str, str]:
        Returns a key-value pair with status.
    """
    await check_internal(request.client.host)
    if not models.env.listener_spectrum_key:
        raise CONDITIONAL_ENDPOINT_RESTRICTION
    from jarvis.api.routers.routes import APIPath

    if command not in ("start", "stop"):
        return {"error": "Invalid command"}
    await settings.ws_manager.send_message(
        message=command, ws_path=APIPath.listener_spectrum_ws
    )
    return {"status": f"Command '{command}' sent."}
