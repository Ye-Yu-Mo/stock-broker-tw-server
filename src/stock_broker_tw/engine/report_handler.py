"""M4 report-driven order status updates.

``RR_RealReport`` / ``RR_RealReportMerge`` events from the Yuanta adapter are
processed here.  The handler maps broker report codes to local order statuses,
persists the update, and broadcasts both the processed report and the
``order.updated`` event.
"""

from __future__ import annotations

import logging
from typing import Any

from stock_broker_tw.engine.state import (
    InvalidOrderStateTransition,
    OrderStateMachine,
    OrderStatus,
    StockOrderState,
)
from stock_broker_tw.state.store import StateStore
from stock_broker_tw.yuanta.events import YuantaEvent
from stock_broker_tw.yuanta.serializer import to_dict

logger = logging.getLogger(__name__)

_REPORT_TYPES = {"RR_RealReport": "real_report", "RR_RealReportMerge": "real_report_merge"}
_M3_STATUS = {
    "PENDING": "0",
    "SUBMITTED": "0",
    "ACCEPTED": "20",
    "PARTIALLY_FILLED": "20",
    "FILLED": "20",
    "CANCELLED": "30",
    "REJECTED": "10",
    "FAILED": "24",
    "NEED_MANUAL_REVIEW": "0",
}

# Status code sources:
# - docs/API/元大API說明文件 43.md and 44.md: RR_RealReport
#   OrderStatus = 0 委託成功, 1 委託失敗, 2 取消成功, 3 取消失敗,
#   4 減量成功, 5 減量失敗, 6 查詢成功, 7 查詢失敗, 8 已成交,
#   18 委託收到, 20 改價成功, 21 改價失敗, 23 取消成交, 24 委託失效,
#   25 價穩失效
# - docs/API/元大API說明文件 45.md and 46.md: RR_RealReportMerge
#   LastOrderStatus additionally uses 10 組合成功, 11 拆解成功, etc.
_REAL_REPORT_CANCEL_STATUSES = frozenset({2, 23, 30})
_REAL_REPORT_REJECT_STATUSES = frozenset({1, 3, 5, 7, 10, 21})
_REAL_REPORT_FAIL_STATUSES = frozenset({24, 25})
_REAL_REPORT_FILL_ANY_STATUSES = frozenset({8})
_REAL_REPORT_FILL_STATUSES = frozenset({0, 4, 6, 18, 20})

_MERGE_CANCEL_STATUSES = frozenset({2, 23, 30})
_MERGE_DIRECT_REJECT_STATUSES = frozenset({10})
_MERGE_LAST_REJECT_STATUSES = frozenset({1, 3, 5, 7, 21})
_MERGE_FAIL_STATUSES = frozenset({24, 25})
_MERGE_FILL_ANY_STATUSES = frozenset({8})
_MERGE_FILL_STATUSES = frozenset({20})
_MERGE_SUBMITTED_STATUSES = frozenset({0})


def _is_mock_order(order: dict[str, Any]) -> bool:
    request = order.get("request") or {}
    data = order.get("data") or {}
    return bool(request.get("mock") or data.get("mock"))


class ReportHandler:
    """Translate raw real-report events into persisted order updates."""

    def __init__(self, store: StateStore, broadcaster: Any = None, notifier: Any = None) -> None:
        self.store = store
        self.broadcaster = broadcaster
        self.notifier = notifier
        self._state_machine = OrderStateMachine()

    async def handle_event(self, event: YuantaEvent) -> dict[str, Any] | None:
        event_type = _REPORT_TYPES.get(event.str_index)
        if event_type is None:
            return None

        data = to_dict(event.obj_value)
        if not isinstance(data, dict):
            return None

        reports = self._extract_reports(data)
        processed: list[dict[str, Any]] = []
        for report in reports:
            result = await self.handle_report(report, report_type=event_type, raw_type=event.str_index)
            if result is not None:
                processed.append(result)
        return {"event_type": event_type, "processed": processed}

    def _extract_reports(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("real_report_list", "real_report_merge_list"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if data.get("order_no") is not None or data.get("basket_no") is not None:
            return [data]
        return []

    async def handle_report(
        self,
        report: dict[str, Any],
        report_type: str = "real_report",
        raw_type: str = "RR_RealReport",
    ) -> dict[str, Any] | None:
        self.store.save_reports(raw_type, [report])

        client_order_id = report.get("client_order_id") or report.get("basket_no")
        order_no = report.get("order_no")
        if order_no is not None:
            order_no = str(order_no)
        row = None
        if client_order_id:
            row = self.store.get_stock_order(str(client_order_id))
        if row is None and order_no:
            row = self.store.get_stock_order_by_order_no(str(order_no))
        if row is None and report.get("basket_no"):
            row = self.store.get_stock_order_by_basket_no(str(report["basket_no"]))
        if row is None:
            payload = {
                "type": report_type,
                "data": {**report, "status": None, "client_order_id": client_order_id},
            }
            await self._broadcast(payload)
            return None
        if _is_mock_order(row):
            # Real broker reports must never settle or mutate a Mock order.
            payload = {
                "type": report_type,
                "data": {**report, "status": None, "client_order_id": client_order_id},
            }
            await self._broadcast(payload)
            return None
        report_account = report.get("account") or report.get("Account")
        if (
            report_account is not None
            and row.get("account") is not None
            and str(report_account) != str(row["account"])
        ):
            # A broker report from another account must not update this row.
            payload = {
                "type": report_type,
                "data": {**report, "status": None, "client_order_id": client_order_id},
            }
            await self._broadcast(payload)
            return None

        status = self._map_report_status(report, report_type=report_type)
        if status is None:
            status = OrderStatus.NEED_MANUAL_REVIEW

        state = StockOrderState.from_dict(
            {
                **row,
                "request": row.get("request"),
                "data": row.get("data") or {},
            }
        )
        try:
            self._state_machine.transition(state, status, reason=f"{raw_type} report")
            final_status = state.status.value
        except Exception:
            final_status = OrderStatus.NEED_MANUAL_REVIEW.value

        report_trade_date = report.get("trade_date") or report.get("order_date")
        row_trade_date = row.get("trade_date") or report_trade_date
        data = dict(report)
        if report_type == "real_report_merge":
            ok_qty = int(report.get("ok_qty") or 0)
            if ok_qty:
                data["filled_qty"] = ok_qty
                data["avg_price"] = report.get("avg_deal_price")
        data["transitions"] = state.transitions
        if final_status == OrderStatus.NEED_MANUAL_REVIEW.value:
            data["last_error"] = "unknown report status"
            data["need_manual_review"] = True
        try:
            self.store.update_stock_order(
                row["client_order_id"],
                status=final_status,
                order_no=row.get("order_no") or order_no,
                trade_date=row_trade_date,
                data=data,
                request=row.get("request"),
                account=row.get("account"),
                action=row.get("action"),
            )
        except InvalidOrderStateTransition:
            # Never let a late/unknown report roll back a final order state.
            final_status = row["status"]
            data["last_error"] = "ignored illegal report status transition"
        # If several local client_order_id rows map to the same broker OrderNo
        # (e.g. an original order plus a cancel/replace operation), keep them all
        # in sync so any client_order_id lookup sees the latest report status.
        if (
            (order_no or row.get("order_no"))
            and (not client_order_id or row.get("action") in {None, "new"})
        ):
            mapped_order_no = order_no or row.get("order_no")
            for other in self.store.list_stock_orders():
                if (
                    other["client_order_id"] != row["client_order_id"]
                    and other.get("order_no") == mapped_order_no
                ):
                    try:
                        self.store.update_stock_order(
                            other["client_order_id"],
                            status=final_status,
                            order_no=mapped_order_no,
                            trade_date=other.get("trade_date") or row.get("trade_date"),
                            data=data,
                            request=other.get("request"),
                            account=other.get("account"),
                            action=other.get("action"),
                        )
                    except InvalidOrderStateTransition:
                        # A cancel/replace row may already be final even when
                        # the original order receives a later broker report.
                        logger.info(
                            "skip linked order status update: client_order_id=%s status=%s",
                            other["client_order_id"],
                            other.get("status"),
                        )
                    except Exception:
                        # A single stale/locked linked row must not discard the
                        # report for the primary order or stop the event consumer.
                        logger.exception(
                            "linked order update failed: client_order_id=%s",
                            other["client_order_id"],
                        )

        updated = self.store.get_stock_order(row["client_order_id"]) or {}
        if self.notifier is not None:
            try:
                self.notifier.send(
                    "order.status",
                    "订单状态变化",
                    {
                        "client_order_id": row["client_order_id"],
                        "status": final_status,
                        "order_no": order_no or row.get("order_no"),
                        "trade_date": row_trade_date,
                        "report_type": report_type,
                    },
                )
            except Exception:
                pass
        self.store.save_orders(
            [
                {
                    "order_no": order_no or row.get("order_no") or "",
                    "account": row.get("account"),
                    "trade_date": row_trade_date or "",
                    "company_no": report.get("company_no") or (row.get("request") or {}).get("stk_code"),
                    "status": _M3_STATUS.get(final_status, final_status),
                    "client_order_id": row["client_order_id"],
                    "basket_no": row["client_order_id"],
                    "order_qty": report.get("order_qty"),
                    "ok_qty": report.get("ok_qty"),
                    "price": report.get("price"),
                    "bs": report.get("bs"),
                }
            ]
        )

        payload = {
            "type": report_type,
            "data": {
                **report,
                "client_order_id": row["client_order_id"],
                "status": final_status,
            },
        }
        if self.broadcaster is not None:
            await self._broadcast(payload)
            await self._broadcast({"type": "order.updated", "data": updated})
        return updated

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        method = getattr(self.broadcaster, "broadcast_json", None)
        if callable(method):
            result = method(payload)
            if hasattr(result, "__await__"):
                await result

    @staticmethod
    def _map_report_status(
        report: dict[str, Any],
        report_type: str = "real_report",
    ) -> OrderStatus | None:
        try:
            order_status_raw = report.get("order_status")
            last_status_raw = report.get("last_order_status")
            order_status = int(order_status_raw) if order_status_raw is not None else -1
            last_status = int(last_status_raw) if last_status_raw is not None else -1
        except (TypeError, ValueError):
            return None
        ok_qty = int(report.get("ok_qty") or 0)
        order_qty = int(report.get("order_qty") or 0)

        def fill_status() -> OrderStatus:
            if ok_qty > 0 and ok_qty >= order_qty:
                return OrderStatus.FILLED
            if ok_qty > 0:
                return OrderStatus.PARTIALLY_FILLED
            return OrderStatus.ACCEPTED

        # RR_RealReport uses its own status codes; RR_RealReportMerge uses the
        # merged order status codes.  Both mappings are table-driven using the
        # constants above, with sources cited in the module docstring.
        if report_type == "real_report":
            if order_status in _REAL_REPORT_CANCEL_STATUSES:
                return OrderStatus.CANCELLED
            if order_status in _REAL_REPORT_REJECT_STATUSES:
                return OrderStatus.REJECTED
            if order_status in _REAL_REPORT_FAIL_STATUSES:
                return OrderStatus.FAILED
            if order_status in _REAL_REPORT_FILL_ANY_STATUSES or last_status in _REAL_REPORT_FILL_ANY_STATUSES:
                return fill_status()
            if order_status in _REAL_REPORT_FILL_STATUSES:
                return fill_status()
            return None

        # RR_RealReportMerge / default mapping.
        if order_status in _MERGE_CANCEL_STATUSES:
            return OrderStatus.CANCELLED
        if order_status in _MERGE_DIRECT_REJECT_STATUSES:
            return OrderStatus.REJECTED
        if order_status in _MERGE_FAIL_STATUSES:
            return OrderStatus.FAILED
        if order_status in _MERGE_FILL_ANY_STATUSES or last_status in _MERGE_FILL_ANY_STATUSES:
            return fill_status()
        if last_status == 2:
            return OrderStatus.CANCELLED
        if last_status in _MERGE_LAST_REJECT_STATUSES:
            return OrderStatus.REJECTED
        if order_status in _MERGE_FILL_STATUSES:
            return fill_status()
        if order_status in _MERGE_SUBMITTED_STATUSES:
            return OrderStatus.SUBMITTED
        return None


# Common alias.
ReportProcessor = ReportHandler

__all__ = ["ReportHandler", "ReportProcessor"]
