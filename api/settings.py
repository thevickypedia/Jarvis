from multiprocessing import Process, Queue
from typing import Dict, Hashable, List, NoReturn

from fastapi import WebSocket
from pydantic import BaseConfig, BaseModel, HttpUrl


class Robinhood(BaseModel):
    """Initiates ``Robinhood`` object to handle members across modules.

    >>> Robinhood

    """

    token: Hashable = None


robinhood = Robinhood()


class Surveillance(BaseConfig):
    """Initiates ``Surveillance`` object to handle members across modules.

    >>> Surveillance

    """

    token: Hashable = None
    public_url: HttpUrl = None
    camera_index: str = None
    available_cameras: List[str] = []
    queue_manager: Queue = None
    client_id: int = None
    processes: Dict[int, Process] = {}


surveillance = Surveillance()


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

    def disconnect(self, websocket: WebSocket):
        """Remove socket from active connections.

        Args:
            websocket: Websocket.
        """
        self.active_connections.remove(websocket)
