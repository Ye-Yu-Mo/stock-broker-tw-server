"""M6 recovery enhancements for M4 stock_orders."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from stock_broker_tw.config import AccountConfig, QueryConfig, Settings, StateConfig
from stock_broker_tw.service.query import QueryService
from stock_broker_tw.state.recovery import run_startup_recovery
from stock_broker_tw.state.store import MockAccountError, StateStore


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


def test_resolve_mock_filled_requires_settlement_path(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "mock-resolve.db")
    store.init_mock_account("MOCK-RECOVERY", cash=10_000.0, positions=[])
    store.claim_stock_order(
        "MOCK-RECOVERY-001",
        {
            "client_order_id": "MOCK-RECOVERY-001",
            "action": "new",
            "account": "MOCK-RECOVERY",
            "stk_code": "2330",
            "quantity": 10,
            "mock": True,
        },
        account="MOCK-RECOVERY",
        action="new",
        mock=True,
    )

    with pytest.raises(MockAccountError, match="settle"):
        store.resolve_stock_order("MOCK-RECOVERY-001", status="FILLED")

    assert store.get_stock_order("MOCK-RECOVERY-001")["status"] == "PENDING"
    assert store.get_mock_account("MOCK-RECOVERY")["cash"] == 10_000.0


def test_recovery_marks_pending_mock_order_without_querying_broker(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    store.save_stock_order(
        client_order_id="MOCK-PENDING",
        request={
            "client_order_id": "MOCK-PENDING",
            "stk_code": "2330",
            "mock": True,
        },
        status="PENDING",
        account="MOCK",
        action="new",
        data={"mock": True},
    )

    result = run(run_startup_recovery(store, service, adapter))

    assert result["status"] == "ok"
    row = store.get_stock_order("MOCK-PENDING")
    assert row["status"] == "NEED_MANUAL_REVIEW"
    assert row["data"]["mock"] is True
    assert "mock" not in adapter.calls


def test_recovery_marks_pending_mock_order_before_login(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path, logged_in=False)
    store.save_stock_order(
        client_order_id="MOCK-PENDING-OFFLINE",
        request={
            "client_order_id": "MOCK-PENDING-OFFLINE",
            "stk_code": "2330",
            "mock": True,
        },
        status="PENDING",
        account="MOCK-RECOVERY",
        action="new",
        data={"mock": True},
    )

    result = run(run_startup_recovery(store, service, adapter))

    assert result["status"] == "skipped"
    assert result["unfinished_before"] == 1
    assert result["unfinished_after"] == 1
    assert result["reconciled"] is False
    assert store.get_stock_order("MOCK-PENDING-OFFLINE")["status"] == "NEED_MANUAL_REVIEW"
    assert adapter.calls == []


def test_mock_recovery_isolated_when_real_query_fails(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    store.save_stock_order(
        client_order_id="REAL-PENDING",
        request={"client_order_id": "REAL-PENDING", "stk_code": "2330"},
        status="SUBMITTED",
        account="S98875005091",
        action="new",
        order_no="H00099",
    )
    store.save_stock_order(
        client_order_id="MOCK-PENDING-MIXED",
        request={"client_order_id": "MOCK-PENDING-MIXED", "stk_code": "2330", "mock": True},
        status="PENDING",
        account="MOCK-RECOVERY",
        action="new",
        data={"mock": True},
    )

    def fail_query(*args, **kwargs):
        raise RuntimeError("broker unavailable")

    adapter.query = fail_query
    result = run(run_startup_recovery(store, service, adapter))

    assert result["status"] == "error"
    assert store.get_stock_order("MOCK-PENDING-MIXED")["status"] == "NEED_MANUAL_REVIEW"


def test_recovery_matches_unresolved_order_by_broker_basket_no(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    store.save_stock_order(
        client_order_id="TIMEOUT-BASKET",
        request={
            "client_order_id": "TIMEOUT-BASKET",
            "broker_basket_no": "B" + "a" * 31,
            "stk_code": "2330",
        },
        status="NEED_MANUAL_REVIEW",
        account="S98875005091",
        action="new",
        data={"execution_uncertain": True},
    )
    store.save_orders(
        [
            {
                "order_no": "H00003",
                "basket_no": "B" + "a" * 31,
                "account": "S98875005091",
                "trade_date": "2026/09/09",
                "company_no": "2330",
                "status": "20",
            }
        ]
    )

    result = run(run_startup_recovery(store, service, adapter))

    assert result["status"] == "ok"
    row = store.get_stock_order("TIMEOUT-BASKET")
    assert row["status"] == "ACCEPTED"
    assert row["order_no"] == "H00003"


def test_recovery_promotes_legacy_timeout_failure(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    broker_basket_no = "B" + "b" * 31
    store.save_stock_order(
        client_order_id="LEGACY-TIMEOUT",
        request={
            "client_order_id": "LEGACY-TIMEOUT",
            "broker_basket_no": broker_basket_no,
            "stk_code": "2330",
        },
        status="FAILED",
        account="S98875005091",
        action="new",
        data={"error": "timed out after 10.0s waiting for SendStockOrder response"},
    )
    store.save_orders(
        [
            {
                "order_no": "H00004",
                "basket_no": broker_basket_no,
                "account": "S98875005091",
                "trade_date": "2026/09/09",
                "company_no": "2330",
                "status": "20",
            }
        ]
    )

    result = run(run_startup_recovery(store, service, adapter))

    assert result["status"] == "ok"
    row = store.get_stock_order("LEGACY-TIMEOUT")
    assert row["status"] == "ACCEPTED"
    assert row["order_no"] == "H00004"
    assert row["data"].get("need_manual_review") is False


def test_recovery_matches_transformed_broker_basket_by_order_fields(tmp_path: Path) -> None:
    store, adapter, service = make_env(tmp_path)
    local_basket = "B" + "c" * 31
    broker_basket = "Ewodr" + local_basket[:27]
    store.save_stock_order(
        client_order_id="TRANSFORMED-BASKET",
        request={
            "client_order_id": "TRANSFORMED-BASKET",
            "broker_basket_no": local_basket,
            "stk_code": "2330",
            "side": "S",
            "price": 45.5,
            "quantity": 1,
        },
        status="NEED_MANUAL_REVIEW",
        account="S98875005091",
        action="new",
        data={"execution_uncertain": True},
    )
    store.save_orders(
        [
            {
                "order_no": "H00005",
                "basket_no": broker_basket,
                "account": "S98875005091",
                "trade_date": "2026/09/09",
                "company_no": "2330",
                "status": "20",
                "bs": "S",
                "price": 45.5,
                "order_qty": 1,
            }
        ]
    )

    result = run(run_startup_recovery(store, service, adapter))

    assert result["status"] == "ok"
    row = store.get_stock_order("TRANSFORMED-BASKET")
    assert row["status"] == "ACCEPTED"
    assert row["order_no"] == "H00005"
