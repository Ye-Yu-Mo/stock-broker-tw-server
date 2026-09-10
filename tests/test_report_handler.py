"""M4 feature 7: report-driven order state updates."""

from __future__ import annotations

import asyncio
from pathlib import Path

from stock_broker_tw.engine.report_handler import ReportHandler
from stock_broker_tw.state.store import StateStore
from stock_broker_tw.yuanta.events import YuantaEvent


class FakeBroadcaster:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def broadcast_json(self, payload: dict) -> None:
        self.messages.append(payload)

    def broadcast_order_update(self, payload: dict) -> None:
        self.messages.append({"type": "order.updated", "data": payload})


def make_env(tmp_path: Path):
    store = StateStore(tmp_path / "state.db")
    broadcaster = FakeBroadcaster()
    handler = ReportHandler(store, broadcaster=broadcaster)
    return store, broadcaster, handler


def run(coro):
    return asyncio.run(coro)


def _save_order(store: StateStore, cid: str, order_no: str = "H00001") -> None:
    store.save_stock_order(
        client_order_id=cid,
        request={
            "client_order_id": cid,
            "action": "new",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 1000,
        },
        status="ACCEPTED",
        account="S98875005091",
        order_no=order_no,
        trade_date="2026/08/28",
    )


def test_real_report_merge_updates_order_and_broadcasts(tmp_path: Path) -> None:
    store, broadcaster, handler = make_env(tmp_path)
    _save_order(store, "C001")
    report = {
        "order_no": "H00001",
        "basket_no": "C001",
        "order_status": 20,
        "last_order_status": 8,
        "ok_qty": 1000,
        "order_qty": 1000,
        "avg_deal_price": 505.0,
        "account": "S98875005091",
    }
    run(handler.handle_event(YuantaEvent(2, 0, "RR_RealReportMerge", None, report)))
    row = store.get_stock_order("C001")
    assert row["status"] == "FILLED"
    assert row["data"].get("ok_qty") == 1000
    types = [m["type"] for m in broadcaster.messages]
    assert "real_report_merge" in types
    assert "order.updated" in types


def test_real_report_partial_fill(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    _save_order(store, "C001")
    report = {
        "order_no": "H00001",
        "basket_no": "C001",
        "order_status": 20,
        "last_order_status": 8,
        "ok_qty": 200,
        "order_qty": 1000,
    }
    run(handler.handle_event(YuantaEvent(2, 0, "RR_RealReport", None, report)))
    row = store.get_stock_order("C001")
    assert row["status"] == "PARTIALLY_FILLED"


def test_real_report_cancel_success_maps_to_cancelled(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    _save_order(store, "C001")
    report = {
        "order_no": "H00001",
        "basket_no": "C001",
        "order_status": 2,
        "ok_qty": 0,
        "order_qty": 1000,
    }
    run(handler.handle_event(YuantaEvent(2, 0, "RR_RealReport", None, report)))
    assert store.get_stock_order("C001")["status"] == "CANCELLED"


def test_unknown_report_marks_manual_review(tmp_path: Path) -> None:
    store, _, handler = make_env(tmp_path)
    _save_order(store, "C001")
    report = {
        "order_no": "H00001",
        "basket_no": "C001",
        "order_status": 99,
        "ok_qty": 0,
        "order_qty": 1000,
    }
    run(handler.handle_event(YuantaEvent(2, 0, "RR_RealReport", None, report)))
    assert store.get_stock_order("C001")["status"] == "NEED_MANUAL_REVIEW"


def test_report_without_local_order_is_persisted_not_crash(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    run(
        handler.handle_event(
            YuantaEvent(2, 0, "RR_RealReport", None, {"order_no": "UNKNOWN", "order_status": 20})
        )
    )
    assert len(store.get_reports("RR_RealReport")) == 1


def test_unknown_report_does_not_rollback_final_order(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    _save_order(store, "C001")
    store.update_stock_order("C001", status="FILLED", data={"filled_qty": 1000})
    report = {
        "order_no": "H00001",
        "basket_no": "C001",
        "order_status": 99,
        "ok_qty": 1000,
        "order_qty": 1000,
    }
    run(handler.handle_event(YuantaEvent(2, 0, "RR_RealReport", None, report)))
    assert store.get_stock_order("C001")["status"] == "FILLED"


def test_real_report_does_not_update_pending_mock_order(tmp_path: Path) -> None:
    store, broadcaster, handler = make_env(tmp_path)
    store.init_mock_account("MOCK-REPORT", cash=10_000.0, positions=[])
    store.claim_stock_order(
        "MOCK-REPORT-001",
        {
            "client_order_id": "MOCK-REPORT-001",
            "action": "new",
            "account": "MOCK-REPORT",
            "stk_code": "2330",
            "quantity": 10,
            "mock": True,
        },
        account="MOCK-REPORT",
        action="new",
        mock=True,
    )
    report = {
        "order_no": "H00001",
        "basket_no": "MOCK-REPORT-001",
        "order_status": 8,
        "ok_qty": 10,
        "order_qty": 10,
        "account": "MOCK-REPORT",
    }

    run(handler.handle_event(YuantaEvent(2, 0, "RR_RealReport", None, report)))

    row = store.get_stock_order("MOCK-REPORT-001")
    assert row["status"] == "PENDING"
    assert store.get_mock_account("MOCK-REPORT")["cash"] == 10_000.0
    assert store.get_trades() == []
    assert broadcaster.messages[-1]["type"] == "real_report"


def test_report_matches_broker_basket_mapping_for_long_client_id(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    client_order_id = "client-order-with-more-than-thirty-two-characters-001"
    broker_basket_no = "B" + "a" * 31
    store.save_stock_order(
        client_order_id=client_order_id,
        request={
            "client_order_id": client_order_id,
            "broker_basket_no": broker_basket_no,
            "action": "new",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 1,
        },
        status="ACCEPTED",
        account="S98875005091",
        order_no=None,
        trade_date="2026/08/28",
    )

    run(
        handler.handle_event(
            YuantaEvent(
                2,
                0,
                "RR_RealReport",
                None,
                {
                    "order_no": "H00002",
                    "basket_no": broker_basket_no,
                    "order_status": 8,
                    "ok_qty": 1,
                    "order_qty": 1,
                },
            )
        )
    )

    assert store.get_stock_order(client_order_id)["status"] == "FILLED"


def test_report_status_zero_means_accepted(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    _save_order(store, "ZERO001")

    run(
        handler.handle_event(
            YuantaEvent(
                2,
                0,
                "RR_RealReport",
                None,
                {"order_no": "H00001", "basket_no": "ZERO001", "order_status": 0, "last_order_status": 0},
            )
        )
    )

    assert store.get_stock_order("ZERO001")["status"] == "ACCEPTED"


def test_final_linked_replace_does_not_break_primary_report(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    _save_order(store, "ORIGINAL001")
    store.save_stock_order(
        client_order_id="CANCEL001",
        request={
            "client_order_id": "CANCEL001",
            "action": "cancel",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "quantity": 1000,
        },
        status="CANCELLED",
        account="S98875005091",
        action="cancel",
        order_no="H00001",
        trade_date="2026/08/28",
    )

    run(
        handler.handle_event(
            YuantaEvent(
                2,
                0,
                "RR_RealReport",
                None,
                {
                    "client_order_id": "ORIGINAL001",
                    "order_no": "H00001",
                    "basket_no": "ORIGINAL001",
                    "order_status": 8,
                    "ok_qty": 1000,
                    "order_qty": 1000,
                },
            )
        )
    )

    assert store.get_stock_order("ORIGINAL001")["status"] == "FILLED"
    assert store.get_stock_order("CANCEL001")["status"] == "CANCELLED"


def test_failed_replace_does_not_reject_original_order(tmp_path: Path) -> None:
    store, _broadcaster, handler = make_env(tmp_path)
    _save_order(store, "ORIGINAL001")
    store.save_stock_order(
        client_order_id="REPLACE001",
        request={
            "client_order_id": "REPLACE001",
            "action": "replace",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 510.0,
            "quantity": 1000,
        },
        status="SUBMITTED",
        account="S98875005091",
        action="replace",
        order_no="H00001",
        trade_date="2026/08/28",
    )

    run(
        handler.handle_event(
            YuantaEvent(
                2,
                0,
                "RR_RealReport",
                None,
                {
                    "client_order_id": "REPLACE001",
                    "order_no": "H00001",
                    "basket_no": "REPLACE001",
                    "order_status": 21,
                    "order_qty": 1000,
                },
            )
        )
    )

    assert store.get_stock_order("REPLACE001")["status"] == "REJECTED"
    assert store.get_stock_order("ORIGINAL001")["status"] == "ACCEPTED"
