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


def _raise_query_error(exc: QueryError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    ) from exc


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
    return {
        "status": "ok" if adapter_ready else "degraded",
        "adapter_ready": adapter_ready,
        "login_status": login_status,
        "event_queue_size": event_queue_size,
        "audit_enabled": settings.audit.enabled,
        "audit_file": settings.audit.file,
        "version": "0.1.0",
        "environment": settings.yuanta.environment,
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


@router.post("/api/v1/orders/stock", dependencies=[Depends(require_token)])
async def submit_stock_order(request: Request, payload: StockOrderPayload) -> dict[str, Any]:
    service = get_broker_service(request)
    request_id = request.headers.get("X-Request-ID")
    data = payload.model_dump()
    if payload.action == OrderAction.REPLACE:
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


__all__ = ["router"]
