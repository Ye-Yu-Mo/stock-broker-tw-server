"""M5 integration tests: HTTP quote subscription and query APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from stock_broker_tw.config import (
    AccountConfig,
    QuoteConfig,
    ServerConfig,
    Settings,
    StateConfig,
)
from stock_broker_tw.main import create_app
from stock_broker_tw.yuanta.events import EventQueue


class FakeAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = True
        self.logged_in = True
        self.disposed = False
        self.last_login_result = None
        self.subscribe_calls: list[tuple[str, str, list]] = []
        self.unsubscribe_calls: list[tuple[str, str, list]] = []
        self.query_calls: list[tuple[str, dict]] = []

    def subscribe(self, function_name: str, account: str, symbols: list):
        self.subscribe_calls.append((function_name, account, symbols))
        return True

    def unsubscribe(self, function_name: str, account: str, symbols: list):
        self.unsubscribe_calls.append((function_name, account, symbols))
        return True

    def query(self, function_name: str, **params):
        self.query_calls.append((function_name, params))
        return {
            "GetWatchListAll": {"query_watch_list": [{"stk_code": "2330", "deal_price": 500.0}]},
            "GetStockInformation": {"stock_information_list": [{"stock_code": "2330"}]},
            "GetStkTickDetail": {"stick_detail_list": [{"deal_price": 500.0}]},
            "GetStkClassifyPrice": {"classify_price_list": [{"price": 500.0}]},
            "GetKLine": {"k_line_list": [{"close_price": 505.0}]},
        }.get(function_name, {})


def make_client(
    tmp_path: Path,
    adapter: FakeAdapter | None = None,
    quote_config: QuoteConfig | None = None,
) -> tuple[TestClient, FakeAdapter]:
    adapter = adapter or FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        quote=quote_config or QuoteConfig(),
    )
    app = create_app(settings=settings, adapter=adapter)
    return TestClient(app), adapter


def auth(token: str = "test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_quote_endpoints_require_token(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.post("/api/v1/quotes/subscribe", json={}).status_code == 401
        assert client.post("/api/v1/quotes/unsubscribe", json={}).status_code == 401
        assert client.get("/api/v1/quotes/subscribed").status_code == 401
        assert client.get("/api/v1/quotes/snapshot").status_code == 401
        assert client.get("/api/v1/quotes/kline").status_code == 401
        assert client.get("/api/v1/stocks/info").status_code == 401


def test_subscribe_unsubscribe_list_via_http(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        res = client.post(
            "/api/v1/quotes/subscribe",
            json={"type": "five_tick", "symbols": ["2330"], "account": "S98875005091"},
            headers=auth(),
        )
        assert res.status_code == 200, res.text
        assert res.json()["data"] == [
            {"account": "S98875005091", "type": "five_tick", "symbol": "2330", "market_type": "TWSE"}
        ]
        assert adapter.subscribe_calls == [
            ("SubscribeFiveTickA", "S98875005091", [{"market_type": "TWSE", "stk_code": "2330"}])
        ]

        listed = client.get("/api/v1/quotes/subscribed", headers=auth())
        assert listed.status_code == 200
        assert listed.json()["data"][0]["symbol"] == "2330"

        res = client.post(
            "/api/v1/quotes/unsubscribe",
            json={"type": "five_tick", "symbols": ["2330"]},
            headers=auth(),
        )
        assert res.status_code == 200
        assert res.json()["data"] == []
        assert adapter.unsubscribe_calls == [
            ("UnSubscribeFiveTickA", "S98875005091", [{"market_type": "TWSE", "stk_code": "2330"}])
        ]


def test_empty_subscribe_returns_400(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        res = client.post(
            "/api/v1/quotes/subscribe",
            json={"type": "five_tick", "symbols": []},
            headers=auth(),
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "EMPTY_SYMBOLS"
        assert adapter.subscribe_calls == []


def test_invalid_quote_type_returns_400(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        res = client.post(
            "/api/v1/quotes/subscribe",
            json={"type": "bad", "symbols": ["2330"]},
            headers=auth(),
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "INVALID_QUOTE_TYPE"
        assert adapter.subscribe_calls == []


def test_quote_query_endpoints(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        snapshot = client.get("/api/v1/quotes/snapshot?stk_code=2330", headers=auth())
        assert snapshot.status_code == 200
        assert snapshot.json()["data"]["query_watch_list"][0]["stk_code"] == "2330"
        assert adapter.query_calls[-1] == (
            "GetWatchListAll",
            {"Account": "S98875005091", "QuoteList": [{"market_type": "TWSE", "stock_code": "2330"}]},
        )

        ticks = client.get("/api/v1/quotes/ticks?stk_code=2330", headers=auth())
        assert ticks.status_code == 200
        assert ticks.json()["data"]["stick_detail_list"][0]["deal_price"] == 500.0
        assert adapter.query_calls[-1][0] == "GetStkTickDetail"

        classify = client.get("/api/v1/quotes/classify-price?stk_code=2330", headers=auth())
        assert classify.status_code == 200
        assert classify.json()["data"]["classify_price_list"][0]["price"] == 500.0
        assert adapter.query_calls[-1][0] == "GetStkClassifyPrice"

        kline = client.get(
            "/api/v1/quotes/kline?stk_code=2330&start_date=2026/01/01&end_date=2026/01/31",
            headers=auth(),
        )
        assert kline.status_code == 200
        assert kline.json()["data"]["k_line_list"][0]["close_price"] == 505.0
        assert adapter.query_calls[-1][0] == "GetKLine"

        info = client.get("/api/v1/stocks/info?stk_code=2330", headers=auth())
        assert info.status_code == 200
        assert info.json()["data"]["stock_information_list"][0]["stock_code"] == "2330"
        assert adapter.query_calls[-1][0] == "GetStockInformation"


def test_kline_invalid_date_returns_400(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        res = client.get(
            "/api/v1/quotes/kline?stk_code=2330&start_date=2026-01-01&end_date=2026/01/31",
            headers=auth(),
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "INVALID_DATE"


def test_subscribe_limit_returns_400(tmp_path: Path) -> None:
    client, _ = make_client(
        tmp_path,
        quote_config=QuoteConfig(max_per_request=1),
    )
    with client:
        res = client.post(
            "/api/v1/quotes/subscribe",
            json={"type": "five_tick", "symbols": ["2330", "2885"]},
            headers=auth(),
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "MAX_PER_REQUEST_EXCEEDED"
