from enum import StrEnum
from typing import List

from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.routing import APIRoute, APIWebSocketRoute


class Endpoints(StrEnum):
    """Endpoint for each API endpoint."""

    root = "/"
    proxy = "/proxy"
    health = "/health"
    keywords = "/keywords"
    get_file = "/get-file"
    put_file = "/put-file"
    video_feed = "/video-feed"
    investment = "/investment"
    line_count = "/line-count"
    file_count = "/file-count"
    list_files = "/list-files"
    secure_send = "/secure-send"
    get_signals = "/get-signals"
    favicon_ico = "/favicon.ico"
    surveillance = "/surveillance"
    stock_monitor = "/stock-monitor"
    surveillance_ws = "/ws/{client_id}"
    speech_synthesis = "/speech-synthesis"
    offline_communicator = "/offline-communicator"
    robinhood_authenticate = "/robinhood-authenticate"
    speech_synthesis_voices = "/speech-synthesis-voices"
    surveillance_authenticate = "/surveillance-authenticate"


def get_all_routes() -> List[APIRoute | APIWebSocketRoute]:
    """Loads all API routes and returns as list.

    Returns:
        List[APIRoute | APIWebSocketRoute]:
        List of all APIRoute or APIWebSocketRoute objects.
    """
    from jarvis.api.models import authenticator
    from jarvis.api.routers import (
        basics,
        fileio,
        investment,
        offline,
        proxy_service,
        secure_send,
        speech_synthesis,
        stats,
        stock_analysis,
        stock_monitor,
        surveillance,
        telegram,
    )
    from jarvis.modules.models import models

    return [
        APIRoute(
            endpoint=surveillance.authenticate_surveillance,
            methods=["POST"],
            path=Endpoints.surveillance_authenticate,
            dependencies=authenticator.SURVEILLANCE_PROTECTOR,
        ),
        APIRoute(
            endpoint=surveillance.monitor, methods=["GET"], path=Endpoints.surveillance
        ),
        APIRoute(
            endpoint=surveillance.video_feed,
            methods=["GET"],
            path=Endpoints.video_feed,
            include_in_schema=False,
        ),
        APIWebSocketRoute(
            endpoint=surveillance.websocket_endpoint, path=Endpoints.surveillance_ws
        ),
        APIRoute(
            endpoint=speech_synthesis.speech_synthesis_voices,
            methods=["GET"],
            path=Endpoints.speech_synthesis_voices,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
        APIRoute(
            endpoint=speech_synthesis.speech_synthesis,
            methods=["POST"],
            path=Endpoints.speech_synthesis,
            response_class=FileResponse,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
        APIRoute(
            endpoint=stock_monitor.stock_monitor_api,
            methods=["POST"],
            path=Endpoints.stock_monitor,
        ),
        APIRoute(
            endpoint=telegram.telegram_webhook,
            methods=["POST"],
            path=models.env.bot_endpoint,  # No enum
        ),
        APIRoute(
            endpoint=investment.authenticate_robinhood,
            methods=["POST"],
            path=Endpoints.robinhood_authenticate,
            dependencies=authenticator.ROBINHOOD_PROTECTOR,
        ),
        APIRoute(
            endpoint=investment.robinhood_path,
            methods=["GET"],
            path=Endpoints.investment,
            response_class=HTMLResponse,
        ),
        APIRoute(
            endpoint=offline.offline_communicator_api,
            methods=["POST"],
            path=Endpoints.offline_communicator,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
        APIRoute(
            endpoint=secure_send.secure_send_api,
            methods=["POST"],
            path=Endpoints.secure_send,
        ),
        APIRoute(endpoint=stats.line_count, methods=["GET"], path=Endpoints.line_count),
        APIRoute(endpoint=stats.file_count, methods=["GET"], path=Endpoints.file_count),
        APIRoute(
            endpoint=stock_analysis.get_signals,
            methods=["GET"],
            path=Endpoints.get_signals,
        ),
        APIRoute(
            endpoint=proxy_service.proxy_service_api,
            methods=["GET"],
            path=Endpoints.proxy,
        ),
        APIRoute(
            endpoint=basics.redirect_index,
            methods=["GET"],
            path=Endpoints.root,
            response_class=RedirectResponse,
            include_in_schema=False,
        ),
        APIRoute(
            endpoint=basics.health,
            methods=["GET"],
            path=Endpoints.health,
            include_in_schema=False,
        ),
        APIRoute(
            endpoint=basics.get_favicon,
            methods=["GET"],
            path=Endpoints.favicon_ico,
            include_in_schema=False,
        ),
        APIRoute(
            endpoint=basics.keywords,
            methods=["GET"],
            path=Endpoints.keywords,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
        APIRoute(
            endpoint=fileio.list_files,
            methods=["GET"],
            path=Endpoints.list_files,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
        APIRoute(
            endpoint=fileio.get_file,
            methods=["GET"],
            path=Endpoints.get_file,
            response_class=FileResponse,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
        APIRoute(
            endpoint=fileio.put_file,
            methods=["POST"],
            path=Endpoints.put_file,
            dependencies=authenticator.OFFLINE_PROTECTOR,
        ),
    ]
