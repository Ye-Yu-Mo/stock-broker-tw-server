"""HTTP API routes: health, metrics, and session management."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.broker.service import BrokerService, BrokerServiceError
from stock_broker_tw.config import Settings
from stock_broker_tw.engine.state import OrderAction
from stock_broker_tw.metrics import metrics, render_metrics
from stock_broker_tw.risk.rules import RiskError
from stock_broker_tw.service.query import QueryError, QueryService
from stock_broker_tw.service.quote import QuoteService, QuoteServiceError
from stock_broker_tw.service.session import LoginCredentials, SessionError, SessionService
from stock_broker_tw.yuanta.adapter import YuantaAdapter

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


class StockOrderPayload(BaseModel):
    """HTTP body for the unified stock order endpoint."""

    client_order_id: str = Field(..., min_length=1, max_length=64)
    action: OrderAction = OrderAction.NEW
    account: str | None = None
    stk_code: str = ""
    side: str = "B"
    price: float | None = None
    quantity: int = 0
    time_in_force: str = "ROD"
    price_flag: str = "LIMIT"
    order_no: str | None = None
    trade_date: str | None = None
    new_price: float | None = None
    new_quantity: int | None = None


class QuoteSubscribePayload(BaseModel):
    """HTTP body for quote subscribe/unsubscribe."""

    type: str
    symbols: list[str] = Field(default_factory=list)
    account: str | None = None
    market_type: str = "TWSE"
    index_flag: int | None = None


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_adapter(request: Request) -> YuantaAdapter:
    return request.app.state.adapter


def get_session_service(request: Request) -> SessionService:
    return request.app.state.session_service


def get_query_service(request: Request) -> QueryService:
    return request.app.state.query_service


def get_audit(request: Request) -> AuditLogger:
    return request.app.state.audit


def get_broker_service(request: Request) -> BrokerService:
    return request.app.state.broker_service


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.quote_service


def get_risk_engine(request: Request):
    return request.app.state.risk_engine


def get_circuit_breaker(request: Request):
    return request.app.state.circuit_breaker


def _raise_query_error(exc: QueryError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    ) from exc


def _raise_quote_error(exc: QuoteServiceError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    ) from exc


def _quote_list_items(data: Any) -> Any:
    """Normalize GetQuoteList responses into a list of quote rows."""
    if isinstance(data, dict):
        for key in ("quote_list", "QuoteList", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return data
    if isinstance(data, list):
        return data
    return data


async def require_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),  # noqa: B008
) -> None:
    settings = get_settings(request)
    expected = settings.server.api_token
    if not expected:
        return
    if credentials is None or credentials.credentials != expected:
        metrics.risk_rejections_total.labels(reason="invalid_token").inc()
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "missing or invalid bearer token"},
        )


def ok(data: Any = None) -> dict[str, Any]:
    return {"code": 0, "message": "ok", "data": data}


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Return service health without requiring authentication."""
    adapter = get_adapter(request)
    try:
        adapter_ready = bool(adapter is not None and (adapter.opened or getattr(adapter, "trader", None)))
        login_status = bool(adapter is not None and adapter.logged_in)
        event_queue_size = adapter.event_queue.qsize() if adapter is not None else 0
    except Exception:
        adapter_ready = False
        login_status = False
        event_queue_size = 0

    settings = get_settings(request)
    risk_engine = getattr(request.app.state, "risk_engine", None)
    circuit_breaker = getattr(request.app.state, "circuit_breaker", None)
    last_recovery = getattr(request.app.state, "last_recovery", None)
    return {
        "status": "ok" if adapter_ready else "degraded",
        "adapter_ready": adapter_ready,
        "login_status": login_status,
        "event_queue_size": event_queue_size,
        "audit_enabled": settings.audit.enabled,
        "audit_file": settings.audit.file,
        "version": "0.1.0",
        "environment": settings.yuanta.environment,
        "panic": bool(getattr(risk_engine, "panic", False)) if risk_engine is not None else False,
        "circuit_breaker_open": bool(getattr(circuit_breaker, "is_open", False)) if circuit_breaker is not None else False,
        "circuit_breaker": circuit_breaker.to_dict() if circuit_breaker is not None else None,
        "last_failure": getattr(circuit_breaker, "last_error", None) if circuit_breaker is not None else None,
        "last_recovery": last_recovery,
    }


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint; intentionally public."""
    return Response(content=render_metrics(), media_type=CONTENT_TYPE_LATEST)


@router.post("/api/v1/session/login", dependencies=[Depends(require_token)])
async def login(
    request: Request,
    payload: LoginCredentials | None = None,
) -> dict[str, Any]:
    service = get_session_service(request)
    request_id = request.headers.get("X-Request-ID")
    try:
        result = await service.login(payload or LoginCredentials(), request_id=request_id)
    except SessionError as exc:
        metrics.risk_rejections_total.labels(reason="login_failed").inc()
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    login_list = result.get("login_list") or []
    first = login_list[0] if login_list else {}
    return ok(
        {
            "login": result,
            "account": first.get("account"),
            "name": first.get("name"),
            "investor_id": first.get("investor_id"),
        }
    )


@router.post("/api/v1/session/logout", dependencies=[Depends(require_token)])
async def logout(request: Request) -> dict[str, Any]:
    service = get_session_service(request)
    request_id = request.headers.get("X-Request-ID")
    try:
        result = await service.logout(request_id=request_id)
    except SessionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    return ok(result)


@router.get("/api/v1/session/status", dependencies=[Depends(require_token)])
async def status(request: Request) -> dict[str, Any]:
    service = get_session_service(request)
    return ok(service.status())


@router.get("/api/v1/positions", dependencies=[Depends(require_token)])
async def positions(request: Request, account: str | None = None) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(await service.positions(account=account, request_id=request.headers.get("X-Request-ID")))
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/account/balance", dependencies=[Depends(require_token)])
async def account_balance(request: Request, account: str | None = None) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(await service.account_balance(account=account, request_id=request.headers.get("X-Request-ID")))
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/account/settlement", dependencies=[Depends(require_token)])
async def settlement(request: Request, account: str | None = None) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(await service.settlement(account=account, request_id=request.headers.get("X-Request-ID")))
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/pnl/unrealized", dependencies=[Depends(require_token)])
async def pnl_unrealized(
    request: Request,
    market_type: str = "TWSE",
    stk_code: str = "",
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.unrealized_pnl(
                market_type=market_type,
                stk_code=stk_code,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/pnl/realized", dependencies=[Depends(require_token)])
async def pnl_realized(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.realized_pnl(
                start_date=start_date or "",
                end_date=end_date or "",
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/pnl/reversal", dependencies=[Depends(require_token)])
async def pnl_reversal(
    request: Request,
    re_gain_loss: str | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    payload: dict[str, Any] | None = None
    if re_gain_loss:
        try:
            payload = json.loads(re_gain_loss)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_REQUEST",
                    "message": "re_gain_loss must be a JSON object",
                    "detail": {"value": re_gain_loss},
                },
            ) from exc
    try:
        return ok(
            await service.reversal_pnl(
                re_gain_loss=payload,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/reports/real", dependencies=[Depends(require_token)])
async def reports_real(request: Request, account: str | None = None) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(await service.real_reports(account=account, request_id=request.headers.get("X-Request-ID")))
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/reports/real-merge", dependencies=[Depends(require_token)])
async def reports_real_merge(request: Request, account: str | None = None) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(await service.real_reports_merge(account=account, request_id=request.headers.get("X-Request-ID")))
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/reports/order-trade", dependencies=[Depends(require_token)])
async def reports_order_trade(
    request: Request,
    notshow_cancel: bool = False,
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.order_trade_reports(
                notshow_cancel=notshow_cancel,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.post("/api/v1/quotes/subscribe", dependencies=[Depends(require_token)])
async def quotes_subscribe(request: Request, payload: QuoteSubscribePayload) -> dict[str, Any]:
    service = get_quote_service(request)
    try:
        result = await service.subscribe(
            payload.model_dump(),
            request_id=request.headers.get("X-Request-ID"),
        )
    except QuoteServiceError as exc:
        _raise_quote_error(exc)
    return ok(result)


@router.post("/api/v1/quotes/unsubscribe", dependencies=[Depends(require_token)])
async def quotes_unsubscribe(request: Request, payload: QuoteSubscribePayload) -> dict[str, Any]:
    service = get_quote_service(request)
    try:
        result = await service.unsubscribe(
            payload.model_dump(),
            request_id=request.headers.get("X-Request-ID"),
        )
    except QuoteServiceError as exc:
        _raise_quote_error(exc)
    return ok(result)


@router.get("/api/v1/quotes/subscribed", dependencies=[Depends(require_token)])
async def quotes_subscribed(
    request: Request,
    account: str | None = None,
    type: str | None = None,
    quote_type: str | None = None,
    source: str = "local",
) -> dict[str, Any]:
    service = get_quote_service(request)
    acct = account or request.app.state.settings.account.account
    normalized_source = (source or "local").lower()
    if normalized_source in {"broker", "remote", "yuanta"}:
        query_service = get_query_service(request)
        try:
            broker = await query_service.quote_list(
                account=acct,
                request_id=request.headers.get("X-Request-ID"),
            )
        except QueryError as exc:
            _raise_query_error(exc)
        return ok({"source": "broker", "items": _quote_list_items(broker)})
    if normalized_source in {"both", "all"}:
        local = service.list_subscribed(account=acct, quote_type=type or quote_type)
        query_service = get_query_service(request)
        try:
            broker = await query_service.quote_list(
                account=acct,
                request_id=request.headers.get("X-Request-ID"),
            )
        except QueryError as exc:
            _raise_query_error(exc)
        return ok({"source": "both", "local": local, "broker": _quote_list_items(broker)})
    # Backwards-compatible default: return the local subscription list directly.
    return ok(service.list_subscribed(account=acct, quote_type=type or quote_type))


@router.get("/api/v1/quotes/snapshot", dependencies=[Depends(require_token)])
async def quotes_snapshot(
    request: Request,
    stk_code: str = "",
    symbols: str = "",
    market_type: str = "TWSE",
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    symbols_param = stk_code or symbols
    if not symbols_param:
        quote_service = get_quote_service(request)
        symbols_param = ",".join(
            item["symbol"] for item in quote_service.list_subscribed(account=account)
        )
    try:
        return ok(
            await service.watchlist_snapshot(
                stk_code=symbols_param,
                market_type=market_type,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/quotes/ticks", dependencies=[Depends(require_token)])
async def quotes_ticks(
    request: Request,
    stk_code: str = "",
    market_type: str = "TWSE",
    select_type: int = 1,
    start_time: str = "",
    end_time: str = "",
    stime: str = "",
    etime: str = "",
    s_time: str = "",
    e_time: str = "",
    last_count: int = 20,
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.stock_ticks(
                stk_code=stk_code,
                market_type=market_type,
                select_type=select_type,
                start_time=start_time or stime or s_time,
                end_time=end_time or etime or e_time,
                last_count=last_count,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/quotes/classify-price", dependencies=[Depends(require_token)])
async def quotes_classify_price(
    request: Request,
    stk_code: str = "",
    market_type: str = "TWSE",
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.classify_price(
                stk_code=stk_code,
                market_type=market_type,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/quotes/kline", dependencies=[Depends(require_token)])
async def quotes_kline(
    request: Request,
    stk_code: str = "",
    kline_type: int = 11,
    market_type: str = "TWSE",
    start_date: str = "",
    end_date: str = "",
    s_date: str = "",
    e_date: str = "",
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.kline(
                stk_code=stk_code,
                kline_type=kline_type,
                market_type=market_type,
                start_date=start_date or s_date,
                end_date=end_date or e_date,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.get("/api/v1/stocks/info", dependencies=[Depends(require_token)])
async def stocks_info(
    request: Request,
    stk_code: str = "",
    symbols: str = "",
    market_type: str = "TWSE",
    account: str | None = None,
) -> dict[str, Any]:
    service = get_query_service(request)
    try:
        return ok(
            await service.stock_info(
                stk_code=stk_code or symbols,
                market_type=market_type,
                account=account,
                request_id=request.headers.get("X-Request-ID"),
            )
        )
    except QueryError as exc:
        _raise_query_error(exc)


@router.post("/api/v1/orders/stock", dependencies=[Depends(require_token)])
async def submit_stock_order(request: Request, payload: StockOrderPayload) -> dict[str, Any]:
    service = get_broker_service(request)
    request_id = request.headers.get("X-Request-ID")
    data = payload.model_dump()
    if payload.action == OrderAction.REPLACE:
        if data.get("new_price") is not None and data.get("new_quantity") is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "REPLACE_BOTH_FIELDS_UNSUPPORTED",
                    "message": "simultaneously changing price and quantity is not supported; submit two replace operations",
                    "detail": {"new_price": data.get("new_price"), "new_quantity": data.get("new_quantity")},
                },
            )
        if data.get("new_price") is not None:
            data["price"] = data["new_price"]
        if data.get("new_quantity") is not None:
            data["quantity"] = data["new_quantity"]
    try:
        result = await service.submit_stock_order(data, request_id=request_id)
    except (BrokerServiceError, RiskError) as exc:
        status_code = exc.status_code if hasattr(exc, "status_code") else 400
        code = exc.code if hasattr(exc, "code") else "ORDER_ERROR"
        message = exc.message if hasattr(exc, "message") else str(exc)
        detail = getattr(exc, "detail", None) or {}
        raise HTTPException(
            status_code=status_code,
            detail={"code": code, "message": message, "detail": detail},
        ) from exc
    return ok(result)


@router.get("/api/v1/orders", dependencies=[Depends(require_token)])
async def list_orders(
    request: Request,
    account: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    service = get_broker_service(request)
    return ok(service.list_orders(account=account, status=status))


@router.get("/api/v1/orders/{client_order_id}", dependencies=[Depends(require_token)])
async def get_order(request: Request, client_order_id: str) -> dict[str, Any]:
    service = get_broker_service(request)
    order = service.get_order(client_order_id)
    if order is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ORDER_NOT_FOUND",
                "message": "order not found",
                "detail": {"client_order_id": client_order_id},
            },
        )
    return ok(order)


@router.post("/api/v1/control/panic", dependencies=[Depends(require_token)])
async def control_panic(request: Request) -> dict[str, Any]:
    """Dynamically enable market panic (blocks all trading)."""
    risk_engine = get_risk_engine(request)
    risk_engine.set_panic(True)
    get_audit(request).record("control.panic", result="success", account=None)
    return ok({"panic": True})


@router.post("/api/v1/control/resume", dependencies=[Depends(require_token)])
async def control_resume(request: Request) -> dict[str, Any]:
    """Dynamically disable market panic and reset the circuit breaker."""
    risk_engine = get_risk_engine(request)
    risk_engine.set_panic(False)
    circuit_breaker = get_circuit_breaker(request)
    if circuit_breaker is not None:
        circuit_breaker.manual_reset()
    get_audit(request).record("control.resume", result="success", account=None)
    return ok({"panic": False, "circuit_breaker": circuit_breaker.to_dict() if circuit_breaker is not None else None})


@router.get("/api/v1/recovery/unresolved", dependencies=[Depends(require_token)])
async def recovery_unresolved(request: Request) -> dict[str, Any]:
    """Return orders that startup recovery could not resolve automatically."""
    store = request.app.state.store
    return ok(store.list_unresolved_recovery())


class ResolveRecoveryPayload(BaseModel):
    """Body for manually resolving an unknown order."""

    status: str = "FILLED"
    order_no: str | None = None
    trade_date: str | None = None
    source: str | None = None
    note: str | None = None


@router.post("/api/v1/recovery/{client_order_id}/resolve", dependencies=[Depends(require_token)])
async def recovery_resolve(
    request: Request,
    client_order_id: str,
    payload: ResolveRecoveryPayload | None = None,
) -> dict[str, Any]:
    """Manually confirm/resolve an unknown order."""
    store = request.app.state.store
    body = payload.model_dump() if payload is not None else {}
    status = body.get("status") or "FILLED"
    order_no = body.get("order_no")
    trade_date = body.get("trade_date")
    note = body.get("note")
    source = (body.get("source") or "").lower()

    if source == "orders":
        if not order_no:
            raise HTTPException(
                status_code=400,
                detail={"code": "ORDER_NO_REQUIRED", "message": "order_no is required for legacy orders"},
            )
        resolved = store.resolve_legacy_order(
            order_no=order_no,
            status=status,
            trade_date=trade_date,
            note=note,
        )
        if resolved is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "ORDER_NOT_FOUND", "message": "legacy order not found", "detail": {"order_no": order_no}},
            )
        get_audit(request).record("recovery.resolve", result="success", account=None, client_order_id=client_order_id, source="orders", status=status)
        return ok(resolved)

    resolved = store.resolve_stock_order(
        client_order_id,
        status=status,
        order_no=order_no,
        trade_date=trade_date,
        note=note,
    )
    if resolved is None and (order_no or client_order_id):
        legacy_order_no = order_no or client_order_id
        resolved = store.resolve_legacy_order(
            order_no=legacy_order_no,
            status=status,
            trade_date=trade_date,
            note=note,
        )
        if resolved is not None:
            get_audit(request).record("recovery.resolve", result="success", account=None, client_order_id=client_order_id, source="orders", status=status)
            return ok(resolved)
    if resolved is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "ORDER_NOT_FOUND", "message": "order not found", "detail": {"client_order_id": client_order_id}},
        )
    get_audit(request).record("recovery.resolve", result="success", account=None, client_order_id=client_order_id, source="stock_orders", status=status)
    return ok(resolved)


__all__ = ["router"]
