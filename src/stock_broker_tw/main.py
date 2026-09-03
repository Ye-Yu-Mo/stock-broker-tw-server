"""FastAPI application factory and uvicorn entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

import uvicorn
from fastapi import FastAPI

from stock_broker_tw.api.http import router as http_router
from stock_broker_tw.api.ws import ConnectionManager
from stock_broker_tw.api.ws import router as ws_router
from stock_broker_tw.audit import AuditLogger, setup_logging
from stock_broker_tw.broker.service import BrokerService
from stock_broker_tw.config import (
    Settings,
    load_settings,
    resolve_query_rate_limits,
    resolve_quote_rate_limits,
)
from stock_broker_tw.engine.queue import SerialOrderQueue
from stock_broker_tw.engine.report_handler import ReportHandler
from stock_broker_tw.metrics import metrics
from stock_broker_tw.notify import Notifier
from stock_broker_tw.risk.circuit_breaker import CircuitBreaker
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.risk.rules import RiskEngine
from stock_broker_tw.service.query import QueryService
from stock_broker_tw.service.quote import QuoteService
from stock_broker_tw.service.session import SessionService
from stock_broker_tw.state.recovery import run_startup_recovery
from stock_broker_tw.state.store import StateStore
from stock_broker_tw.yuanta.adapter import YuantaAdapter


def create_app(
    settings: Settings | None = None,
    adapter: YuantaAdapter | Any | None = None,
) -> FastAPI:
    """Build a FastAPI app with the given settings and adapter.

    ``adapter`` may be a real :class:`YuantaAdapter` or a test fake exposing the
    same session-related surface (``open``, ``login``, ``logout``, ``status``,
    ``event_queue``, ``last_login_result``).
    """
    settings = settings or load_settings()
    setup_logging(settings)

    adapter = adapter or YuantaAdapter(
        spark_api_dir=settings.yuanta.spark_api_dir,
        environment=settings.yuanta.environment,
        log_type=settings.yuanta.log_type,
        pmm_server_check=settings.yuanta.pmm_server_check,
    )

    audit = AuditLogger(enabled=settings.audit.enabled, file_path=settings.audit.file)
    notifier = Notifier(config=settings.notify)
    session_service = SessionService(adapter, settings, audit=audit)
    state_store = StateStore(settings.state.db_path)
    # Keep M3/M4 explicit query/quote rate settings working while still
    # allowing the unified rate_limit block to override them.
    query_per_second, query_per_minute = resolve_query_rate_limits(settings)
    quote_per_second, quote_per_minute = resolve_quote_rate_limits(settings)
    rate_limiter = RateLimiter(
        max_per_second=query_per_second,
        max_per_minute=query_per_minute,
        limits={
            "SendStockOrder": (
                settings.rate_limit.trade_per_second,
                settings.rate_limit.trade_per_minute,
            ),
            "SubscribeWatchlist": (quote_per_second, quote_per_minute),
            "UnSubscribeWatchlist": (quote_per_second, quote_per_minute),
            "SubscribeWatchlistAll": (quote_per_second, quote_per_minute),
            "UnSubscribeWatchlistAll": (quote_per_second, quote_per_minute),
            "SubscribeFiveTickA": (quote_per_second, quote_per_minute),
            "UnSubscribeFiveTickA": (quote_per_second, quote_per_minute),
            "SubscribeStockTick": (quote_per_second, quote_per_minute),
            "UnSubscribeStockTick": (quote_per_second, quote_per_minute),
            "SubscribeMarketInformation": (quote_per_second, quote_per_minute),
            "UnSubscribeMarketInformation": (quote_per_second, quote_per_minute),
            "SubscribeStockInformation": (quote_per_second, quote_per_minute),
            "UnSubscribeStockInformation": (quote_per_second, quote_per_minute),
        },
    )
    ws_manager = ConnectionManager()
    circuit_breaker = CircuitBreaker(
        failure_threshold=getattr(settings.risk, "circuit_failure_threshold", 5),
        cooldown_seconds=getattr(settings.risk, "circuit_cooldown_seconds", 30.0),
        notifier=notifier,
    )
    query_service = QueryService(
        adapter,
        settings,
        store=state_store,
        audit=audit,
        rate_limiter=rate_limiter,
        circuit_breaker=circuit_breaker,
    )
    quote_service = QuoteService(
        adapter,
        settings,
        store=state_store,
        audit=audit,
        rate_limiter=rate_limiter,
        circuit_breaker=circuit_breaker,
    )
    risk_engine = RiskEngine(settings, notifier=notifier)
    order_queue = SerialOrderQueue()
    broker_service = BrokerService(
        adapter,
        settings,
        store=state_store,
        audit=audit,
        queue=order_queue,
        risk=risk_engine,
        broadcaster=ws_manager,
        rate_limiter=rate_limiter,
        circuit_breaker=circuit_breaker,
        notifier=notifier,
    )
    report_handler = ReportHandler(state_store, broadcaster=ws_manager, notifier=notifier)

    async def recover_after_login() -> dict[str, Any]:
        summary = await run_startup_recovery(
            state_store,
            query_service,
            adapter,
            audit=audit,
            notifier=notifier,
        )
        app.state.last_recovery = summary
        return summary

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await ws_manager.start(adapter.event_queue, report_handler=report_handler)
        last_recovery = await run_startup_recovery(
            state_store,
            query_service,
            adapter,
            audit=audit,
            notifier=notifier,
        )
        app.state.last_recovery = last_recovery
        yield
        await ws_manager.stop()

    app = FastAPI(
        title="stock-broker-tw-server",
        version="0.1.1",
        lifespan=lifespan,
    )
    session_service.on_login_success = recover_after_login
    app.state.settings = settings
    app.state.adapter = adapter
    app.state.audit = audit
    app.state.session_service = session_service
    app.state.state_store = state_store
    app.state.store = state_store
    app.state.query_service = query_service
    app.state.quote_service = quote_service
    app.state.ws_manager = ws_manager
    app.state.risk_engine = risk_engine
    app.state.circuit_breaker = circuit_breaker
    app.state.notifier = notifier
    app.state.order_queue = order_queue
    app.state.broker_service = broker_service
    app.state.report_handler = report_handler
    app.state.last_recovery = None

    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        start = perf_counter()
        response = await call_next(request)
        duration = perf_counter() - start
        metrics.http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        ).inc()
        metrics.http_request_duration_seconds.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration)
        return response

    app.include_router(http_router)
    app.include_router(ws_router)
    return app


def run() -> None:
    """Run the FastAPI service with uvicorn using settings."""
    settings = load_settings()
    uvicorn.run(
        "stock_broker_tw.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level=settings.server.log_level.lower(),
    )


app = create_app()


__all__ = ["app", "create_app", "run"]
