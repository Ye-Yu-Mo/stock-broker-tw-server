"""Tests for SQLite state persistence (snapshots, orders, trades, reports)."""

from __future__ import annotations

from pathlib import Path

from stock_broker_tw.state.store import StateStore


def test_state_store_creates_database_automatically(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "state.db"
    store = StateStore(db_path)
    store.save_snapshot("positions", {"items": []}, account="S98875005091")
    assert db_path.exists()
    assert store.get_latest_snapshot("positions")["data"] == {"items": []}


def test_snapshot_latest_wins(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_snapshot("positions", {"items": [1]}, account="A")
    store.save_snapshot("positions", {"items": [2]}, account="A")
    latest = store.get_latest_snapshot("positions", account="A")
    assert latest is not None
    assert latest["data"] == {"items": [2]}


def test_orders_and_trades_roundtrip(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_orders(
        [
            {
                "order_no": "H00001",
                "account": "S98875005091",
                "trade_date": {"year": 2026, "month": 8, "day": 27},
                "company_no": "2330",
                "order_status": 20,
                "bs": "B",
            }
        ]
    )
    orders = store.get_orders(order_no="H00001")
    assert len(orders) == 1
    assert orders[0]["order_no"] == "H00001"
    assert orders[0]["data"]["order_status"] == 20

    store.save_trades(
        [
            {
                "order_no": "H00001",
                "account": "S98875005091",
                "trade_date": "2026/08/27",
                "company_no": "2330",
                "s_price": 105.0,
            }
        ]
    )
    trades = store.get_trades(order_no="H00001")
    assert len(trades) == 1
    assert trades[0]["s_price"] == 105.0


def test_reports_roundtrip_and_replace(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_reports(
        "GetRealReportMerge",
        [
            {
                "order_no": "H00001",
                "order_date": {"year": 2026, "month": 8, "day": 27},
                "ok_qty": 100,
            }
        ],
    )
    reports = store.get_reports("GetRealReportMerge")
    assert len(reports) == 1
    assert reports[0]["ok_qty"] == 100

    store.save_reports(
        "GetRealReportMerge",
        [
            {
                "order_no": "H00001",
                "order_date": {"year": 2026, "month": 8, "day": 27},
                "ok_qty": 200,
            }
        ],
    )
    reports = store.get_reports("GetRealReportMerge")
    assert len(reports) == 1
    assert reports[0]["ok_qty"] == 200


def test_get_unfinished_orders(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_orders(
        [
            {"order_no": "H00001", "order_status": 0},
            {"order_no": "H00002", "order_status": 20},
            {"order_no": "H00003", "order_status": 30},
        ]
    )
    unfinished = store.get_unfinished_orders()
    assert [item["order_no"] for item in unfinished] == ["H00001"]


def test_in_memory_store_keeps_data_across_calls() -> None:
    store = StateStore(":memory:")
    store.save_snapshot("positions", {"stk_store_list": []}, account="S")
    latest = store.get_latest_snapshot("positions")
    assert latest is not None
    assert latest["data"] == {"stk_store_list": []}
