"""Read-only query orchestration for M3 APIs."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.config import Settings
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.state.store import StateStore


class QueryError(Exception):
    """Raised when a read-only query cannot be completed."""

    def __init__(
        self,
        message: str,
        code: str = "QUERY_ERROR",
        status_code: int = 400,
        detail: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail


class QueryService:
    """Call Yuanta query functions and persist local snapshots/reports."""

    def __init__(
        self,
        adapter: Any,
        settings: Settings,
        store: StateStore | None = None,
        state_store: StateStore | None = None,
        rate_limiter: RateLimiter | None = None,
        audit: AuditLogger | None = None,
    ) -> None:
        self.adapter = adapter
        self.settings = settings
        self.store = store or state_store or StateStore(settings.state.db_path)
        self.state_store = self.store
        self.rate_limiter = rate_limiter or RateLimiter(
            max_per_second=settings.query.rate_limit_per_second,
            max_per_minute=settings.query.rate_limit_per_minute,
        )
        self.audit = audit or AuditLogger(
            enabled=settings.audit.enabled,
            file_path=settings.audit.file,
        )

    # -- public query methods ---------------------------------------------

    async def positions(self, account: str | None = None, request_id: str | None = None) -> Any:
        acct = self._account(account)
        try:
            data = await self._query("GetStoreSummary", request_id=request_id, Account=acct)
        except QueryError as exc:
            if exc.code == "RATE_LIMITED":
                raise
            cached = self.store.get_latest_snapshot("positions", account=acct)
            if cached is not None:
                cached_data = cached["data"]
                if isinstance(cached_data, dict):
                    return {
                        "from_cache": True,
                        "cached_at": cached["created_at"],
                        **cached_data,
                    }
                return {
                    "from_cache": True,
                    "cached_at": cached["created_at"],
                    "data": cached_data,
                }
            raise
        self.store.save_snapshot("positions", data, account=acct)
        return data

    async def account_balance(
        self, account: str | None = None, request_id: str | None = None
    ) -> Any:
        acct = self._account(account)
        data = await self._query("GetBankBalance", request_id=request_id, Account=acct)
        self.store.save_snapshot("bank_balance", data, account=acct)
        return data

    async def settlement(self, account: str | None = None, request_id: str | None = None) -> Any:
        acct = self._account(account)
        data = await self._query(
            "GetStkTransactionOutlay", request_id=request_id, Account=acct
        )
        self.store.save_snapshot("settlement", data, account=acct)
        return data

    async def unrealized_pnl(
        self,
        market_type: str = "TWSE",
        stk_code: str = "",
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        data = await self._query(
            "GetUnrealizedGainLossDetail",
            request_id=request_id,
            Account=acct,
            MarketType=market_type,
            StkCode=stk_code,
        )
        self.store.save_snapshot("pnl_unrealized", data, account=acct)
        return data

    async def realized_pnl(
        self,
        start_date: str,
        end_date: str,
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        start_date = self.validate_date(start_date, "start_date")
        end_date = self.validate_date(end_date, "end_date")
        data = await self._query(
            "GetHisRealizedGainLoss",
            request_id=request_id,
            Account=acct,
            SDate=start_date,
            EDate=end_date,
        )
        self.store.save_snapshot("pnl_realized", data, account=acct)
        return data

    async def reversal_pnl(
        self,
        re_gain_loss: Any = None,
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        payload = re_gain_loss if re_gain_loss is not None else {}
        data = await self._query(
            "GetStkHistoryReportReversal",
            request_id=request_id,
            Account=acct,
            ReGainLoss=payload,
        )
        self.store.save_snapshot("pnl_reversal", data, account=acct)
        return data

    async def real_reports(self, account: str | None = None, request_id: str | None = None) -> Any:
        acct = self._account(account)
        data = await self._query("GetRealReport", request_id=request_id, Account=acct)
        self.store.save_reports("GetRealReport", data.get("real_report_list", []))
        return data

    async def real_reports_merge(
        self, account: str | None = None, request_id: str | None = None
    ) -> Any:
        acct = self._account(account)
        data = await self._query("GetRealReportMerge", request_id=request_id, Account=acct)
        self.store.save_reports("GetRealReportMerge", data.get("real_report_merge_list", []))
        return data

    async def order_trade_reports(
        self,
        notshow_cancel: bool = False,
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        data = await self._query(
            "GetOrderTradeReport",
            request_id=request_id,
            NotshowCancel=bool(notshow_cancel),
            Account=acct,
        )
        self.store.save_orders(data.get("stk_order_list", []))
        self.store.save_trades(data.get("stk_trade_list", []))
        self.store.save_reports(
            "GetOrderTradeReport",
            [
                {**item, "report_type": "order"}
                for item in data.get("stk_order_list", [])
            ],
        )
        return data

    # -- M5 quote query methods --------------------------------------------

    async def quote_list(
        self,
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        """Call GetQuoteList to read the broker-side subscribed quote list."""
        acct = self._account(account)
        return await self._query("GetQuoteList", request_id=request_id, Account=acct)

    async def watchlist_snapshot(
        self,
        stk_code: str = "",
        market_type: str = "TWSE",
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        quote_list = self._quote_list(stk_code, market_type)
        data = await self._query(
            "GetWatchListAll",
            request_id=request_id,
            Account=acct,
            QuoteList=quote_list,
        )
        self.store.save_snapshot("quote_snapshot", data, account=acct)
        return data

    async def stock_info(
        self,
        stk_code: str = "",
        market_type: str = "TWSE",
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        if not stk_code:
            raise QueryError(
                "stk_code is required",
                code="INVALID_REQUEST",
                status_code=400,
                detail={"field": "stk_code"},
            )
        stk_list = self._quote_list(stk_code, market_type)
        data = await self._query(
            "GetStockInformation",
            request_id=request_id,
            Account=acct,
            StkList=stk_list,
        )
        self.store.save_snapshot("stock_info", data, account=acct)
        return data

    async def stock_ticks(
        self,
        stk_code: str,
        market_type: str = "TWSE",
        select_type: int = 1,
        start_time: str = "",
        end_time: str = "",
        last_count: int = 20,
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        if not stk_code:
            raise QueryError(
                "stk_code is required",
                code="INVALID_REQUEST",
                status_code=400,
                detail={"field": "stk_code"},
            )
        data = await self._query(
            "GetStkTickDetail",
            request_id=request_id,
            Account=acct,
            MarketType=market_type,
            StkCode=stk_code,
            SelectType=select_type,
            Stime=start_time,
            Etime=end_time,
            LastCount=last_count,
        )
        self.store.save_snapshot("stock_ticks", data, account=acct)
        return data

    async def classify_price(
        self,
        stk_code: str,
        market_type: str = "TWSE",
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        if not stk_code:
            raise QueryError(
                "stk_code is required",
                code="INVALID_REQUEST",
                status_code=400,
                detail={"field": "stk_code"},
            )
        data = await self._query(
            "GetStkClassifyPrice",
            request_id=request_id,
            Account=acct,
            MarketType=market_type,
            StkCode=stk_code,
        )
        self.store.save_snapshot("classify_price", data, account=acct)
        return data

    async def kline(
        self,
        stk_code: str,
        kline_type: int = 11,
        market_type: str = "TWSE",
        start_date: str = "",
        end_date: str = "",
        account: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        acct = self._account(account)
        if not stk_code:
            raise QueryError(
                "stk_code is required",
                code="INVALID_REQUEST",
                status_code=400,
                detail={"field": "stk_code"},
            )
        start_date = self.validate_date(start_date, "start_date")
        end_date = self.validate_date(end_date, "end_date")
        data = await self._query(
            "GetKLine",
            request_id=request_id,
            Account=acct,
            KLineType=kline_type,
            MarketType=market_type,
            StkCode=stk_code,
            SDate=start_date,
            EDate=end_date,
        )
        self.store.save_snapshot("kline", data, account=acct)
        return data

    @staticmethod
    def _quote_list(stk_code: str, market_type: str) -> list[dict[str, Any]]:
        symbols = [s.strip() for s in stk_code.split(",") if s.strip()]
        return [
            {"market_type": market_type.upper(), "stock_code": symbol}
            for symbol in symbols
        ]

    # -- convenience aliases ----------------------------------------------

    get_positions = positions
    bank_balance = account_balance
    get_bank_balance = account_balance
    get_account_balance = account_balance
    get_settlement = settlement
    get_unrealized_pnl = unrealized_pnl
    pnl_unrealized = unrealized_pnl
    get_realized_pnl = realized_pnl
    pnl_realized = realized_pnl
    get_reversal_pnl = reversal_pnl
    pnl_reversal = reversal_pnl
    get_real_reports = real_reports
    real_report = real_reports
    get_real_report_merge = real_reports_merge
    real_report_merge = real_reports_merge
    get_order_trade_reports = order_trade_reports
    get_order_trade_report = order_trade_reports
    order_trade_report = order_trade_reports
    get_quote_list = quote_list
    snapshot = watchlist_snapshot
    get_watchlist_snapshot = watchlist_snapshot
    ticks = stock_ticks
    get_stock_ticks = stock_ticks
    get_stock_info = stock_info
    get_classify_price = classify_price
    get_kline = kline

    # -- helpers -----------------------------------------------------------

    def _account(self, account: str | None = None) -> str:
        return account or self.settings.account.account

    async def _query(self, function_name: str, request_id: str | None = None, **params: Any) -> Any:
        if not self.rate_limiter.acquire(function_name):
            self.audit.record(
                "query.rate_limited",
                result="error",
                request_id=request_id,
                account=params.get("Account"),
                function=function_name,
            )
            raise QueryError(
                "query rate limit exceeded",
                code="RATE_LIMITED",
                status_code=429,
                detail={"function": function_name},
            )

        self.audit.record(
            "query.start",
            result="attempt",
            request_id=request_id,
            account=params.get("Account"),
            function=function_name,
        )

        try:
            query_method = self.adapter.query

            async def _run_query() -> Any:
                try:
                    if asyncio.iscoroutinefunction(query_method):
                        return await query_method(function_name, **params)
                    return await asyncio.to_thread(query_method, function_name, **params)
                except TypeError:
                    # Some fake/legacy query methods only accept positional args.
                    if asyncio.iscoroutinefunction(query_method):
                        return await query_method(function_name, *params.values())
                    return await asyncio.to_thread(
                        query_method, function_name, *params.values()
                    )

            result = await asyncio.wait_for(
                _run_query(),
                timeout=self.settings.query.timeout,
            )
        except TimeoutError as exc:
            self.audit.record(
                "query.timeout",
                result="error",
                request_id=request_id,
                account=params.get("Account"),
                function=function_name,
                error=str(exc),
            )
            raise QueryError(
                f"query {function_name} timed out",
                code="QUERY_TIMEOUT",
                status_code=504,
                detail={"function": function_name},
            ) from exc
        except QueryError:
            raise
        except Exception as exc:
            self.audit.record(
                "query.error",
                result="error",
                request_id=request_id,
                account=params.get("Account"),
                function=function_name,
                error=str(exc),
            )
            raise QueryError(
                f"query {function_name} failed: {exc}",
                code="QUERY_ERROR",
                status_code=502,
                detail={"function": function_name},
            ) from exc

        self.audit.record(
            "query.success",
            result="success",
            request_id=request_id,
            account=params.get("Account"),
            function=function_name,
        )
        return result

    @staticmethod
    def validate_date(value: str, field_name: str = "date") -> str:
        """Validate and normalize a Yuanta date in ``yyyy/MM/dd`` format."""
        if not value:
            raise QueryError(
                f"{field_name} is required",
                code="INVALID_REQUEST",
                status_code=400,
                detail={"field": field_name},
            )
        try:
            datetime.strptime(value, "%Y/%m/%d").replace(tzinfo=UTC)
        except ValueError as exc:
            raise QueryError(
                f"{field_name} must be in yyyy/MM/dd format",
                code="INVALID_DATE",
                status_code=400,
                detail={"field": field_name, "value": value},
            ) from exc
        return value


__all__ = ["QueryError", "QueryService"]
