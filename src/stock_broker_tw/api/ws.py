"""WebSocket endpoint for real-time event fan-out."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from stock_broker_tw.metrics import metrics
from stock_broker_tw.yuanta.events import AsyncEventConsumer, EventQueue, YuantaEvent
from stock_broker_tw.yuanta.serializer import to_dict

router = APIRouter()


class ConnectionManager:
    """Manage connected WebSocket clients and broadcast adapter events."""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self._consumer: AsyncEventConsumer | None = None
        self._task: asyncio.Task[None] | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)
        metrics.ws_connections.set(len(self.active))
        await websocket.send_json({"type": "welcome", "message": "connected"})

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)
        metrics.ws_connections.set(len(self.active))

    async def start(self, event_queue: EventQueue) -> None:
        if self._consumer is not None:
            return
        self._consumer = event_queue.consume(self.broadcast_event)
        await self._consumer.start()

    async def stop(self) -> None:
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
        self._task = None

    async def broadcast_event(self, event: YuantaEvent) -> None:
        payload = {
            "type": event.str_index,
            "int_mark": event.int_mark,
            "dw_index": event.dw_index,
            "obj_handle": to_dict(event.obj_handle),
            "data": to_dict(event.obj_value),
        }
        for websocket in list(self.active):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(websocket)

    async def _heartbeat(self, websocket: WebSocket) -> None:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "heartbeat", "message": "pong"})


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    settings = websocket.app.state.settings
    expected = settings.server.api_token

    token = websocket.query_params.get("token")
    if not token:
        authorization = websocket.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
    if expected and token != expected:
        await websocket.close(code=1008)
        return

    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    heartbeat_task = asyncio.create_task(manager._heartbeat(websocket))
    try:
        while True:
            # Keep the connection alive; client messages are ignored in M2.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(websocket)


__all__ = ["ConnectionManager", "router"]
