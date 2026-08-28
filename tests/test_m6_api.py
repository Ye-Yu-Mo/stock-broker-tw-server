"""M6 API integration tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from stock_broker_tw.config import (
    AccountConfig,
    NotifyConfig,
    QuoteConfig,
    RiskConfig,
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
        self.calls: list[dict] = []
        self.query_calls: list[tuple[str, dict]] = []
        self.subscribe_calls: list[tuple[str, str, list]] = []
        self.fail_send = False

    def open(self) -> None:
        self.opened = True

    def reset_login_result(self) -> None:
        self.last_login_result = None

    def login(self, *args, **kwargs) -> bool:
        return True

    def logout(self) -> bool:
        return True

    def send_stock_order(self, account: str, order: dict, timeout: float = 10.0):
        self.calls.append({"account": account, "order": order})
        if self.fail_send:
            raise RuntimeError("boom")
        return {
            "result_count": {"msg_code": "0001", "msg_content": "ok", "count": 1},
            "result_list": [
                {
                    "identify": order.get("identify", 1),
                    "reply_code": 0,
                    "order_no": "H00001",
                    "trade_date": "2026/08/28",
                    "err_type": "",
                    "err_no": "",
                    "advisory": "",
                }
            ],
        }

    def subscribe(self, function_name: str, account: str, symbols: list):
        self.subscribe_calls.append((function_name, account, symbols))
        return True

    def unsubscribe(self, function_name: str, account: str, symbols: list):
        self.subscribe_calls.append((function_name, account, symbols))
        return True

    def query(self, function_name: str, **params):
        self.query_calls.append((function_name, params))
        if function_name == "GetQuoteList":
            return {
                "account": "S98875005091",
                "quote_list": [
                    {"market_type": "TWSE", "stock_code": "2330", "index_flag": 7},
                ],
            }
        return {}


def make_client(tmp_path: Path, adapter: FakeAdapter | None = None, risk: RiskConfig | None = None):
    adapter = adapter or FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        risk=risk or RiskConfig(),
        quote=QuoteConfig(),
        notify=NotifyConfig(enabled=False),
    )
    app = create_app(settings=settings, adapter=adapter)
    return TestClient(app), adapter


def auth(token: str = "test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_replace_with_both_new_price_and_new_quantity_returns_400(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        # Create an original order so replace can resolve order_no locally.
        client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "action": "new",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C002",
                "action": "replace",
                "order_no": "H00001",
                "stk_code": "2330",
                "side": "B",
                "new_price": 510.0,
                "new_quantity": 20,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "REPLACE_BOTH_FIELDS_UNSUPPORTED"
        # Only the initial new order reached the adapter; the replace was rejected.
        assert len(adapter.calls) == 1


def test_subscribed_supports_broker_source(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        res = client.get("/api/v1/quotes/subscribed?source=broker", headers=auth())
        assert res.status_code == 200
        body = res.json()["data"]
        assert body["source"] == "broker"
        assert body["items"][0]["stock_code"] == "2330"
        assert adapter.query_calls[-1][0] == "GetQuoteList"


def test_watchlist_subscribe_distinguishes_index_flag(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        for flag in (7, 8):
            res = client.post(
                "/api/v1/quotes/subscribe",
                json={
                    "type": "watchlist",
                    "symbols": ["2330"],
                    "index_flag": flag,
                    "account": "S98875005091",
                },
                headers=auth(),
            )
            assert res.status_code == 200, res.text
        assert adapter.subscribe_calls == [
            ("SubscribeWatchlist", "S98875005091", [{"market_type": "TWSE", "stk_code": "2330", "index_flag": 7}]),
            ("SubscribeWatchlist", "S98875005091", [{"market_type": "TWSE", "stk_code": "2330", "index_flag": 8}]),
        ]
        rows = client.get("/api/v1/quotes/subscribed", headers=auth()).json()["data"]
        assert len(rows) == 2
        assert {row["index_flag"] for row in rows} == {7, 8}


def test_panic_and_resume_controls(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.get("/health").json()["panic"] is False
        res = client.post("/api/v1/control/panic", headers=auth())
        assert res.status_code == 200
        assert client.get("/health").json()["panic"] is True

        order_res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "action": "new",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        assert order_res.status_code == 400
        assert "PANIC" in order_res.json()["detail"]["code"]

        resume = client.post("/api/v1/control/resume", headers=auth())
        assert resume.status_code == 200
        assert client.get("/health").json()["panic"] is False


def test_health_exposes_circuit_breaker_and_recovery(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        body = client.get("/health").json()
        assert "circuit_breaker_open" in body
        assert "last_failure" in body
        assert "last_recovery" in body


def test_recovery_unresolved_and_resolve_api(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        store = client.app.state.store
        store.save_stock_order(
            client_order_id="C001",
            request={"client_order_id": "C001", "stk_code": "2330"},
            status="NEED_MANUAL_REVIEW",
            account="S98875005091",
            action="new",
        )
        res = client.get("/api/v1/recovery/unresolved", headers=auth())
        assert res.status_code == 200
        assert any(item["client_order_id"] == "C001" for item in res.json()["data"])

        resolve = client.post(
            "/api/v1/recovery/C001/resolve",
            json={"status": "FILLED"},
            headers=auth(),
        )
        assert resolve.status_code == 200
        assert store.get_stock_order("C001")["status"] == "FILLED"


def test_circuit_open_blocks_write_with_503(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        breaker = client.app.state.circuit_breaker
        breaker.failure_threshold = 1
        breaker.record_failure("simulated adapter outage")
        res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "action": "new",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        assert res.status_code == 503
        assert res.json()["detail"]["code"] == "CIRCUIT_OPEN"
        assert adapter.calls == []

        # Resume manually clears the breaker.
        resume = client.post("/api/v1/control/resume", headers=auth())
        assert resume.status_code == 200
        ok_res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "action": "new",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        assert ok_res.status_code == 200
