"""M6 recovery enhancements for M4 stock_orders."""

from __future__ import annotations

import asyncio
from pathlib import Path

from stock_broker_tw.config import AccountConfig, QueryConfig, Settings, StateConfig
from stock_broker_tw.service.query import QueryService
from stock_broker_tw.state.recovery import run_startup_recovery
from stock_broker_tw.state.store import StateStore


class FakeAdapter:
    def __init__(self, logged_in: bool = True) -> None:
        self.logged_in = logged_in
        self.calls: list[str] = []

    def query(self, function_name: str, **params):
        self.calls.append(function_name)
        if function_name == "GetOrderTradeReport":
            return {
                "stk_order_list": [
                    {
                        "order_no": "H00002",
                        "account": "S98875005091",
                        "trade_date": {"year": 2026, "month": 8, "day": 27},
                        "company_no": "2330",
                        "order_status": 20,
                    }
                ],
                "stk_trade_list": [],
            }
        return {}


def make_env(tmp_path: Path, logged_in: bool = True):
    settings = Settings(
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        query=QueryConfig(timeout=0.5),
        account=AccountConfig(account="S98875005091", password="1234"),
    )
    store = StateStore(settings.state.db_path)
    adapter = FakeAdapter(logged_in=logged_in)
    service = QueryService(adapter, settings, store=store)
    return store, adapter, service


def run(coro):
    return asyncio.run(coro)


def test_recovery_reconciles_stock_orders(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    store.save_stock_order(
        client_order_id="C001",
        request={"client_order_id": "C001", "stk_code": "2330"},
        status="SUBMITTED",
        account="S98875005091",
        action="new",
        order_no="H00002",
        trade_date="2026/08/27",
    )
    result = run(run_startup_recovery(store, service, adapter))
    assert result["status"] == "ok"
    assert result["unfinished_before"] == 1
    row = store.get_stock_order("C001")
    assert row is not None
    assert row["status"] == "ACCEPTED"


def test_recovery_marks_unresolved_stock_orders_manual_review(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    store.save_stock_order(
        client_order_id="C001",
        request={"client_order_id": "C001", "stk_code": "2330"},
        status="SUBMITTED",
        account="S98875005091",
        action="new",
        order_no="H00999",
        trade_date="2026/08/27",
    )
    result = run(run_startup_recovery(store, service, adapter))
    assert result["status"] == "ok"
    row = store.get_stock_order("C001")
    assert row is not None
    assert row["status"] == "NEED_MANUAL_REVIEW"
    unresolved = store.list_unresolved_recovery()
    assert any(item["source"] == "stock_orders" and item["client_order_id"] == "C001" for item in unresolved)


def test_resolve_unresolved_stock_order(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_stock_order(
        client_order_id="C001",
        request={"client_order_id": "C001", "stk_code": "2330"},
        status="NEED_MANUAL_REVIEW",
        account="S98875005091",
        action="new",
    )
    store.resolve_stock_order("C001", status="FILLED", note="manual confirm")
    row = store.get_stock_order("C001")
    assert row is not None
    assert row["status"] == "FILLED"
    assert row["data"].get("need_manual_review") is False
