"""Tests for startup recovery reconciliation."""

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
                        "order_no": "H00001",
                        "account": "S98875005091",
                        "trade_date": {"year": 2026, "month": 8, "day": 27},
                        "company_no": "2330",
                        "order_status": 20,
                    }
                ],
                "stk_trade_list": [],
                "fut_order_list": [],
                "fut_trade_list": [],
                "ov_stk_order_list": [],
                "ov_stk_trade_list": [],
                "ov_fut_order_list": [],
                "ov_fut_trade_list": [],
            }
        return {"real_report_merge_list": []}


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


def test_recovery_skips_when_not_logged_in(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path, logged_in=False)
    result = run(run_startup_recovery(store, service, adapter))
    assert result["status"] == "skipped"
    assert adapter.calls == []


def test_recovery_reconciles_unfinished_orders(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path, logged_in=True)
    store.save_orders(
        [
            {
                "order_no": "H00001",
                "account": "S98875005091",
                "trade_date": {"year": 2026, "month": 8, "day": 27},
                "company_no": "2330",
                "order_status": 0,
            }
        ]
    )
    result = run(run_startup_recovery(store, service, adapter))
    assert result["status"] == "ok"
    assert result["unfinished_before"] == 1
    assert result["unfinished_after"] == 0
    assert "GetOrderTradeReport" in adapter.calls
    orders = store.get_orders(order_no="H00001")
    assert orders[0]["data"]["order_status"] == 20


class FakeAdapterStillUnfinished(FakeAdapter):
    def query(self, function_name: str, **params):
        self.calls.append(function_name)
        if function_name == "GetOrderTradeReport":
            return {
                "stk_order_list": [
                    {
                        "order_no": "H00001",
                        "account": "S98875005091",
                        "trade_date": {"year": 2026, "month": 8, "day": 27},
                        "company_no": "2330",
                        "order_status": 0,
                    }
                ],
                "stk_trade_list": [],
                "fut_order_list": [],
                "fut_trade_list": [],
                "ov_stk_order_list": [],
                "ov_stk_trade_list": [],
                "ov_fut_order_list": [],
                "ov_fut_trade_list": [],
            }
        return {"real_report_merge_list": []}


def test_recovery_marks_unresolved_orders_manual_review(tmp_path: Path) -> None:
    settings = Settings(
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        query=QueryConfig(timeout=0.5),
        account=AccountConfig(account="S98875005091", password="1234"),
    )
    store = StateStore(settings.state.db_path)
    adapter = FakeAdapterStillUnfinished(logged_in=True)
    service = QueryService(adapter, settings, store=store)
    store.save_orders(
        [
            {
                "order_no": "H00001",
                "account": "S98875005091",
                "trade_date": {"year": 2026, "month": 8, "day": 27},
                "company_no": "2330",
                "order_status": 0,
            }
        ]
    )
    result = run(run_startup_recovery(store, service, adapter))
    assert result["status"] == "ok"
    assert result["unfinished_after"] == 1
    orders = store.get_orders(order_no="H00001")
    assert orders[0]["status"] == "NEED_MANUAL_REVIEW"
