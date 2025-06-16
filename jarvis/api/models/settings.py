from multiprocessing import Process, Queue
from typing import Dict, Hashable, List, Optional, Tuple

from fastapi import WebSocket
from pydantic import BaseConfig, BaseModel, EmailStr


class Robinhood(BaseModel):
    """Initiates ``Robinhood`` object to handle members across modules.

    >>> Robinhood

    """

    token: Hashable = None


robinhood = Robinhood()


class StockMonitorHelper(BaseModel):
    """Initiates ``StockMonitorHelper`` object to handle members across modules.

    >>> StockMonitorHelper

    """

    otp_sent: Dict[EmailStr, Hashable] = {}
    otp_recd: Dict[EmailStr, Optional[Hashable]] = {}


stock_monitor_helper = StockMonitorHelper()


class Surveillance(BaseConfig):
    """Initiates ``Surveillance`` object to handle members across modules.

    >>> Surveillance

    """

    token: Hashable = None
    camera_index: str = None
    client_id: int = None
    available_cameras: List[str] = []
    processes: Dict[int, Process] = {}
    queue_manager: Dict[int, Queue] = {}
    session_manager: Dict[int, float] = {}
    frame: Tuple[int, int, int] = ()


surveillance = Surveillance()


class StockMonitor(BaseModel):
    """Initiates ``StockMonitor`` object to handle members across modules.

    >>> StockMonitor

    """

    user_info: Tuple[str, str, str, str, str, str] = (
        "ticker",
        "email",
        "max",
        "min",
        "correction",
        "repeat",
    )
    values: str = "(" + ",".join("?" for _ in user_info) + ")"
    alerts: Tuple[str, str, str, str, str, str, str] = (
        "time",
        "ticker",
        "email",
        "max",
        "min",
        "correction",
        "repeat",
    )
    alert_values: str = "(" + ",".join("?" for _ in alerts) + ")"


stock_monitor = StockMonitor()


class Trader(BaseModel):
    """Initiates ``Trader`` object to handle members across modules.

    >>> Trader

    """

    stock_list: Dict[str, str] = {}
    result: Dict[str, List[str]] = {"BUY": [], "SELL": [], "HOLD": []}


trader = Trader()


class ConnectionManager:
    """Initiates ``ConnectionManager`` object to handle multiple connections using ``WebSockets``.

    >>> ConnectionManager

    References:
        https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
    """

    def __init__(self):
        """Loads up an active connection queue."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts the websocket connection.

        Args:
            websocket: Websocket.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove socket from active connections.

        Args:
            websocket: Websocket.
        """
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, ws_path: str) -> None:
        """Send message to an active connection with match websocket path.

        Args:
            message: Message to send.
            ws_path: Websocket path.
        """
        for connection in self.active_connections:
            if connection.url.path == ws_path:
                await connection.send_text(message)


ws_manager = ConnectionManager()
