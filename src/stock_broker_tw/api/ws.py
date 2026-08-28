"""WebSocket endpoint for real-time event fan-out."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from stock_broker_tw.metrics import metrics
from stock_broker_tw.yuanta.events import AsyncEventConsumer, EventQueue, YuantaEvent
from stock_broker_tw.yuanta.serializer import to_dict

router = APIRouter()

_REPORT_EVENT_TYPES = {"RR_RealReport", "RR_RealReportMerge"}
_QUOTE_EVENT_TYPES = {
    "SubscribeWatchlist",
    "SubscribeWatchlistAll",
    "SubscribeFiveTickA",
    "SubscribeStockTick",
    "SubscribeMarketInformation",
    "SubscribeStockInformation",
}


class ConnectionManager:
    """Manage connected WebSocket clients and broadcast adapter events."""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self._consumer: AsyncEventConsumer | None = None
        self._task: asyncio.Task[None] | None = None
        self.report_handler = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)
        metrics.ws_connections.set(len(self.active))
        await websocket.send_json({"type": "welcome", "message": "connected"})

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)
        metrics.ws_connections.set(len(self.active))

    async def start(self, event_queue: EventQueue, report_handler=None) -> None:
        if self._consumer is not None:
            return
        self.report_handler = report_handler
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

        # M4: process reports after the raw event is fanned out, preserving the
        # M2 raw-event behavior while still emitting processed report events.
        if self.report_handler is not None and event.str_index in _REPORT_EVENT_TYPES:
            try:
                handle = self.report_handler.handle_event(event)
                if asyncio.iscoroutine(handle) or hasattr(handle, "__await__"):
                    await handle
            except Exception:
                # Report processing must not kill the shared event consumer.
                pass

        # M5: keep the raw subscription event and also emit a unified
        # ``quote.updated`` processed event for JSON-friendly clients.
        if event.str_index in _QUOTE_EVENT_TYPES:
            try:
                await self.broadcast_json(
                    {
                        "type": "quote.updated",
                        "source": event.str_index,
                        "event": event.str_index,
                        "data": to_dict(event.obj_value),
                    }
                )
            except Exception:
                # Quote event processing must not kill the shared consumer.
                pass

    async def broadcast_json(self, payload: dict) -> None:
        """Send an arbitrary JSON object to all connected clients."""
        for websocket in list(self.active):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(websocket)

    async def broadcast_order_update(self, state: dict) -> None:
        """Convenience wrapper for order status notifications."""
        await self.broadcast_json({"type": "order.updated", "data": state})

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
            # Keep the connection alive; client messages are ignored in M2/M4.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(websocket)


__all__ = ["ConnectionManager", "router"]
