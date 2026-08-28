"""M4 feature 2: client_order_id idempotency store."""

from __future__ import annotations

from pathlib import Path

from stock_broker_tw.state.store import StateStore


def test_stock_order_roundtrip_and_idempotent_key(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    request = {
        "client_order_id": "C001",
        "action": "new",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 100.0,
        "quantity": 10,
    }
    store.save_stock_order(client_order_id="C001", request=request, status="PENDING", account="S98875005091")
    row = store.get_stock_order("C001")
    assert row is not None
    assert row["client_order_id"] == "C001"
    assert row["status"] == "PENDING"
    assert row["request"]["stk_code"] == "2330"

    store.update_stock_order(
        "C001",
        status="ACCEPTED",
        order_no="H00001",
        trade_date="2026/08/28",
        data={"reply_code": 0},
    )
    row = store.get_stock_order("C001")
    assert row["order_no"] == "H00001"
    assert row["data"]["reply_code"] == 0
    assert store.get_stock_order_by_order_no("H00001")["client_order_id"] == "C001"


def test_list_stock_orders_filters(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_stock_order(client_order_id="C1", request={"client_order_id": "C1"}, status="PENDING", account="A")
    store.save_stock_order(client_order_id="C2", request={"client_order_id": "C2"}, status="FILLED", account="A")
    store.save_stock_order(client_order_id="C3", request={"client_order_id": "C3"}, status="PENDING", account="B")
    assert [r["client_order_id"] for r in store.list_stock_orders()] == ["C1", "C2", "C3"]
    assert [r["client_order_id"] for r in store.list_stock_orders(status="PENDING")] == ["C1", "C3"]
    assert [r["client_order_id"] for r in store.list_stock_orders(account="B")] == ["C3"]
