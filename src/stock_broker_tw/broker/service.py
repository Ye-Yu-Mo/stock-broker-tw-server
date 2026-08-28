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
import uuid
from typing import Any

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.config import Settings
from stock_broker_tw.engine.queue import SerialOrderQueue
from stock_broker_tw.engine.state import (
    OrderAction,
    OrderSide,
    OrderStateMachine,
    OrderStatus,
    PriceFlag,
    StockOrderRequest,
    StockOrderState,
    TimeInForce,
)
from stock_broker_tw.risk.rules import RiskEngine, RiskError
from stock_broker_tw.state.store import StateStore


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
    ) -> None:
        self.adapter = adapter
        self.settings = settings
        self.store = store or StateStore(settings.state.db_path)
        self.audit = audit or AuditLogger(enabled=settings.audit.enabled, file_path=settings.audit.file)
        self.queue = queue or SerialOrderQueue()
        self.risk = risk or RiskEngine(settings)
        self.broadcaster = broadcaster
        self._state_machine = OrderStateMachine()

    # -- public API ---------------------------------------------------------

    async def place_stock_order(
        self,
        request: StockOrderRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        req = StockOrderRequest.from_dict(request)
        self._ensure_account(req)
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
        self.audit.record(
            "order.place",
            result="attempt",
            request_id=request_id,
            account=req.account,
            client_order_id=req.client_order_id,
        )
        self._save_pending(req)
        try:
            await self.queue.submit(req.account, lambda: self._execute_new(req))
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
            await self.queue.submit(req.account, lambda: self._execute_cancel(req))
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
            await self.queue.submit(req.account, lambda: self._execute_replace(req))
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
        req = StockOrderRequest.from_dict(request)
        action = req.action.value if isinstance(req.action, OrderAction) else str(req.action)
        if action == OrderAction.CANCEL.value:
            return await self.cancel_stock_order(req, request_id=request_id)
        if action == OrderAction.REPLACE.value:
            return await self.replace_stock_order(req, request_id=request_id)
        return await self.place_stock_order(req, request_id=request_id)

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
            raise

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
        if self.broadcaster is not None and hasattr(self.broadcaster, "broadcast_order_update"):
            broadcast = self.broadcaster.broadcast_order_update(
                {
                    "client_order_id": client_order_id,
                    "status": final_status,
                    "order_no": order_no,
                    "trade_date": trade_date,
                    "request": row.get("request"),
                    "data": data or {},
                    "last_error": error,
                }
            )
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

    async def _execute_new(self, req: StockOrderRequest) -> None:
        await self._update_status(req.client_order_id, OrderStatus.SUBMITTED.value, reason="sending to broker")
        response = await self._call_send(req)
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

    async def _execute_cancel(self, req: StockOrderRequest) -> None:
        await self._update_status(req.client_order_id, OrderStatus.SUBMITTED.value, reason="sending cancel")
        response = await self._call_send(req)
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

    async def _execute_replace(self, req: StockOrderRequest) -> None:
        await self._update_status(req.client_order_id, OrderStatus.SUBMITTED.value, reason="sending replace")
        response = await self._call_send(req)
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

    async def _call_send(self, req: StockOrderRequest) -> Any:
        order = self._build_order(req)
        timeout = getattr(getattr(self.settings, "risk", None), "order_timeout", 10.0)
        send = getattr(self.adapter, "send_stock_order", None)
        if callable(send):
            if asyncio.iscoroutinefunction(send):
                try:
                    result = await send(req.account, order, timeout=timeout)
                except TypeError:
                    result = await send(req.account, order)
            else:
                try:
                    result = await asyncio.to_thread(
                        send, req.account, order, timeout=timeout
                    )
                except TypeError:
                    result = await asyncio.to_thread(send, req.account, order)
            if inspect.isawaitable(result):
                result = await result
            return result
        query = getattr(self.adapter, "query", None)
        if callable(query):
            if asyncio.iscoroutinefunction(query):
                try:
                    result = await query(
                        "SendStockOrder", req.account, [order], timeout=timeout
                    )
                except TypeError:
                    result = await query("SendStockOrder", req.account, [order])
            else:
                try:
                    result = await asyncio.to_thread(
                        query,
                        "SendStockOrder",
                        req.account,
                        [order],
                        timeout=timeout,
                    )
                except TypeError:
                    result = await asyncio.to_thread(
                        query, "SendStockOrder", req.account, [order]
                    )
            if inspect.isawaitable(result):
                result = await result
            return result
        raise BrokerServiceError(
            "adapter does not support SendStockOrder",
            code="ADAPTER_UNSUPPORTED",
            status_code=501,
        )

    def _build_order(self, req: StockOrderRequest) -> dict[str, Any]:
        return {
            "identify": req.identify,
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
            return 4
        if action == OrderAction.REPLACE.value:
            # TODO-M4: 03 = 改量, 07 = 改價.  If both fields are present, treat
            # it as a price change (07) because price is the more specific one.
            return 7 if req.price is not None else 3
        return 0

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
