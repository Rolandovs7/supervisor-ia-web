"""Real-time alert notifications over WebSockets."""

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.security import validate_token

router = APIRouter(tags=["websockets"])


class ConnectionManager:
    """Track live WebSocket clients and fan out alert messages."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    def broadcast_threadsafe(self, message: dict[str, Any]) -> None:
        """Broadcast from a sync background worker (the YOLO thread)."""
        if not self.active_connections or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)


manager = ConnectionManager()


@router.websocket("/ws/alertas")
async def alertas_ws(websocket: WebSocket) -> None:
    """Stream alerts to clients authenticated with ``?token=<JWT>``."""
    try:
        validate_token(websocket.query_params.get("token"))
    except HTTPException:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
