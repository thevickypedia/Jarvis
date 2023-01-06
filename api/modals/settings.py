from multiprocessing import Process, Queue
from typing import Dict, Hashable, List, NoReturn, Optional, Tuple

from fastapi import WebSocket
from pydantic import BaseConfig, BaseModel, EmailStr, HttpUrl


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
    public_url: HttpUrl = None
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

    user_info: Tuple[str, str, str, str, str] = ("ticker", "email", "max", "min", "correction")
    values: str = '(' + ','.join('?' for _ in user_info) + ')'
    stock_list: List[str] = []


stock_monitor = StockMonitor()


class ConnectionManager:
    """Initiates ``ConnectionManager`` object to handle multiple connections using ``WebSockets``.

    >>> ConnectionManager

    References:
        https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
    """

    def __init__(self):
        """Loads up an active connection queue."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> NoReturn:
        """Accepts the websocket connection.

        Args:
            websocket: Websocket.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> NoReturn:
        """Remove socket from active connections.

        Args:
            websocket: Websocket.
        """
        self.active_connections.remove(websocket)
