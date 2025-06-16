from typing import Dict

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

from jarvis.api.logger import logger
from jarvis.api.models import settings
from jarvis.modules.exceptions import CONDITIONAL_ENDPOINT_RESTRICTION
from jarvis.modules.models import models
from jarvis.modules.templates import templates


async def load_index() -> HTMLResponse:
    """Loads the HTML index path for listener spectrum file.

    Returns:
        HTMLResponse:
        Returns the HTML response for listener spectrum.
    """
    if not models.env.listener_spectrum_key:
        raise CONDITIONAL_ENDPOINT_RESTRICTION
    with open(templates.listener_spectrum.html, "r", encoding="utf-8") as file:
        html = file.read()
    return HTMLResponse(html)


async def get_listener_spectrum_js() -> FileResponse:
    """Returns the JavaScript for listener spectrum.

    Returns:
        FileResponse:
        Returns the loaded JavaScript as FileResponse.
    """
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


async def send_wave_command(command: str) -> Dict[str, str]:
    """Function to send wave commands to 'start' or 'stop' the spectrum.

    Args:
        command: Start or Stop command.

    Returns:
        Dict[str, str]:
        Returns a key-value pair with status.
    """
    if not models.env.listener_spectrum_key:
        raise CONDITIONAL_ENDPOINT_RESTRICTION
    from jarvis.api.routers.routes import APIPath

    if command not in ("start", "stop"):
        return {"error": "Invalid command"}
    await settings.ws_manager.send_message(
        message=command, ws_path=APIPath.listener_spectrum_ws
    )
    return {"status": f"Command '{command}' sent."}
