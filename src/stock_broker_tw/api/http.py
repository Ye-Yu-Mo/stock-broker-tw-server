"""HTTP API routes: health, metrics, and session management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import CONTENT_TYPE_LATEST

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.config import Settings
from stock_broker_tw.metrics import metrics, render_metrics
from stock_broker_tw.service.session import LoginCredentials, SessionError, SessionService
from stock_broker_tw.yuanta.adapter import YuantaAdapter

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_adapter(request: Request) -> YuantaAdapter:
    return request.app.state.adapter


def get_session_service(request: Request) -> SessionService:
    return request.app.state.session_service


def get_audit(request: Request) -> AuditLogger:
    return request.app.state.audit


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


__all__ = ["router"]
