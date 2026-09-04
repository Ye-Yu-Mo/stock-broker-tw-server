"""M4 broker service: domestic stock order/cancel/replace orchestration.

The service is responsible for:
- normalizing API requests into :class:`StockOrderRequest`
- running risk checks before anything enters the serial queue
- persisting idempotent state under ``client_order_id``
- mapping orders to the Yuanta ``SendStockOrder`` parameters
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import math
import threading
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.config import Settings
from stock_broker_tw.engine.queue import SerialOrderQueue
from stock_broker_tw.engine.state import (
    InvalidOrderStateTransition,
    OrderAction,
    OrderSide,
    OrderStateMachine,
    OrderStatus,
    PriceFlag,
    StockOrderRequest,
    StockOrderState,
    TimeInForce,
)
from stock_broker_tw.metrics import metrics
from stock_broker_tw.risk.circuit_breaker import CircuitBreaker
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.risk.rules import RiskEngine, RiskError
from stock_broker_tw.state.store import MockAccountError, StateStore

logger = logging.getLogger(__name__)


class BrokerServiceError(Exception):
    """Raised when an order operation cannot be completed."""

    def __init__(
        self,
        message: str,
        code: str = "BROKER_ERROR",
        status_code: int = 400,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}


# Yuanta ``SendStockOrder.TradeKind`` field values.  Source:
# docs/api.md section 5.1 (國內證券下單 / 改量 / 取消 / 改價):
#   00 = 委託單, 03 = 改量, 04 = 取消, 07 = 改價
_TRADE_KIND_NEW = 0
_TRADE_KIND_REPLACE_QTY = 3
_TRADE_KIND_CANCEL = 4
_TRADE_KIND_REPLACE_PRICE = 7


class BrokerService:
    """Order entry facade used by HTTP/WebSocket layers."""

    def __init__(
        self,
        adapter: Any,
        settings: Settings,
        store: StateStore | None = None,
        audit: AuditLogger | None = None,
        queue: SerialOrderQueue | None = None,
        risk: RiskEngine | None = None,
        broadcaster: Any = None,
        rate_limiter: RateLimiter | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        notifier: Any = None,
        query_service: Any = None,
    ) -> None:
        self.adapter = adapter
        self.settings = settings
        self.store = store or StateStore(settings.state.db_path)
        self.audit = audit or AuditLogger(enabled=settings.audit.enabled, file_path=settings.audit.file)
        self.queue = queue or SerialOrderQueue()
        self.risk = risk or RiskEngine(settings, notifier=notifier)
        self.broadcaster = broadcaster
        self.notifier = notifier
        self.query_service = query_service
        self.rate_limiter = rate_limiter or RateLimiter(
            max_per_second=settings.rate_limit.trade_per_second,
            max_per_minute=settings.rate_limit.trade_per_minute,
        )
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            failure_threshold=getattr(getattr(settings, "risk", None), "circuit_failure_threshold", 5),
            cooldown_seconds=getattr(getattr(settings, "risk", None), "circuit_cooldown_seconds", 30.0),
            notifier=notifier,
        )
        self._state_machine = OrderStateMachine()
        self._risk_alert_lock = threading.Lock()
        self._risk_alerts: dict[tuple[str, str], float] = {}
        self._risk_alert_window = max(
            0.0,
            float(getattr(settings.notify, "risk_rejection_dedupe_seconds", 60.0)),
        )

    # -- public API ---------------------------------------------------------

    def init_mock_account(
        self,
        account: str,
        cash: float,
        positions: Any = None,
    ) -> dict[str, Any]:
        try:
            return self.store.init_mock_account(account, cash, positions)
        except MockAccountError as exc:
            raise BrokerServiceError(
                exc.message,
                code=exc.code,
                status_code=400,
            ) from exc

    def get_mock_account(self, account: str) -> dict[str, Any] | None:
        return self.store.get_mock_account(account)

    async def place_stock_order(
        self,
        request: StockOrderRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        mock = bool(request.get("mock", False)) if isinstance(request, dict) else False
        raw_account = request.get("account") if isinstance(request, dict) else None
        if mock and not raw_account:
            raise BrokerServiceError(
                "mock orders require an initialized mock account",
                code="MOCK_ACCOUNT_REQUIRED",
                status_code=400,
            )
        req = StockOrderRequest.from_dict(request)
        self._ensure_account(req)
        if mock:
            if self.store.get_mock_account(req.account) is None:
                raise BrokerServiceError(
                    f"mock account not found: {req.account}",
                    code="MOCK_ACCOUNT_NOT_FOUND",
                    status_code=404,
                )
        elif self.store.get_mock_account(req.account) is not None:
            raise BrokerServiceError(
                "mock account requires mock=true",
                code="MOCK_ACCOUNT_REQUIRES_MOCK",
                status_code=400,
            )
        request_id = request_id or str(uuid.uuid4())
        existing = self.store.get_stock_order(req.client_order_id)
        if existing is not None and existing.get("action") == req.action.value:
            return existing
        if existing is not None:
            raise BrokerServiceError(
                "client_order_id already used for a different action",
                code="IDEMPOTENCY_CONFLICT",
                status_code=409,
            )

        self._check_risk(req, "place", request_id)
        self._check_write_circuit(req.client_order_id)
        self._check_trade_rate(req, "place", request_id)
        self.audit.record(
            "order.place",
            result="attempt",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
        )
        self._save_pending(req)
        try:
            await self.queue.submit(req.account, lambda: self._execute_new(req, request_id, mock=mock))
        except RiskError:
            raise
        except Exception as exc:
            if isinstance(exc, BrokerServiceError):
                self.audit.record(
                    "order.place",
                    result="error",
                    request_id=request_id,
                    account=req.account,
                    client_order_id=req.client_order_id,
                    error=str(exc),
                )
                raise
            self._mark_failed(req.client_order_id, exc)
            self.audit.record(
                "order.place",
                result="error",
                request_id=request_id,
                account=req.account,
                client_order_id=req.client_order_id,
                error=str(exc),
            )
            raise BrokerServiceError(
                str(exc),
                code="ORDER_SUBMIT_FAILED",
                status_code=502,
            ) from exc
        self.audit.record(
            "order.place",
            result="success",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
        )
        return self.store.get_stock_order(req.client_order_id) or {}

    async def cancel_stock_order(
        self,
        request: StockOrderRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        req = StockOrderRequest.from_dict(request)
        self._ensure_account(req)
        request_id = request_id or str(uuid.uuid4())
        req.action = OrderAction.CANCEL
        existing = self.store.get_stock_order(req.client_order_id)
        if existing is not None and existing.get("action") == OrderAction.CANCEL.value:
            return existing
        if existing is not None:
            raise BrokerServiceError(
                "client_order_id already used for a different action",
                code="IDEMPOTENCY_CONFLICT",
                status_code=409,
            )
        self._resolve_order_no(req)
        self._check_risk(req, "cancel", request_id)
        self._check_write_circuit(req.client_order_id)
        self._check_trade_rate(req, "cancel", request_id)
        self.audit.record(
            "order.cancel",
            result="attempt",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
            order_no=req.order_no,
        )
        self._save_pending(req)
        try:
            await self.queue.submit(req.account, lambda: self._execute_cancel(req, request_id))
        except Exception as exc:
            if isinstance(exc, BrokerServiceError):
                self.audit.record(
                    "order.cancel",
                    result="error",
                    request_id=request_id,
                    account=req.account,
                    client_order_id=req.client_order_id,
                    error=str(exc),
                )
                raise
            self._mark_failed(req.client_order_id, exc)
            self.audit.record(
                "order.cancel",
                result="error",
                request_id=request_id,
                account=req.account,
                client_order_id=req.client_order_id,
                error=str(exc),
            )
            raise BrokerServiceError(
                str(exc),
                code="ORDER_CANCEL_FAILED",
                status_code=502,
            ) from exc
        self.audit.record(
            "order.cancel",
            result="success",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
            order_no=req.order_no,
        )
        return self.store.get_stock_order(req.client_order_id) or {}

    async def replace_stock_order(
        self,
        request: StockOrderRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        self._reject_simultaneous_replace(request)
        req = StockOrderRequest.from_dict(request)
        self._ensure_account(req)
        request_id = request_id or str(uuid.uuid4())
        req.action = OrderAction.REPLACE
        existing = self.store.get_stock_order(req.client_order_id)
        if existing is not None and existing.get("action") == OrderAction.REPLACE.value:
            return existing
        if existing is not None:
            raise BrokerServiceError(
                "client_order_id already used for a different action",
                code="IDEMPOTENCY_CONFLICT",
                status_code=409,
            )
        self._resolve_order_no(req)
        self._check_risk(req, "replace", request_id)
        self._check_write_circuit(req.client_order_id)
        self._check_trade_rate(req, "replace", request_id)
        self.audit.record(
            "order.replace",
            result="attempt",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
            order_no=req.order_no,
        )
        self._save_pending(req)
        try:
            await self.queue.submit(req.account, lambda: self._execute_replace(req, request_id))
        except Exception as exc:
            if isinstance(exc, BrokerServiceError):
                self.audit.record(
                    "order.replace",
                    result="error",
                    request_id=request_id,
                    account=req.account,
                    client_order_id=req.client_order_id,
                    error=str(exc),
                )
                raise
            self._mark_failed(req.client_order_id, exc)
            self.audit.record(
                "order.replace",
                result="error",
                request_id=request_id,
                account=req.account,
                client_order_id=req.client_order_id,
                error=str(exc),
            )
            raise BrokerServiceError(
                str(exc),
                code="ORDER_REPLACE_FAILED",
                status_code=502,
            ) from exc
        self.audit.record(
            "order.replace",
            result="success",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
            order_no=req.order_no,
        )
        return self.store.get_stock_order(req.client_order_id) or {}

    async def submit_stock_order(
        self,
        request: StockOrderRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        self._reject_simultaneous_replace(request)
        req = StockOrderRequest.from_dict(request)
        action = req.action.value if isinstance(req.action, OrderAction) else str(req.action)
        if action == OrderAction.CANCEL.value:
            return await self.cancel_stock_order(req, request_id=request_id)
        if action == OrderAction.REPLACE.value:
            return await self.replace_stock_order(req, request_id=request_id)
        return await self.place_stock_order(request, request_id=request_id)

    async def place_order(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Alias for :meth:`place_stock_order`."""
        return await self.place_stock_order(*args, **kwargs)

    async def cancel_order(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Alias for :meth:`cancel_stock_order`."""
        return await self.cancel_stock_order(*args, **kwargs)

    async def replace_order(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Alias for :meth:`replace_stock_order`."""
        return await self.replace_stock_order(*args, **kwargs)

    def get_order(self, client_order_id: str) -> dict[str, Any] | None:
        return self.store.get_stock_order(client_order_id)

    def list_orders(
        self,
        account: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.store.list_stock_orders(account=account, status=status)

    # -- internals ----------------------------------------------------------

    def _ensure_account(self, req: StockOrderRequest) -> None:
        if not req.account:
            req.account = self.settings.account.account

    @staticmethod
    def _reject_simultaneous_replace(request: Any) -> None:
        if not isinstance(request, dict):
            return
        action = str(request.get("action") or "new").lower()
        if action == "replace" and request.get("new_price") is not None and request.get("new_quantity") is not None:
            raise BrokerServiceError(
                "simultaneously changing price and quantity is not supported; submit two replace operations",
                code="REPLACE_BOTH_FIELDS_UNSUPPORTED",
                status_code=400,
                detail={"new_price": request.get("new_price"), "new_quantity": request.get("new_quantity")},
            )

    def _check_risk(
        self,
        req: StockOrderRequest,
        action: str,
        request_id: str | None,
    ) -> None:
        try:
            self.risk.check(req)
        except RiskError as exc:
            self.audit.record(
                f"order.{action}",
                result="risk_rejected",
                request_id=request_id,
                account=req.account,
                client_order_id=req.client_order_id,
                error=exc.message,
                code=exc.code,
            )
            self._notify_risk_rejection(req, action, exc.code, exc.message)
            raise

    def _check_write_circuit(self, client_order_id: str) -> None:
        if not self.circuit_breaker.allow_request():
            self.audit.record(
                "order.circuit_open",
                result="error",
                account=None,
                client_order_id=client_order_id,
                error=self.circuit_breaker.last_error,
            )
            raise BrokerServiceError(
                "trading circuit is open; write requests are temporarily blocked",
                code="CIRCUIT_OPEN",
                status_code=503,
                detail={"circuit": self.circuit_breaker.to_dict()},
            )

    def _check_trade_rate(
        self,
        req: StockOrderRequest,
        action: str,
        request_id: str | None,
    ) -> None:
        if not self.rate_limiter.acquire("SendStockOrder", key=req.account):
            metrics.rate_limited_total.labels(function="SendStockOrder").inc()
            self.audit.record(
                "order.rate_limited",
                result="error",
                request_id=request_id,
                account=req.account,
                client_order_id=req.client_order_id,
                function="SendStockOrder",
                order_action=action,
            )
            self._notify_risk_rejection(
                req,
                action,
                "RATE_LIMITED",
                "RATE_LIMITED: trade rate limit exceeded",
            )
            raise BrokerServiceError(
                "trade rate limit exceeded",
                code="RATE_LIMITED",
                status_code=429,
                detail={"function": "SendStockOrder", "action": action},
            )

    def _notify(self, event: str, title: str, fields: dict[str, Any]) -> None:
        if self.notifier is None:
            return
        try:
            method = getattr(self.notifier, "send", None)
            if callable(method):
                method(event, title, fields)
        except Exception:
            pass

    def _notify_risk_rejection(
        self,
        req: StockOrderRequest,
        action: str,
        code: str,
        reason: str,
    ) -> None:
        """Send one deduplicated alert without affecting the rejection path."""
        if self.notifier is None:
            return
        key = (req.client_order_id, f"{code}:{reason}")
        now = time.monotonic()
        with self._risk_alert_lock:
            previous = self._risk_alerts.get(key)
            if (
                self._risk_alert_window > 0
                and previous is not None
                and now - previous < self._risk_alert_window
            ):
                metrics.notifications_suppressed_total.labels(event="risk.rejected").inc()
                return
            self._risk_alerts[key] = now
            if len(self._risk_alerts) > 4096:
                cutoff = now - self._risk_alert_window
                self._risk_alerts = {
                    alert_key: sent_at
                    for alert_key, sent_at in self._risk_alerts.items()
                    if sent_at >= cutoff
                }

        fields = {
            "client_order_id": req.client_order_id,
            "account": req.account,
            "stk_code": req.stk_code,
            "side": self._side_value(req.side),
            "price": req.price,
            "quantity": req.quantity,
            "action": action,
            "code": code,
            "reason": reason,
        }
        try:
            self.notifier.send("risk.rejected", "风控拒绝", fields)
        except Exception as exc:
            # Notifier implementations are expected to be best-effort, but a
            # custom notifier must not be able to turn a rejection into success.
            logger.warning("risk rejection notification failed: %s", exc)

    def _save_pending(self, req: StockOrderRequest) -> None:
        req.trade_date = self._date_to_str(req.trade_date)
        self.store.save_stock_order(
            client_order_id=req.client_order_id,
            request=req.to_dict(),
            status=OrderStatus.PENDING.value,
            account=req.account,
            action=req.action.value if isinstance(req.action, OrderAction) else str(req.action),
            order_no=req.order_no,
            trade_date=req.trade_date,
            data={"request": req.to_dict()},
        )

    async def _update_status(
        self,
        client_order_id: str,
        status: str,
        order_no: str | None = None,
        trade_date: str | None = None,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        reason: str | None = None,
    ) -> None:
        row = self.store.get_stock_order(client_order_id)
        if row is None:
            return
        state = StockOrderState.from_dict(
            {
                **row,
                "request": row.get("request"),
            }
        )
        try:
            self._state_machine.transition(state, OrderStatus(status), reason=reason)
            final_status = state.status.value
        except Exception:
            # Keep store consistent even when a report/response arrives out of
            # order; mark it for manual review instead of dropping the update.
            final_status = OrderStatus.NEED_MANUAL_REVIEW.value
        persisted_data = dict(data or {})
        persisted_data["transitions"] = state.transitions
        if state.need_manual_review:
            persisted_data["need_manual_review"] = True
        if error:
            persisted_data["last_error"] = error
        try:
            self.store.update_stock_order(
                client_order_id,
                status=final_status,
                order_no=order_no,
                trade_date=trade_date,
                data=persisted_data,
                request=row.get("request"),
                account=row.get("account"),
                action=row.get("action"),
            )
        except InvalidOrderStateTransition:
            # A late update must not roll back a final order; keep the stored
            # status and surface the rejection in the order data.
            final_status = row["status"]
            persisted_data["last_error"] = "ignored illegal status update"
            self.store.update_stock_order(
                client_order_id,
                status=final_status,
                order_no=order_no,
                trade_date=trade_date,
                data=persisted_data,
                request=row.get("request"),
                account=row.get("account"),
                action=row.get("action"),
            )
        update_payload = {
            "client_order_id": client_order_id,
            "status": final_status,
            "order_no": order_no,
            "trade_date": trade_date,
            "request": row.get("request"),
            "data": data or {},
            "last_error": error,
        }
        self._notify(
            "order.status",
            "订单状态变化",
            {
                "client_order_id": client_order_id,
                "status": final_status,
                "order_no": order_no,
                "trade_date": trade_date,
                "error": error,
            },
        )
        if self.broadcaster is not None and hasattr(self.broadcaster, "broadcast_order_update"):
            broadcast = self.broadcaster.broadcast_order_update(update_payload)
            if inspect.isawaitable(broadcast):
                await broadcast

    def _mark_failed(self, client_order_id: str, exc: Exception) -> None:
        self.store.update_stock_order(
            client_order_id,
            status=OrderStatus.FAILED.value,
            data={"error": str(exc)},
        )

    def _resolve_order_no(self, req: StockOrderRequest) -> None:
        if req.order_no:
            req.order_no = str(req.order_no)
            local = self.store.get_stock_order_by_order_no(req.order_no)
            legacy = self.store.get_orders(order_no=req.order_no)
            if local is None and not legacy:
                raise BrokerServiceError(
                    "order_no is not found in local order mapping",
                    code="ORDER_NOT_FOUND",
                    status_code=404,
                )
            return
        row = self.store.get_stock_order(req.client_order_id)
        if row and row.get("order_no"):
            req.order_no = row["order_no"]
            req.trade_date = req.trade_date or row.get("trade_date")
            return
        if req.client_order_id:
            by_cid = self.store.get_stock_order(req.client_order_id)
            if by_cid and by_cid.get("order_no"):
                req.order_no = by_cid["order_no"]
                req.trade_date = req.trade_date or by_cid.get("trade_date")
                return
        raise BrokerServiceError(
            "order_no is required and no local mapping was found",
            code="ORDER_NOT_FOUND",
            status_code=404,
        )

    async def _execute_new(
        self,
        req: StockOrderRequest,
        request_id: str | None = None,
        mock: bool = False,
    ) -> None:
        if mock:
            await self._execute_mock(req, request_id=request_id)
            return
        await self._update_status(req.client_order_id, OrderStatus.SUBMITTED.value, reason="sending to broker")
        response = await self._call_send(req, request_id=request_id)
        result = self._first_result(response)
        if result is None:
            error = self._response_error(response)
            if error:
                await self._update_status(
                    req.client_order_id,
                    OrderStatus.REJECTED.value,
                    data={"response": response},
                    error=error,
                    reason="broker returned failure response",
                )
                raise BrokerServiceError(
                    error,
                    code="ORDER_REJECTED",
                    status_code=502,
                    detail={"response": response},
                )
            await self._update_status(
                req.client_order_id,
                OrderStatus.NEED_MANUAL_REVIEW.value,
                data={"response": response},
                reason="no order result returned",
            )
            return
        reply_code = self._result_field(result, "reply_code", "ReplyCode")
        if reply_code not in (0, "0", None):
            error = (
                self._result_field(result, "advisory", "Advisory")
                or self._result_field(result, "err_no", "ErrNO")
                or f"broker reply_code={reply_code}"
            )
            await self._update_status(
                req.client_order_id,
                OrderStatus.REJECTED.value,
                data={"response": response, "result": result},
                error=str(error),
                reason="broker rejected order",
            )
            raise BrokerServiceError(
                str(error),
                code="ORDER_REJECTED",
                status_code=502,
                detail={"result": result},
            )
        order_no = self._result_field(result, "order_no", "orderNO", "OrderNO")
        if order_no is not None:
            order_no = str(order_no)
        trade_date = self._date_to_str(self._result_field(result, "trade_date", "TradeDate"))
        if not order_no:
            await self._update_status(
                req.client_order_id,
                OrderStatus.NEED_MANUAL_REVIEW.value,
                data={"response": response, "result": result},
                reason="accepted but no order_no in response",
            )
            return
        await self._update_status(
            req.client_order_id,
            OrderStatus.ACCEPTED.value,
            order_no=order_no,
            trade_date=trade_date,
            data={"response": response, "result": result},
            reason="broker accepted order",
        )
        self._save_m3_order(req, order_no, trade_date)

    async def _execute_mock(
        self,
        req: StockOrderRequest,
        request_id: str | None = None,
    ) -> None:
        """Fill a new order locally using the current opposing quote."""
        try:
            if self.query_service is None:
                raise BrokerServiceError(
                    "mock quote service is unavailable",
                    code="MOCK_QUOTE_UNAVAILABLE",
                    status_code=503,
                )
            snapshot = await self.query_service.watchlist_snapshot(
                stk_code=req.stk_code,
                market_type="TWSE",
                # Market data is read through the configured real session; the
                # mock account must never be sent to Spark API as a real account.
                account=self.settings.account.account,
                request_id=request_id,
            )
            bid1, ask1 = self._mock_quote_prices(snapshot, req.stk_code)
            fill_price = ask1 if self._side_value(req.side) == "B" else bid1
            now = datetime.now(UTC)
            order_no = f"MOCK-{uuid.uuid4()}"
            trade_date = now.strftime("%Y/%m/%d")
            mock_data = {
                "mock": True,
                "execution": "simulated",
                "bid1": bid1,
                "ask1": ask1,
                "fill_price": fill_price,
                "filled_qty": req.quantity,
                "avg_price": fill_price,
                "timestamp": now.isoformat(),
            }
            self.store.apply_mock_fill(
                account=req.account,
                side=self._side_value(req.side),
                stk_code=req.stk_code,
                quantity=req.quantity,
                price=fill_price,
            )
        except MockAccountError as exc:
            await self._update_status(
                req.client_order_id,
                OrderStatus.REJECTED.value,
                data={"mock": True},
                error=exc.message,
                reason="mock account rejected fill",
            )
            self._notify_risk_rejection(req, "place", exc.code, exc.message)
            raise BrokerServiceError(
                exc.message,
                code=exc.code,
                status_code=409,
            ) from exc
        except BrokerServiceError as exc:
            await self._update_status(
                req.client_order_id,
                OrderStatus.REJECTED.value,
                data={"mock": True},
                error=exc.message,
                reason="mock quote unavailable",
            )
            raise
        except Exception as exc:
            await self._update_status(
                req.client_order_id,
                OrderStatus.REJECTED.value,
                data={"mock": True},
                error=str(exc),
                reason="mock quote unavailable",
            )
            raise BrokerServiceError(
                str(exc),
                code="MOCK_QUOTE_UNAVAILABLE",
                status_code=502,
            ) from exc

        await self._update_status(
            req.client_order_id,
            OrderStatus.ACCEPTED.value,
            order_no=order_no,
            trade_date=trade_date,
            data=mock_data,
            reason="mock order accepted",
        )
        await self._update_status(
            req.client_order_id,
            OrderStatus.FILLED.value,
            order_no=order_no,
            trade_date=trade_date,
            data=mock_data,
            reason="mock order filled",
        )
        self._save_m3_order(req, order_no, trade_date)

    @staticmethod
    def _mock_quote_prices(snapshot: Any, stk_code: str) -> tuple[float, float]:
        rows: Any = snapshot
        if isinstance(snapshot, dict):
            for key in ("query_watch_list", "watchlist", "quote_list", "items"):
                if isinstance(snapshot.get(key), list):
                    rows = snapshot[key]
                    break
            else:
                nested = snapshot.get("data")
                if isinstance(nested, (dict, list)):
                    return BrokerService._mock_quote_prices(nested, stk_code)
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            raise BrokerServiceError(
                "mock quote response has no quote rows",
                code="MOCK_QUOTE_UNAVAILABLE",
                status_code=502,
            )

        row = next(
            (
                item
                for item in rows
                if isinstance(item, dict)
                and str(
                    item.get("stk_code", item.get("stock_code", item.get("symbol", "")))
                )
                == str(stk_code)
            ),
            None,
        )
        if row is None:
            raise BrokerServiceError(
                f"mock quote not found for {stk_code}",
                code="MOCK_QUOTE_UNAVAILABLE",
                status_code=502,
            )

        bid1 = BrokerService._mock_quote_field(
            row,
            "bid1",
            "buy_price1",
            "buy_price",
            "BidPrice1",
            "BuyPrice1",
            "BuyPrice",
        )
        ask1 = BrokerService._mock_quote_field(
            row,
            "ask1",
            "sell_price1",
            "sell_price",
            "AskPrice1",
            "SellPrice1",
            "SellPrice",
        )
        try:
            bid1 = float(bid1)
            ask1 = float(ask1)
        except (TypeError, ValueError) as exc:
            raise BrokerServiceError(
                f"mock quote has invalid prices for {stk_code}",
                code="MOCK_QUOTE_UNAVAILABLE",
                status_code=502,
            ) from exc
        if not math.isfinite(bid1) or not math.isfinite(ask1) or bid1 <= 0 or ask1 <= 0:
            raise BrokerServiceError(
                f"mock quote has unavailable prices for {stk_code}",
                code="MOCK_QUOTE_UNAVAILABLE",
                status_code=502,
            )
        return bid1, ask1

    @staticmethod
    def _mock_quote_field(row: dict[str, Any], *keys: str) -> Any:
        containers = [row]
        for key in ("index_flag_50", "IndexFlag_50", "five_tick", "five_tick_a"):
            nested = row.get(key)
            if isinstance(nested, dict):
                containers.append(nested)
        for container in containers:
            for key in keys:
                if container.get(key) is not None:
                    return container[key]
        return None

    async def _execute_cancel(self, req: StockOrderRequest, request_id: str | None = None) -> None:
        await self._update_status(req.client_order_id, OrderStatus.SUBMITTED.value, reason="sending cancel")
        response = await self._call_send(req, request_id=request_id)
        result = self._first_result(response)
        if result is None:
            error = self._response_error(response)
            if error:
                await self._update_status(
                    req.client_order_id,
                    OrderStatus.REJECTED.value,
                    data={"response": response},
                    error=error,
                    reason="broker returned cancel failure",
                )
                raise BrokerServiceError(
                    error,
                    code="CANCEL_REJECTED",
                    status_code=502,
                    detail={"response": response},
                )
            await self._update_status(
                req.client_order_id,
                OrderStatus.NEED_MANUAL_REVIEW.value,
                data={"response": response},
                reason="no cancel result returned",
            )
            return
        reply_code = self._result_field(result, "reply_code", "ReplyCode")
        if reply_code not in (0, "0", None):
            error = (
                self._result_field(result, "advisory", "Advisory")
                or self._result_field(result, "err_no", "ErrNO")
                or f"broker reply_code={reply_code}"
            )
            await self._update_status(
                req.client_order_id,
                OrderStatus.REJECTED.value,
                data={"response": response, "result": result},
                error=str(error),
                reason="broker rejected cancel",
            )
            raise BrokerServiceError(str(error), code="CANCEL_REJECTED", status_code=502)
        await self._update_status(
            req.client_order_id,
            OrderStatus.ACCEPTED.value,
            order_no=req.order_no,
            trade_date=req.trade_date,
            data={"response": response, "result": result},
            reason="broker accepted cancel request",
        )

    async def _execute_replace(self, req: StockOrderRequest, request_id: str | None = None) -> None:
        await self._update_status(req.client_order_id, OrderStatus.SUBMITTED.value, reason="sending replace")
        response = await self._call_send(req, request_id=request_id)
        result = self._first_result(response)
        if result is None:
            error = self._response_error(response)
            if error:
                await self._update_status(
                    req.client_order_id,
                    OrderStatus.REJECTED.value,
                    data={"response": response},
                    error=error,
                    reason="broker returned replace failure",
                )
                raise BrokerServiceError(
                    error,
                    code="REPLACE_REJECTED",
                    status_code=502,
                    detail={"response": response},
                )
            await self._update_status(
                req.client_order_id,
                OrderStatus.NEED_MANUAL_REVIEW.value,
                data={"response": response},
                reason="no replace result returned",
            )
            return
        reply_code = self._result_field(result, "reply_code", "ReplyCode")
        if reply_code not in (0, "0", None):
            error = (
                self._result_field(result, "advisory", "Advisory")
                or self._result_field(result, "err_no", "ErrNO")
                or f"broker reply_code={reply_code}"
            )
            await self._update_status(
                req.client_order_id,
                OrderStatus.REJECTED.value,
                data={"response": response, "result": result},
                error=str(error),
                reason="broker rejected replace",
            )
            raise BrokerServiceError(str(error), code="REPLACE_REJECTED", status_code=502)
        await self._update_status(
            req.client_order_id,
            OrderStatus.ACCEPTED.value,
            order_no=req.order_no,
            trade_date=req.trade_date,
            data={"response": response, "result": result},
            reason="broker accepted replace request",
        )

    async def _call_send(self, req: StockOrderRequest, request_id: str | None = None) -> Any:
        order = self._build_order(req, request_id=request_id)
        timeout = getattr(getattr(self.settings, "risk", None), "order_timeout", 10.0)
        try:
            send = getattr(self.adapter, "send_stock_order", None)
            if callable(send):
                if asyncio.iscoroutinefunction(send):
                    try:
                        if request_id is not None:
                            result = await send(
                                req.account, order, timeout=timeout, request_id=request_id
                            )
                        else:
                            result = await send(req.account, order, timeout=timeout)
                    except TypeError:
                        result = await send(req.account, order, timeout=timeout)
                else:
                    try:
                        if request_id is not None:
                            result = await asyncio.to_thread(
                                send,
                                req.account,
                                order,
                                timeout=timeout,
                                request_id=request_id,
                            )
                        else:
                            result = await asyncio.to_thread(
                                send, req.account, order, timeout=timeout
                            )
                    except TypeError:
                        result = await asyncio.to_thread(send, req.account, order, timeout=timeout)
                if inspect.isawaitable(result):
                    result = await result
            else:
                query = getattr(self.adapter, "query", None)
                if callable(query):
                    if asyncio.iscoroutinefunction(query):
                        try:
                            if request_id is not None:
                                result = await query(
                                    "SendStockOrder",
                                    req.account,
                                    [order],
                                    timeout=timeout,
                                    request_id=request_id,
                                )
                            else:
                                result = await query(
                                    "SendStockOrder", req.account, [order], timeout=timeout
                                )
                        except TypeError:
                            result = await query(
                                "SendStockOrder", req.account, [order], timeout=timeout
                            )
                    else:
                        try:
                            if request_id is not None:
                                result = await asyncio.to_thread(
                                    query,
                                    "SendStockOrder",
                                    req.account,
                                    [order],
                                    timeout=timeout,
                                    request_id=request_id,
                                )
                            else:
                                result = await asyncio.to_thread(
                                    query,
                                    "SendStockOrder",
                                    req.account,
                                    [order],
                                    timeout=timeout,
                                )
                        except TypeError:
                            result = await asyncio.to_thread(
                                query, "SendStockOrder", req.account, [order], timeout=timeout
                            )
                    if inspect.isawaitable(result):
                        result = await result
                else:
                    raise BrokerServiceError(
                        "adapter does not support SendStockOrder",
                        code="ADAPTER_UNSUPPORTED",
                        status_code=501,
                    )
        except Exception as exc:
            self.circuit_breaker.record_failure(exc)
            self._notify(
                "order.broker_error",
                "委托发送异常",
                {
                    "client_order_id": req.client_order_id,
                    "action": req.action.value if isinstance(req.action, OrderAction) else str(req.action),
                    "error": str(exc),
                },
            )
            raise
        self.circuit_breaker.record_success()
        return result

    def _build_order(
        self,
        req: StockOrderRequest,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            # Use the caller's request_id as the Yuanta Identify correlation id
            # when available and no explicit custom Identify was supplied; it is
            # echoed in SendStockOrder responses.
            "identify": (
                request_id
                if request_id is not None and req.identify == 1
                else req.identify
            ),
            "account": req.account or self.settings.account.account,
            "order_no": req.order_no or "",
            "trade_date": self._date_to_str(req.trade_date) or "",
            "ap_code": req.ap_code,
            "trade_kind": self._trade_kind(req),
            "order_type": req.order_type,
            "stk_code": req.stk_code,
            "buy_sell": self._side_value(req.side),
            "price_flag": self._price_flag_value(req.price_flag),
            "price": req.price or 0.0,
            "basket_no": req.client_order_id,
            "order_qty": req.quantity or 0,
            "time_in_force": self._tif_value(req.time_in_force),
        }

    @staticmethod
    def _trade_kind(req: StockOrderRequest) -> int:
        action = req.action.value if isinstance(req.action, OrderAction) else str(req.action)
        if action == OrderAction.CANCEL.value:
            return _TRADE_KIND_CANCEL
        if action == OrderAction.REPLACE.value:
            # 03 = 改量, 07 = 改價.  If both fields are present, treat it as a
            # price change (07) because price is the more specific one.
            # Source: docs/api.md section 5.1 / docs/API/元大API說明文件 43.md.
            return _TRADE_KIND_REPLACE_PRICE if req.price is not None else _TRADE_KIND_REPLACE_QTY
        return _TRADE_KIND_NEW

    @staticmethod
    def _side_value(side: Any) -> str:
        if isinstance(side, OrderSide):
            return side.value
        return str(side)

    @staticmethod
    def _price_flag_value(flag: Any) -> str:
        if isinstance(flag, PriceFlag):
            flag = flag.value
        return {
            "LIMIT": "",
            "M": "M",
            "H": "H",
            "L": "L",
            "-": "-",
        }.get(str(flag), str(flag))

    @staticmethod
    def _tif_value(tif: Any) -> str:
        if isinstance(tif, TimeInForce):
            tif = tif.value
        return {
            "ROD": "0",
            "IOC": "3",
            "FOK": "4",
        }.get(str(tif), str(tif))

    @staticmethod
    def _date_to_str(value: Any) -> Any:
        if isinstance(value, dict):
            year = value.get("year") if value.get("year") is not None else value.get("Year")
            month = value.get("month") if value.get("month") is not None else value.get("Month")
            day = value.get("day") if value.get("day") is not None else value.get("Day")
            if year is not None and month is not None and day is not None:
                return f"{int(year):04d}/{int(month):02d}/{int(day):02d}"
            return str(value)
        return value

    @staticmethod
    def _result_field(result: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in result:
                return result[key]
        return None

    @staticmethod
    def _response_error(response: Any) -> str | None:
        if not isinstance(response, dict):
            return None
        for key in ("result_count", "ResultCount"):
            count = response.get(key)
            if isinstance(count, dict):
                msg_code = count.get("msg_code", count.get("MsgCode"))
                if msg_code is not None and str(msg_code) not in {"0", "0000", "0001", "00001"}:
                    return str(count.get("msg_content", count.get("MsgContent", msg_code)))
        return None

    @staticmethod
    def _m3_status(status: str) -> str:
        """Map M4 statuses to the numeric codes used by the M3 orders table."""
        return {
            "PENDING": "0",
            "SUBMITTED": "0",
            "ACCEPTED": "20",
            "PARTIALLY_FILLED": "20",
            "FILLED": "20",
            "CANCELLED": "30",
            "REJECTED": "10",
            "FAILED": "24",
            "NEED_MANUAL_REVIEW": "0",
        }.get(status, status)

    @staticmethod
    def _first_result(response: Any) -> dict[str, Any] | None:
        if isinstance(response, dict):
            for key in ("result_list", "results", "ResultList", "Results"):
                value = response.get(key)
                if isinstance(value, list) and value:
                    first = value[0]
                    return first if isinstance(first, dict) else None
            if any(key in response for key in ("order_no", "reply_code", "orderNO", "ReplyCode")):
                return response
            nested = response.get("data")
            if isinstance(nested, dict):
                return BrokerService._first_result(nested)
        elif isinstance(response, list) and response:
            return response[0] if isinstance(response[0], dict) else None
        return None

    def _save_m3_order(self, req: StockOrderRequest, order_no: str, trade_date: str | None) -> None:
        self.store.save_orders(
            [
                {
                    "order_no": order_no,
                    "account": req.account,
                    "trade_date": trade_date or req.trade_date or "",
                    "company_no": req.stk_code,
                    "status": "20",
                    "client_order_id": req.client_order_id,
                    "basket_no": req.client_order_id,
                    "bs": self._side_value(req.side),
                    "price": req.price,
                    "order_qty": req.quantity,
                }
            ]
        )


__all__ = ["BrokerService", "BrokerServiceError"]
