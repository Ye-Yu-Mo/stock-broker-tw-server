"""M5 WebSocket tests: quote.updated processed events."""

from __future__ import annotations

from fastapi.testclient import TestClient

from stock_broker_tw.config import ServerConfig, Settings
from stock_broker_tw.main import create_app
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


class FakeAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = True
        self.logged_in = True
        self.disposed = False
        self.last_login_result = None


def test_websocket_receives_raw_and_quote_updated() -> None:
    settings = Settings(server=ServerConfig(api_token="test-token"))
    adapter = FakeAdapter()
    app = create_app(settings=settings, adapter=adapter)
    with TestClient(app) as client, client.websocket_connect("/ws?token=test-token") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "welcome"

        adapter.event_queue.put(
            YuantaEvent(
                2,
                0,
                "SubscribeFiveTickA",
                None,
                {"key": "TWSE2330", "market_type": "TWSE", "stk_code": "2330"},
            )
        )
        seen_types = set()
        messages = []
        for _ in range(3):
            msg = ws.receive_json()
            messages.append(msg)
            seen_types.add(msg["type"])
            if {"SubscribeFiveTickA", "quote.updated"} <= seen_types:
                break
        assert "SubscribeFiveTickA" in seen_types
        assert "quote.updated" in seen_types
        quote = next(m for m in messages if m["type"] == "quote.updated")
        assert quote["source"] == "SubscribeFiveTickA"
        assert quote["data"]["stk_code"] == "2330"


def test_websocket_receives_quote_and_report_together() -> None:
    settings = Settings(server=ServerConfig(api_token="test-token"))
    adapter = FakeAdapter()
    app = create_app(settings=settings, adapter=adapter)
    with TestClient(app) as client, client.websocket_connect("/ws?token=test-token") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "welcome"

        adapter.event_queue.put(
            YuantaEvent(2, 0, "SubscribeStockTick", None, {"stk_code": "2330"})
        )
        adapter.event_queue.put(
            YuantaEvent(
                2,
                0,
                "RR_RealReport",
                None,
                {"order_no": "H00001", "order_status": 20},
            )
        )
        seen_types = set()
        for _ in range(6):
            msg = ws.receive_json()
            seen_types.add(msg["type"])
            if {"quote.updated", "RR_RealReport"} <= seen_types:
                break
        assert "quote.updated" in seen_types
        assert "RR_RealReport" in seen_types
