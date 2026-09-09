"""Startup recovery: reconcile local unfinished orders with Yuanta reports."""

from __future__ import annotations

import logging
from typing import Any

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.service.query import QueryService
from stock_broker_tw.state.store import StateStore

logger = logging.getLogger(__name__)


async def run_startup_recovery(
    store: StateStore,
    query_service: QueryService,
    adapter: Any,
    settings: Any = None,
    audit: AuditLogger | None = None,
    notifier: Any = None,
) -> dict[str, Any]:
    """Reconcile unfinished orders after service restart.

    The function is best-effort: it never raises.  It handles both the M3
    ``orders`` table and the M4 ``stock_orders`` table.  If the adapter is not
    logged in or has no query support, it returns a skipped summary.
    """
    if not getattr(adapter, "logged_in", False):
        logger.info("startup recovery skipped: adapter is not logged in")
        return _skip_without_broker(store, "not_logged_in")

    query_method = getattr(adapter, "query", None)
    if not callable(query_method):
        logger.info("startup recovery skipped: adapter has no query support")
        return _skip_without_broker(store, "no_query_support")

    try:
        unfinished_orders = store.get_unfinished_orders()
        unfinished_stock_orders = store.get_unfinished_stock_orders()
        mock_stock_orders = [
            order for order in unfinished_stock_orders if _is_mock_order(order)
        ]
        broker_stock_orders = [
            order for order in unfinished_stock_orders if not _is_mock_order(order)
        ]
        unfinished_before = len(unfinished_orders) + len(unfinished_stock_orders)
        logger.info(
            "startup recovery: found %s unfinished local order(s) (%s legacy, %s M4)",
            unfinished_before,
            len(unfinished_orders),
            len(unfinished_stock_orders),
        )
        if not unfinished_before:
            logger.info("startup recovery: no unfinished orders to reconcile")
            return {
                "status": "ok",
                "unfinished_before": 0,
                "unfinished_after": 0,
                "reconciled": True,
                "unresolved_orders": 0,
                "unresolved_stock_orders": 0,
            }

        # Mock orders never go through the broker reconciliation path.  A
        # process can stop after claiming an order but before its atomic fill;
        # keep that uncertainty explicit for manual resolution before querying
        # the real broker.
        for order in mock_stock_orders:
            data = dict(order.get("data") or {})
            data.update({"mock": True, "need_manual_review": True})
            data.setdefault("recovery_reason", "mock order was pending at restart")
            store.update_stock_order(
                order["client_order_id"],
                status="NEED_MANUAL_REVIEW",
                order_no=order.get("order_no"),
                trade_date=order.get("trade_date"),
                data=data,
            )

        if unfinished_orders or broker_stock_orders:
            await query_service.order_trade_reports()
            try:
                await query_service.real_reports_merge()
            except Exception as exc:  # noqa: BLE001 - merge is supplementary
                logger.warning("startup recovery: real-report-merge refresh failed: %s", exc)

        # M4 stock orders: try to map refreshed legacy report status back to the
        # M4 order row.  If no mapping is available (or the report still says
        # submitted), mark the row for manual review.  A concrete final or
        # accepted status from the broker is considered resolved.
        for order in store.get_unfinished_stock_orders():
            mapped = _reconcile_stock_order_from_legacy(store, order)
            if mapped is None or mapped in {"PENDING", "SUBMITTED", "NEED_MANUAL_REVIEW"}:
                data = dict(order.get("data") or {})
                data["need_manual_review"] = True
                store.update_stock_order(
                    order["client_order_id"],
                    status="NEED_MANUAL_REVIEW",
                    order_no=order.get("order_no"),
                    trade_date=order.get("trade_date"),
                    data=data,
                )

        # M3 legacy orders: mark any still-unfinished rows for manual review.
        for order in store.get_unfinished_orders():
            order["status"] = "NEED_MANUAL_REVIEW"
            store.save_orders([order])

        all_unresolved = store.list_unresolved_recovery()
        unresolved_stock_orders = sum(
            1 for item in all_unresolved if item["source"] == "stock_orders"
        )
        unresolved_orders = len(all_unresolved) - unresolved_stock_orders
        unfinished_after = len(store.get_unfinished_orders()) + len(store.get_unfinished_stock_orders())
        summary = {
            "status": "ok",
            "unfinished_before": unfinished_before,
            "unfinished_after": unfinished_after,
            "reconciled": unfinished_after == 0 and len(all_unresolved) == 0,
            "unresolved_orders": unresolved_orders,
            "unresolved_stock_orders": unresolved_stock_orders,
        }
        logger.info(
            "startup recovery: finished, %s unfinished before, %s unresolved after",
            unfinished_before,
            len(all_unresolved),
        )
        if audit is not None:
            audit.record("recovery.startup", result="ok", **summary)
        return summary
    except Exception as exc:  # noqa: BLE001 - startup must not crash
        logger.warning("startup recovery failed: %s", exc)
        if audit is not None:
            audit.record("recovery.startup", result="error", error=str(exc))
        if notifier is not None:
            try:
                notifier.send(
                    "recovery.error",
                    "启动恢复异常",
                    {"error": str(exc)},
                )
            except Exception:
                pass
        return {"status": "error", "error": str(exc)}


def _skip_without_broker(store: StateStore, reason: str) -> dict[str, Any]:
    """Mark pending Mock work for review without touching the broker."""
    try:
        unfinished_orders = store.get_unfinished_orders()
        unfinished_stock_orders = store.get_unfinished_stock_orders()
        mock_orders = [order for order in unfinished_stock_orders if _is_mock_order(order)]
        for order in mock_orders:
            data = dict(order.get("data") or {})
            data.update({"mock": True, "need_manual_review": True})
            data.setdefault("recovery_reason", f"mock order pending while {reason}")
            store.update_stock_order(
                order["client_order_id"],
                status="NEED_MANUAL_REVIEW",
                order_no=order.get("order_no"),
                trade_date=order.get("trade_date"),
                data=data,
            )
        unresolved = store.list_unresolved_recovery()
        unresolved_stock_orders = sum(
            1 for item in unresolved if item["source"] == "stock_orders"
        )
        return {
            "status": "skipped",
            "reason": reason,
            "unfinished_before": len(unfinished_orders) + len(unfinished_stock_orders),
            "unfinished_after": len(store.get_unfinished_orders())
            + len(store.get_unfinished_stock_orders()),
            "reconciled": len(unresolved) == 0,
            "unresolved_orders": len(unresolved) - unresolved_stock_orders,
            "unresolved_stock_orders": unresolved_stock_orders,
        }
    except Exception as exc:  # noqa: BLE001 - recovery must not crash startup
        logger.warning("startup recovery skip handling failed: %s", exc)
        return {"status": "skipped", "reason": reason}


def _reconcile_stock_order_from_legacy(store: StateStore, order: dict[str, Any]) -> str | None:
    """Map a refreshed M3 order status back to an M4 stock order, if possible."""
    if order.get("status") == "FAILED" and _is_uncertain_order(order):
        data = dict(order.get("data") or {})
        data["need_manual_review"] = True
        store.update_stock_order(
            order["client_order_id"],
            status="NEED_MANUAL_REVIEW",
            data=data,
        )
        order = store.get_stock_order(order["client_order_id"]) or order
    order_no = order.get("order_no")
    trade_date = order.get("trade_date")
    legacy_rows = store.get_orders(order_no=str(order_no), trade_date=trade_date) if order_no else []
    if not legacy_rows:
        request = order.get("request") or {}
        data = order.get("data") or {}
        basket_no = request.get("broker_basket_no") or data.get("broker_basket_no")
        if basket_no:
            legacy_rows = [
                row
                for row in store.get_orders()
                if (row.get("data") or {}).get("basket_no") == basket_no
            ]
            if not legacy_rows:
                candidates = [
                    row for row in store.get_orders() if _legacy_matches_order(row, order)
                ]
                if len(candidates) == 1:
                    legacy_rows = candidates
    if not legacy_rows:
        return None
    legacy = legacy_rows[-1]
    order_no = order_no or legacy.get("order_no")
    status = str(legacy.get("status") or legacy.get("data", {}).get("order_status") or "")
    m4_status = _M3_TO_M4.get(status)
    if m4_status is None:
        return None
    data = dict(order.get("data") or {})
    data["recovery_from_legacy"] = True
    if m4_status in {"ACCEPTED", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED", "FAILED"}:
        data["need_manual_review"] = False
        data["execution_uncertain"] = False
    store.update_stock_order(
        order["client_order_id"],
        status=m4_status,
        order_no=str(order_no),
        trade_date=trade_date or legacy.get("trade_date"),
        data=data,
    )
    return m4_status


def _legacy_matches_order(legacy: dict[str, Any], order: dict[str, Any]) -> bool:
    request = order.get("request") or {}
    if not isinstance(request, dict):
        return False
    if legacy.get("account") and order.get("account") and legacy["account"] != order["account"]:
        return False
    symbol = request.get("stk_code") or request.get("StkCode")
    if symbol and str(legacy.get("company_no") or "") != str(symbol):
        return False
    side = request.get("side") or request.get("buy_sell") or request.get("BuySell")
    if side and str(legacy.get("bs") or "").upper() != str(side).upper():
        return False
    requested_price = request.get("price")
    legacy_price = legacy.get("price")
    if requested_price is not None and legacy_price is not None:
        try:
            if float(requested_price) != float(legacy_price):
                return False
        except (TypeError, ValueError):
            return False
    requested_quantity = request.get("quantity") or request.get("OrderQty")
    legacy_quantity = legacy.get("order_qty")
    if requested_quantity and legacy_quantity is not None:
        try:
            if int(requested_quantity) != int(legacy_quantity):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _is_uncertain_order(order: dict[str, Any]) -> bool:
    data = order.get("data") or {}
    if not isinstance(data, dict):
        return False
    return bool(data.get("execution_uncertain")) or "timed out" in str(data.get("error") or "").lower()


def _is_mock_order(order: dict[str, Any]) -> bool:
    request = order.get("request") or {}
    data = order.get("data") or {}
    return bool(request.get("mock") or data.get("mock"))


_M3_TO_M4 = {
    "0": "SUBMITTED",
    "10": "REJECTED",
    "20": "ACCEPTED",
    "24": "FAILED",
    "25": "FAILED",
    "30": "CANCELLED",
}


__all__ = ["run_startup_recovery"]
