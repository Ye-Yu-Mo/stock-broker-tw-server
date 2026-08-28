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
from stock_broker_tw.config import Settings, load_settings
from stock_broker_tw.engine.queue import SerialOrderQueue
from stock_broker_tw.engine.report_handler import ReportHandler
from stock_broker_tw.metrics import metrics
from stock_broker_tw.risk.rules import RiskEngine
from stock_broker_tw.service.query import QueryService
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
    session_service = SessionService(adapter, settings, audit=audit)
    state_store = StateStore(settings.state.db_path)
    query_service = QueryService(adapter, settings, store=state_store, audit=audit)
    ws_manager = ConnectionManager()
    risk_engine = RiskEngine(settings)
    order_queue = SerialOrderQueue()
    broker_service = BrokerService(
        adapter,
        settings,
        store=state_store,
        audit=audit,
        queue=order_queue,
        risk=risk_engine,
        broadcaster=ws_manager,
    )
    report_handler = ReportHandler(state_store, broadcaster=ws_manager)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await ws_manager.start(adapter.event_queue, report_handler=report_handler)
        await run_startup_recovery(state_store, query_service, adapter)
        yield
        await ws_manager.stop()

    app = FastAPI(
        title="stock-broker-tw-server",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.adapter = adapter
    app.state.audit = audit
    app.state.session_service = session_service
    app.state.state_store = state_store
    app.state.store = state_store
    app.state.query_service = query_service
    app.state.ws_manager = ws_manager
    app.state.risk_engine = risk_engine
    app.state.order_queue = order_queue
    app.state.broker_service = broker_service
    app.state.report_handler = report_handler

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
