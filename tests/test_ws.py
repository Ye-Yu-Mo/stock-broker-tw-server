"""Tests for the M2 WebSocket basic connection and event fan-out."""

from __future__ import annotations

from fastapi.testclient import TestClient

from stock_broker_tw.config import ServerConfig, Settings
from stock_broker_tw.main import create_app
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


class FakeAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = False
        self.logged_in = False
        self.disposed = False
        self.last_login_result = None

    def open(self) -> None:
        self.opened = True

    def reset_login_result(self) -> None:
        self.last_login_result = None

    def login(self, *args, **kwargs) -> bool:
        return True

    def logout(self) -> bool:
        return True


def test_websocket_receives_welcome_and_broadcast_event() -> None:
    settings = Settings(server=ServerConfig(api_token="test-token"))
    adapter = FakeAdapter()
    app = create_app(settings=settings, adapter=adapter)
    with TestClient(app) as client, client.websocket_connect("/ws?token=test-token") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "welcome"

        adapter.event_queue.put(
            YuantaEvent(2, 0, "RR_RealReport", None, {"order_no": "12345"})
        )
        event = ws.receive_json()
        assert event["type"] == "RR_RealReport"
        assert event["data"]["order_no"] == "12345"


def test_websocket_rejects_missing_or_bad_token() -> None:
    import starlette.websockets

    settings = Settings(server=ServerConfig(api_token="test-token"))
    app = create_app(settings=settings, adapter=FakeAdapter())
    with TestClient(app) as client:
        try:
            with client.websocket_connect("/ws"):
                raise AssertionError("expected WebSocket to be rejected")
        except starlette.websockets.WebSocketDisconnect as exc:
            assert exc.code == 1008
