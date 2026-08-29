"""M5 quote subscription orchestration service.

``QuoteService`` isolates the HTTP/WebSocket layers from the Yuanta adapter.  It
keeps a local deduplicated subscription list, enforces per-request and total
symbol limits, and rate-limits each Yuanta ``Subscribe*`` / ``UnSubscribe*``
FunctionID.
"""

from __future__ import annotations

import asyncio
from typing import Any

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.broker.quote import QuoteType, SubscribeRequest
from stock_broker_tw.config import Settings, resolve_quote_rate_limits
from stock_broker_tw.metrics import metrics
from stock_broker_tw.risk.circuit_breaker import CircuitBreaker
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.state.store import StateStore


class QuoteServiceError(Exception):
    """Raised when a quote subscription operation cannot be completed."""

    def __init__(
        self,
        message: str,
        code: str = "QUOTE_ERROR",
        status_code: int = 400,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}


class QuoteService:
    """Subscribe/unsubscribe/list quote symbols through the Yuanta adapter."""

    def __init__(
        self,
        adapter: Any,
        settings: Settings,
        store: StateStore | None = None,
        state_store: StateStore | None = None,
        rate_limiter: RateLimiter | None = None,
        audit: AuditLogger | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.adapter = adapter
        self.settings = settings
        self.store = store or state_store or StateStore(settings.state.db_path)
        self.state_store = self.store
        quote_per_second, quote_per_minute = resolve_quote_rate_limits(settings)
        self.rate_limiter = rate_limiter or RateLimiter(
            max_per_second=quote_per_second,
            max_per_minute=quote_per_minute,
        )
        self.audit = audit or AuditLogger(
            enabled=settings.audit.enabled,
            file_path=settings.audit.file,
        )
        self.circuit_breaker = circuit_breaker

    # -- public API ---------------------------------------------------------

    async def subscribe(
        self,
        request: SubscribeRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            req = SubscribeRequest.from_dict(request)
        except ValueError as exc:
            raise QuoteServiceError(
                str(exc),
                code="INVALID_QUOTE_TYPE",
                status_code=400,
            ) from exc
        account = req.account or self.settings.account.account
        if not req.symbols:
            raise QuoteServiceError(
                "symbols must not be empty",
                code="EMPTY_SYMBOLS",
                status_code=400,
            )
        max_per_request = self.settings.quote.max_per_request
        if len(req.symbols) > max_per_request:
            raise QuoteServiceError(
                f"too many symbols in one request: {len(req.symbols)} > {max_per_request}",
                code="MAX_PER_REQUEST_EXCEEDED",
                status_code=400,
                detail={"max_per_request": max_per_request, "count": len(req.symbols)},
            )

        existing = self.store.list_quote_subscriptions(account=account)
        index_flag = self._index_flag(req)
        existing_keys = {
            (row["type"], row["symbol"], row["market_type"], row.get("index_flag")) for row in existing
        }
        new_symbols = list(
            dict.fromkeys(
                symbol
                for symbol in req.symbols
                if (req.type.value, symbol, req.market_type, index_flag) not in existing_keys
            )
        )

        total_after = len(existing) + len(new_symbols)
        max_total = self.settings.quote.max_total_subscriptions
        if total_after > max_total:
            raise QuoteServiceError(
                f"total subscription limit exceeded: {total_after} > {max_total}",
                code="MAX_TOTAL_EXCEEDED",
                status_code=400,
                detail={"max_total": max_total, "total": total_after},
            )

        if not new_symbols:
            return self._serialize_rows(self.store.list_quote_subscriptions(account=account))

        function_name = req.type.subscribe_function
        if not self.rate_limiter.acquire(function_name, key=account):
            metrics.rate_limited_total.labels(function=function_name).inc()
            self.audit.record(
                "quote.rate_limited",
                result="error",
                request_id=request_id,
                account=account,
                function=function_name,
            )
            raise QuoteServiceError(
                "quote subscribe rate limit exceeded",
                code="RATE_LIMITED",
                status_code=429,
                detail={"function": function_name},
            )

        payload = self._build_payload(req, new_symbols)
        try:
            await self._call_adapter("subscribe", function_name, account, payload)
        except Exception as exc:
            self.audit.record(
                "quote.subscribe",
                result="error",
                request_id=request_id,
                account=account,
                function=function_name,
                symbols=new_symbols,
                error=str(exc),
            )
            raise QuoteServiceError(
                f"quote subscribe failed: {exc}",
                code="SUBSCRIBE_FAILED",
                status_code=502,
                detail={"function": function_name},
            ) from exc

        self.store.save_quote_subscriptions(
            account=account,
            quote_type=req.type.value,
            symbols=new_symbols,
            market_type=req.market_type,
            index_flag=index_flag,
        )
        self.audit.record(
            "quote.subscribe",
            result="success",
            request_id=request_id,
            account=account,
            function=function_name,
            symbols=new_symbols,
        )
        return self._serialize_rows(self.store.list_quote_subscriptions(account=account))

    async def unsubscribe(
        self,
        request: SubscribeRequest | dict[str, Any],
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            req = SubscribeRequest.from_dict(request)
        except ValueError as exc:
            raise QuoteServiceError(
                str(exc),
                code="INVALID_QUOTE_TYPE",
                status_code=400,
            ) from exc
        account = req.account or self.settings.account.account

        existing = self.store.list_quote_subscriptions(account=account)
        index_flag = self._index_flag(req)
        existing_keys = {
            (row["type"], row["symbol"], row["market_type"], row.get("index_flag")) for row in existing
        }
        remove_symbols = list(
            dict.fromkeys(
                symbol
                for symbol in req.symbols
                if (req.type.value, symbol, req.market_type, index_flag) in existing_keys
            )
        )
        if not remove_symbols:
            return self._serialize_rows(existing)

        function_name = req.type.unsubscribe_function
        if not self.rate_limiter.acquire(function_name, key=account):
            metrics.rate_limited_total.labels(function=function_name).inc()
            self.audit.record(
                "quote.rate_limited",
                result="error",
                request_id=request_id,
                account=account,
                function=function_name,
            )
            raise QuoteServiceError(
                "quote unsubscribe rate limit exceeded",
                code="RATE_LIMITED",
                status_code=429,
                detail={"function": function_name},
            )

        payload = self._build_payload(req, remove_symbols)
        try:
            await self._call_adapter("unsubscribe", function_name, account, payload)
        except Exception as exc:
            self.audit.record(
                "quote.unsubscribe",
                result="error",
                request_id=request_id,
                account=account,
                function=function_name,
                symbols=remove_symbols,
                error=str(exc),
            )
            raise QuoteServiceError(
                f"quote unsubscribe failed: {exc}",
                code="UNSUBSCRIBE_FAILED",
                status_code=502,
                detail={"function": function_name},
            ) from exc

        self.store.delete_quote_subscriptions(
            account=account,
            quote_type=req.type.value,
            symbols=remove_symbols,
            market_type=req.market_type,
            index_flag=index_flag,
        )
        self.audit.record(
            "quote.unsubscribe",
            result="success",
            request_id=request_id,
            account=account,
            function=function_name,
            symbols=remove_symbols,
        )
        return self._serialize_rows(self.store.list_quote_subscriptions(account=account))

    def list_subscribed(
        self,
        account: str | None = None,
        quote_type: str | None = None,
    ) -> list[dict[str, Any]]:
        acct = account or self.settings.account.account
        return self._serialize_rows(
            self.store.list_quote_subscriptions(account=acct, quote_type=quote_type)
        )

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _index_flag(req: SubscribeRequest) -> int | None:
        if req.type is QuoteType.WATCHLIST:
            return req.index_flag if req.index_flag is not None else 7
        return req.index_flag

    @staticmethod
    def _build_payload(req: SubscribeRequest, symbols: list[str]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for symbol in symbols:
            row: dict[str, Any] = {
                "market_type": req.market_type,
                "stk_code": symbol,
            }
            if req.type is QuoteType.WATCHLIST:
                row["index_flag"] = req.index_flag if req.index_flag is not None else 7
            rows.append(row)
        return rows

    async def _call_adapter(self, operation: str, function_name: str, account: str, payload: list[dict[str, Any]]) -> None:
        try:
            method = getattr(self.adapter, operation, None)
            if not callable(method):
                # Compatibility with fakes that expose the Yuanta method directly.
                method = getattr(self.adapter, function_name, None)
                if not callable(method):
                    raise TypeError(f"adapter has no {operation}() or {function_name}()")
                try:
                    call = method(account, payload)
                except TypeError:
                    call = method(account, payload, 0)
            else:
                call = method(function_name, account, payload)

            if asyncio.iscoroutine(call) or hasattr(call, "__await__"):
                result = await call
            else:
                result = call
            if result is False:
                raise RuntimeError(f"{operation} {function_name} was rejected")
        except Exception as exc:
            if self.circuit_breaker is not None:
                self.circuit_breaker.record_failure(exc)
            raise
        if self.circuit_breaker is not None:
            self.circuit_breaker.record_success()

    @staticmethod
    def _serialize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {
                "account": row["account"],
                "type": row["type"],
                "symbol": row["symbol"],
                "market_type": row["market_type"],
            }
            if row.get("index_flag") is not None:
                item["index_flag"] = row["index_flag"]
            result.append(item)
        return result


__all__ = ["QuoteService", "QuoteServiceError"]
