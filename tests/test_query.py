"""Tests for QueryService using a fake adapter and real SQLite store."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from stock_broker_tw.config import AccountConfig, QueryConfig, Settings, StateConfig
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.service.query import QueryError, QueryService
from stock_broker_tw.state.store import StateStore


class FakeAdapter:
    def __init__(self, result=None) -> None:
        self.logged_in = True
        self.calls: list[tuple[str, dict]] = []
        self.result = result or {"stk_store_list": []}
        self.raise_timeout = False

    def query(self, function_name: str, **params):
        self.calls.append((function_name, params))
        if self.raise_timeout:
            raise TimeoutError(f"timeout {function_name}")
        return self.result


def make_service(
    tmp_path: Path,
    adapter: FakeAdapter | None = None,
    rate_limiter: RateLimiter | None = None,
) -> tuple[QueryService, FakeAdapter]:
    adapter = adapter or FakeAdapter()
    settings = Settings(
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        query=QueryConfig(timeout=0.5),
        account=AccountConfig(account="S98875005091", password="1234"),
    )
    store = StateStore(settings.state.db_path)
    service = QueryService(
        adapter,
        settings,
        store=store,
        rate_limiter=rate_limiter,
    )
    return service, adapter


def run(coro):
    return asyncio.run(coro)


def test_positions_queries_and_saves_snapshot(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path)
    result = run(service.positions())
    assert adapter.calls == [("GetStoreSummary", {"Account": "S98875005091"})]
    assert result == {"stk_store_list": []}
    latest = service.store.get_latest_snapshot("positions")
    assert latest is not None
    assert latest["data"] == result


def test_balance_and_settlement_use_account(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path, FakeAdapter({"bank_balance_list": []}))
    run(service.account_balance(account="S123"))
    assert adapter.calls[-1] == ("GetBankBalance", {"Account": "S123"})

    service2, adapter2 = make_service(tmp_path, FakeAdapter({"transaction_outlay_list": []}))
    run(service2.settlement())
    assert adapter2.calls[-1] == ("GetStkTransactionOutlay", {"Account": "S98875005091"})


def test_pnl_realized_passes_dates(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path, FakeAdapter({"realized_gain_loss_list": []}))
    run(service.realized_pnl("2026/01/01", "2026/01/31"))
    assert adapter.calls[-1] == (
        "GetHisRealizedGainLoss",
        {"Account": "S98875005091", "SDate": "2026/01/01", "EDate": "2026/01/31"},
    )


def test_order_trade_report_passes_notshow_cancel(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path, FakeAdapter({"stk_order_list": []}))
    run(service.order_trade_reports(notshow_cancel=True))
    assert adapter.calls[-1] == (
        "GetOrderTradeReport",
        {"NotshowCancel": True, "Account": "S98875005091"},
    )


def test_positions_falls_back_to_snapshot_on_query_error(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path)
    service.store.save_snapshot("positions", {"stk_store_list": [{"stk_code": "2330"}]}, account="S98875005091")
    adapter.raise_timeout = True
    result = run(service.positions())
    assert result["from_cache"] is True
    assert result["stk_store_list"] == [{"stk_code": "2330"}]


def test_query_timeout_maps_to_504(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.raise_timeout = True
    service, _ = make_service(tmp_path, adapter)
    with pytest.raises(QueryError) as exc_info:
        run(service.positions())
    assert exc_info.value.status_code == 504
    assert exc_info.value.code == "QUERY_TIMEOUT"


def test_rate_limit_maps_to_429(tmp_path: Path) -> None:
    limiter = RateLimiter(max_per_second=0, max_per_minute=0)
    service, _ = make_service(tmp_path, rate_limiter=limiter)
    with pytest.raises(QueryError) as exc_info:
        run(service.positions())
    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "RATE_LIMITED"
