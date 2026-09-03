"""Integration tests for M3 read-only query APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from stock_broker_tw.config import (
    AccountConfig,
    QueryConfig,
    ServerConfig,
    Settings,
    StateConfig,
)
from stock_broker_tw.main import create_app
from stock_broker_tw.yuanta.events import EventQueue


class FakeAdapter:
    def __init__(self) -> None:
        self.logged_in = True
        self.opened = True
        self.event_queue = EventQueue()
        self.calls: list[tuple[str, dict]] = []
        self.timeout_functions: set[str] = set()

    def query(self, function_name: str, **params):
        self.calls.append((function_name, params))
        if function_name in self.timeout_functions:
            raise TimeoutError(f"timeout {function_name}")
        return {
            "GetStoreSummary": {"stk_store_list": [], "ov_stk_store_list": []},
            "GetBankBalance": {"bank_balance_list": [{"available_balance": 100.0}]},
            "GetStkTransactionOutlay": {"transaction_outlay_list": [{"settlement_amt": 50.0}]},
            "GetUnrealizedGainLossDetail": {"un_gain_loss_detail_list": []},
            "GetHisRealizedGainLoss": {"realized_gain_loss_list": []},
            "GetStkHistoryReportReversal": {"reversal_report_list": []},
            "GetRealReport": {"real_report_list": []},
            "GetRealReportMerge": {"real_report_merge_list": []},
            "GetOrderTradeReport": {
                "stk_order_list": [],
                "stk_trade_list": [],
                "fut_order_list": [],
                "fut_trade_list": [],
                "ov_stk_order_list": [],
                "ov_stk_trade_list": [],
                "ov_fut_order_list": [],
                "ov_fut_trade_list": [],
            },
        }.get(function_name, {})


def make_client(
    tmp_path: Path,
    adapter: FakeAdapter | None = None,
    rate_limit_per_second: int = 3,
) -> tuple[TestClient, FakeAdapter]:
    adapter = adapter or FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        query=QueryConfig(timeout=0.2, rate_limit_per_second=rate_limit_per_second),
    )
    app = create_app(settings=settings, adapter=adapter)
    return TestClient(app), adapter


def auth(token: str = "test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_m3_endpoints_require_token(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.get("/api/v1/positions").status_code == 401
        assert client.get("/api/v1/account/balance").status_code == 401
        assert client.get("/api/v1/reports/order-trade").status_code == 401


def test_positions_returns_data_and_saves_snapshot(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        res = client.get("/api/v1/positions", headers=auth())
        assert res.status_code == 200, res.text
        assert res.json()["data"] == {"stk_store_list": [], "ov_stk_store_list": []}
        assert adapter.calls[-1] == ("GetStoreSummary", {"Account": "S98875005091"})
        store = client.app.state.store
        latest = store.get_latest_snapshot("positions")
        assert latest is not None
        assert latest["data"]["stk_store_list"] == []


def test_balance_and_settlement_endpoints(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        balance = client.get("/api/v1/account/balance", headers=auth())
        assert balance.status_code == 200
        assert balance.json()["data"]["bank_balance_list"][0]["available_balance"] == 100.0

        settlement = client.get("/api/v1/account/settlement", headers=auth())
        assert settlement.status_code == 200
        assert settlement.json()["data"]["transaction_outlay_list"][0]["settlement_amt"] == 50.0


def test_pnl_and_report_endpoints(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        paths = [
            "/api/v1/pnl/unrealized",
            "/api/v1/pnl/realized?start_date=2026/01/01&end_date=2026/01/31",
            "/api/v1/pnl/reversal?re_gain_loss=%7B%7D",
            "/api/v1/reports/real",
            "/api/v1/reports/real-merge",
            "/api/v1/reports/order-trade",
        ]
        for path in paths:
            res = client.get(path, headers=auth())
            assert res.status_code == 200, f"{path}: {res.text}"


def test_reversal_requires_json_object(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        missing = client.get("/api/v1/pnl/reversal", headers=auth())
        assert missing.status_code == 400
        assert missing.json()["detail"]["code"] == "REGAINLOSS_REQUIRED"

        for value in ("null", "[]", "1"):
            res = client.get(
                f"/api/v1/pnl/reversal?re_gain_loss={value}",
                headers=auth(),
            )
            assert res.status_code == 400
            assert res.json()["detail"]["code"] == "INVALID_REQUEST"


def test_invalid_date_returns_400(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        res = client.get(
            "/api/v1/pnl/realized?start_date=2026-01-01&end_date=2026/01/31",
            headers=auth(),
        )
        assert res.status_code == 400
        body = res.json()["detail"]
        assert body["code"] == "INVALID_DATE"


def test_query_timeout_returns_504(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.timeout_functions.add("GetStoreSummary")
    client, _ = make_client(tmp_path, adapter)
    with client:
        res = client.get("/api/v1/positions", headers=auth())
        assert res.status_code == 504
        assert res.json()["detail"]["code"] == "QUERY_TIMEOUT"


def test_rate_limit_returns_429(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path, rate_limit_per_second=0)
    with client:
        res = client.get("/api/v1/positions", headers=auth())
        assert res.status_code == 429
        assert res.json()["detail"]["code"] == "RATE_LIMITED"


def test_order_trade_notshow_cancel_param(tmp_path: Path) -> None:
    client, adapter = make_client(tmp_path)
    with client:
        res = client.get(
            "/api/v1/reports/order-trade?notshow_cancel=true",
            headers=auth(),
        )
        assert res.status_code == 200
        assert adapter.calls[-1] == (
            "GetOrderTradeReport",
            {"NotshowCancel": True, "Account": "S98875005091"},
        )


def test_positions_returns_cached_snapshot_on_timeout(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.timeout_functions.add("GetStoreSummary")
    client, _ = make_client(tmp_path, adapter)
    client.app.state.store.save_snapshot(
        "positions",
        {"stk_store_list": [{"stk_code": "2330"}], "ov_stk_store_list": []},
        account="S98875005091",
    )
    with client:
        res = client.get("/api/v1/positions", headers=auth())
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["from_cache"] is True
        assert body["stk_store_list"] == [{"stk_code": "2330"}]
