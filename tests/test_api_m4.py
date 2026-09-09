"""M4 integration tests: HTTP order APIs and WebSocket order updates."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stock_broker_tw.config import (
    AccountConfig,
    RiskConfig,
    ServerConfig,
    Settings,
    StateConfig,
)
from stock_broker_tw.main import create_app
from stock_broker_tw.service.query import QueryError
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


class FakeAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = True
        self.logged_in = True
        self.disposed = False
        self.last_login_result = None
        self.calls: list[dict] = []
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

    def query(self, function_name: str, **params):
        if function_name == "GetWatchListAll":
            return {
                "query_watch_list": [
                    {
                        "stk_code": params["QuoteList"][0]["stock_code"],
                        "buy_price": 99.0,
                        "sell_price": 101.0,
                    }
                ]
            }
        return {}


class FakeMockQuoteProvider:
    async def snapshot(self, stk_code: str, market_type: str = "TWSE"):
        return {
            "query_watch_list": [
                {"stk_code": stk_code, "buy_price": 99.0, "sell_price": 101.0}
            ]
        }


class ErrorMockQuoteProvider:
    async def snapshot(self, stk_code: str, market_type: str = "TWSE"):
        raise QueryError(
            "mock quote rate limited",
            code="RATE_LIMITED",
            status_code=429,
            detail={"function": "GetWatchListAll"},
        )


def make_client(tmp_path: Path, adapter: FakeAdapter | None = None, risk: RiskConfig | None = None):
    adapter = adapter or FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        risk=risk or RiskConfig(),
    )
    app = create_app(
        settings=settings,
        adapter=adapter,
        mock_quote_provider=FakeMockQuoteProvider(),
    )
    return TestClient(app), adapter


def auth(token: str = "test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_orders_endpoints_require_token(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.post("/api/v1/orders/stock", json={}).status_code == 401
        assert client.get("/api/v1/orders").status_code == 401
        assert client.get("/api/v1/orders/C001").status_code == 401


def test_place_order_and_query(tmp_path: Path) -> None:
    client, _adapter = make_client(tmp_path)
    with client:
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
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["status"] == "ACCEPTED"
        assert body["order_no"] == "H00001"

        res = client.get("/api/v1/orders/C001", headers=auth())
        assert res.status_code == 200
        assert res.json()["data"]["client_order_id"] == "C001"

        res = client.get("/api/v1/orders", headers=auth())
        assert res.json()["data"][0]["client_order_id"] == "C001"


def test_duplicate_client_order_id_does_not_call_adapter_twice(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    payload = {
        "client_order_id": "C001",
        "action": "new",
        "stk_code": "2330",
        "side": "B",
        "price": 500.0,
        "quantity": 10,
        "account": "S98875005091",
    }
    with client:
        first = client.post("/api/v1/orders/stock", json=payload, headers=auth())
        second = client.post("/api/v1/orders/stock", json=payload, headers=auth())
        assert first.status_code == 200
        assert second.status_code == 200
        assert len(adapter.calls) == 1


def test_risk_rejected_returns_400_and_no_adapter_call(tmp_path: Path) -> None:
    risk = RiskConfig(max_order_qty=1)
    client, adapter = make_client(tmp_path, risk=risk)
    with client:
        res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 100,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "ORDER_QTY_EXCEEDED"
        assert adapter.calls == []


def test_mock_order_skips_adapter_and_fills(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        initialized = client.post(
            "/api/v1/mock/accounts/init",
            json={"account": "MOCK-API-001", "cash": 100_000.0, "positions": []},
            headers=auth(),
        )
        assert initialized.status_code == 200, initialized.text
        res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "MOCK-API-001",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "MOCK-API-001",
                "mock": True,
            },
            headers=auth(),
        )

        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["status"] == "FILLED"
        assert body["order_no"].startswith("MOCK-")
        assert body["avg_price"] == 101.0
        assert body["filled_qty"] == 10
        assert adapter.calls == []


def test_mock_account_init_and_order_uses_ask1(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        initialized = client.post(
            "/api/v1/mock/accounts/init",
            json={
                "account": "MOCK-API",
                "cash": 10_000.0,
                "positions": [],
            },
            headers=auth(),
        )
        assert initialized.status_code == 200, initialized.text
        assert initialized.json()["data"]["cash"] == 10_000.0

        with client.websocket_connect("/ws?token=test-token") as ws:
            assert ws.receive_json()["type"] == "welcome"
            res = client.post(
                "/api/v1/orders/stock",
                json={
                    "client_order_id": "MOCK-API-002",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 10,
                    "account": "MOCK-API",
                    "mock": True,
                },
                headers=auth(),
            )
            assert res.status_code == 200, res.text
            body = res.json()["data"]
            assert body["status"] == "FILLED"
            assert body["avg_price"] == 101.0
            assert body["data"]["ask1"] == 101.0
            assert body["data"]["mock"] is True

            updates = []
            for _ in range(2):
                message = ws.receive_json()
                if message["type"] == "order.updated":
                    updates.append(message["data"])
            assert any(update["status"] == "FILLED" for update in updates)

        listed = client.get(
            "/api/v1/orders?account=MOCK-API",
            headers=auth(),
        )
        assert listed.status_code == 200
        assert listed.json()["data"][0]["status"] == "FILLED"
        assert adapter.calls == []



def test_websocket_receives_real_report_and_order_updated(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        # Persist an accepted order before feeding the report.
        res = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "S98875005091",
            },
            headers=auth(),
        )
        assert res.status_code == 200
        assert client.app.state.store.get_stock_order("C001")["order_no"] == "H00001"

        with client.websocket_connect("/ws?token=test-token") as ws:
            welcome = ws.receive_json()
            assert welcome["type"] == "welcome"

            adapter.event_queue.put(
                YuantaEvent(
                    2,
                    0,
                    "RR_RealReportMerge",
                    None,
                    {
                        "order_no": "H00001",
                        "basket_no": "C001",
                        "order_status": 20,
                        "last_order_status": 8,
                        "ok_qty": 10,
                        "order_qty": 10,
                        "avg_deal_price": 505.0,
                    },
                )
            )
            seen_types = set()
            for _ in range(5):
                msg = ws.receive_json()
                seen_types.add(msg["type"])
                if "order.updated" in seen_types and "real_report_merge" in seen_types:
                    break
            assert "real_report_merge" in seen_types
            assert "order.updated" in seen_types
            assert client.app.state.store.get_stock_order("C001")["status"] == "FILLED"


def test_http_mock_cancel_and_replace_stay_local(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        initialized = client.post(
            "/api/v1/mock/accounts/init",
            json={"account": "MOCK-HTTP", "cash": 10_000.0, "positions": []},
            headers=auth(),
        )
        assert initialized.status_code == 200
        placed = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "MOCK-HTTP-001",
                "account": "MOCK-HTTP",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "mock": True,
            },
            headers=auth(),
        )
        order_no = placed.json()["data"]["order_no"]

        for action, extra in (
            ("cancel", {}),
            ("replace", {"new_price": 510.0}),
        ):
            response = client.post(
                "/api/v1/orders/stock",
                json={
                    "client_order_id": f"MOCK-HTTP-{action}",
                    "action": action,
                    "account": "MOCK-HTTP",
                    "order_no": order_no,
                    "stk_code": "2330",
                    "mock": True,
                    **extra,
                },
                headers=auth(),
            )
            assert response.status_code == 409, response.text
            assert response.json()["detail"]["code"] == "MOCK_ORDER_FINAL"

        assert adapter.calls == []


def test_default_app_provides_offline_mock_quotes(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        risk=RiskConfig(),
    )
    client = TestClient(create_app(settings=settings, adapter=adapter))
    with client:
        initialized = client.post(
            "/api/v1/mock/accounts/init",
            json={"account": "MOCK-DEFAULT", "cash": 10_000.0, "positions": []},
            headers=auth(),
        )
        assert initialized.status_code == 200, initialized.text
        response = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "MOCK-DEFAULT-001",
                "account": "MOCK-DEFAULT",
                "stk_code": "2330",
                "side": "B",
                "quantity": 10,
                "mock": True,
            },
            headers=auth(),
        )
        assert response.status_code == 200, response.text
        assert response.json()["data"]["status"] == "FILLED"
        assert response.json()["data"]["avg_price"] == 101.0
        assert adapter.calls == []


def test_mock_account_api_enforces_namespace_and_deactivation(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        invalid = client.post(
            "/api/v1/mock/accounts/init",
            json={"account": "S98875005091", "cash": 10_000.0, "positions": []},
            headers=auth(),
        )
        assert invalid.status_code == 422

        initialized = client.post(
            "/api/v1/mock/accounts/init",
            json={"account": "MOCK-DELETE", "cash": 10_000.0, "positions": []},
            headers=auth(),
        )
        assert initialized.status_code == 200
        removed = client.delete("/api/v1/mock/accounts/MOCK-DELETE", headers=auth())
        assert removed.status_code == 200, removed.text
        assert removed.json()["data"]["active"] is False

        account = client.get("/api/v1/mock/accounts/MOCK-DELETE", headers=auth())
        assert account.status_code == 200
        assert account.json()["data"]["active"] is False
        assert adapter.calls == []


def test_mock_account_api_rejects_non_finite_values(tmp_path: Path) -> None:
    client, _adapter = make_client(tmp_path)
    with client:
        for cash in ("NaN", "Infinity"):
            response = client.post(
                "/api/v1/mock/accounts/init",
                json={"account": "MOCK-NONFINITE", "cash": cash, "positions": []},
                headers=auth(),
            )
            assert response.status_code == 422, response.text


def test_mock_query_error_keeps_http_contract(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        risk=RiskConfig(),
    )
    client = TestClient(
        create_app(
            settings=settings,
            adapter=adapter,
            mock_quote_provider=ErrorMockQuoteProvider(),
        )
    )
    with client:
        initialized = client.post(
            "/api/v1/mock/accounts/init",
            json={"account": "MOCK-QUERY-API", "cash": 10_000.0, "positions": []},
            headers=auth(),
        )
        assert initialized.status_code == 200
        response = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "MOCK-QUERY-API-001",
                "account": "MOCK-QUERY-API",
                "stk_code": "2330",
                "side": "B",
                "quantity": 1,
                "mock": True,
            },
            headers=auth(),
        )
        assert response.status_code == 429
        assert response.json()["detail"] == {
            "code": "RATE_LIMITED",
            "message": "mock quote rate limited",
            "detail": {"function": "GetWatchListAll"},
        }


@pytest.mark.parametrize(
    ("field", "value"),
    (("side", "X"), ("price_flag", "INVALID"), ("time_in_force", "INVALID"), ("ap_code", 1)),
)
def test_order_api_rejects_invalid_adapter_fields(
    tmp_path: Path, field: str, value: object
) -> None:
    client, adapter = make_client(tmp_path)
    payload = {
        "client_order_id": "INVALID001",
        "stk_code": "2330",
        "side": "B",
        "price": 500.0,
        "quantity": 1,
        "account": "S98875005091",
    }
    payload[field] = value

    with client:
        response = client.post("/api/v1/orders/stock", json=payload, headers=auth())

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_ORDER_FIELD"
    assert adapter.calls == []


def test_order_api_rejects_non_positive_replace_quantity(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        response = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "REPLACE001",
                "action": "replace",
                "account": "S98875005091",
                "order_no": "H00001",
                "stk_code": "2330",
                "side": "B",
                "new_quantity": 0,
            },
            headers=auth(),
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_ORDER_FIELD"
    assert adapter.calls == []


def test_order_api_accepts_semantic_ap_code(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        response = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "SEMANTIC001",
                "account": "S98875005091",
                "stk_code": "00635U",
                "side": "S",
                "price": 46.0,
                "quantity": 1,
                "ap_code": "INTRADAY_ODD_LOT",
            },
            headers=auth(),
        )

    assert response.status_code == 200
    assert adapter.calls[-1]["order"]["ap_code"] == 4
