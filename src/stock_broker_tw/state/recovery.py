"""Startup recovery: reconcile local unfinished orders with Yuanta reports."""

from __future__ import annotations

import logging
from typing import Any

from stock_broker_tw.service.query import QueryService
from stock_broker_tw.state.store import StateStore

logger = logging.getLogger(__name__)


async def run_startup_recovery(
    store: StateStore,
    query_service: QueryService,
    adapter: Any,
    settings: Any = None,
) -> dict[str, Any]:
    """Reconcile unfinished orders after service restart.

    The function is best-effort: it never raises.  If the adapter is not logged
    in or has no query support, it returns a skipped summary.
    """
    if not getattr(adapter, "logged_in", False):
        logger.info("startup recovery skipped: adapter is not logged in")
        return {"status": "skipped", "reason": "not_logged_in"}

    query_method = getattr(adapter, "query", None)
    if not callable(query_method):
        logger.info("startup recovery skipped: adapter has no query support")
        return {"status": "skipped", "reason": "no_query_support"}

    try:
        unfinished_before = store.get_unfinished_orders()
        logger.info(
            "startup recovery: found %s unfinished local order(s)",
            len(unfinished_before),
        )
        if not unfinished_before:
            logger.info("startup recovery: no unfinished orders to reconcile")
            return {
                "status": "ok",
                "unfinished_before": 0,
                "unfinished_after": 0,
                "reconciled": False,
            }

        await query_service.order_trade_reports()
        try:
            await query_service.real_reports_merge()
        except Exception as exc:  # noqa: BLE001 - merge is supplementary
            logger.warning("startup recovery: real-report-merge refresh failed: %s", exc)

        unfinished_after = store.get_unfinished_orders()
        for order in unfinished_after:
            order["status"] = "NEED_MANUAL_REVIEW"
            store.save_orders([order])

        logger.info(
            "startup recovery: finished, %s unfinished before, %s unresolved after",
            len(unfinished_before),
            len(unfinished_after),
        )
        return {
            "status": "ok",
            "unfinished_before": len(unfinished_before),
            "unfinished_after": len(unfinished_after),
        }
    except Exception as exc:  # noqa: BLE001 - startup must not crash
        logger.warning("startup recovery failed: %s", exc)
        return {"status": "error", "error": str(exc)}


__all__ = ["run_startup_recovery"]
