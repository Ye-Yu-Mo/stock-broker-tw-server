"""Session service: login/logout/status orchestration for the Yuanta adapter."""

from __future__ import annotations

import asyncio
import inspect
import logging
import uuid
from typing import Any

from pydantic import BaseModel

from stock_broker_tw.audit import AuditLogger
from stock_broker_tw.config import Settings
from stock_broker_tw.metrics import metrics
from stock_broker_tw.yuanta.adapter import YuantaAdapter, YuantaAdapterError

logger = logging.getLogger(__name__)


class SessionError(Exception):
    """Raised when a session operation cannot be completed."""

    def __init__(self, message: str, code: str = "SESSION_ERROR", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class LoginCredentials(BaseModel):
    """Credentials accepted by the session login endpoint."""

    account: str | None = None
    password: str | None = None
    pfx_path: str | None = None
    pfx_pass: str | None = None


class SessionService:
    """Own the session lifecycle on top of :class:`YuantaAdapter`."""

    def __init__(
        self,
        adapter: YuantaAdapter,
        settings: Settings,
        audit: AuditLogger | None = None,
        on_login_success: Any = None,
    ) -> None:
        self.adapter = adapter
        self.settings = settings
        self.audit = audit or AuditLogger(enabled=settings.audit.enabled, file_path=settings.audit.file)
        self.on_login_success = on_login_success

    async def login(
        self,
        credentials: LoginCredentials,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        request_id = request_id or str(uuid.uuid4())
        account = credentials.account or self.settings.account.account
        password = credentials.password or self.settings.account.password
        pfx_path = credentials.pfx_path or self.settings.account.pfx_path
        pfx_pass = credentials.pfx_pass or self.settings.account.pfx_pass

        if not account or not password:
            self.audit.record(
                "session.login",
                result="error",
                request_id=request_id,
                account=account,
                error="missing account or password",
            )
            raise SessionError("account and password are required", code="INVALID_REQUEST", status_code=400)

        metrics.login_attempts_total.labels(result="attempt").inc()
        self.audit.record(
            "session.login",
            result="attempt",
            request_id=request_id,
            account=account,
            method="pfx" if pfx_path else "password",
        )

        try:
            logger.debug(
                "session login dispatch: request_id=%s environment=%s method=%s",
                request_id,
                self.settings.yuanta.environment,
                "pfx" if pfx_path else "password",
            )
            self.adapter.open()
            self._clear_login_result(self.adapter)
            accepted = self.adapter.login(
                account,
                password,
                pfx_path=pfx_path,
                pfx_pass=pfx_pass,
            )
            logger.debug(
                "session login dispatch result: request_id=%s accepted=%s opened=%s logged_in=%s",
                request_id,
                bool(accepted),
                getattr(self.adapter, "opened", None),
                getattr(self.adapter, "logged_in", None),
            )
        except YuantaAdapterError as exc:
            metrics.login_attempts_total.labels(result="error").inc()
            self.audit.record(
                "session.login",
                result="error",
                request_id=request_id,
                account=account,
                error=str(exc),
            )
            raise SessionError(
                str(exc),
                code="ADAPTER_ERROR",
                status_code=409 if "already logged in" in str(exc) else 400,
            ) from exc

        if not accepted:
            logger.warning(
                "session login rejected by adapter: request_id=%s accepted=False opened=%s logged_in=%s",
                request_id,
                getattr(self.adapter, "opened", None),
                getattr(self.adapter, "logged_in", None),
            )
            metrics.login_attempts_total.labels(result="error").inc()
            self.audit.record(
                "session.login",
                result="error",
                request_id=request_id,
                account=account,
                error="login request rejected by adapter",
            )
            raise SessionError("login request was rejected", code="LOGIN_REJECTED", status_code=502)

        logger.debug(
            "waiting for Login response: request_id=%s timeout=%.1fs",
            request_id,
            self.settings.yuanta.login_timeout,
        )
        try:
            result = await self._wait_for_login_result(self.adapter, self.settings.yuanta.login_timeout)
            logger.debug(
                "Login response cache populated: request_id=%s login_entries=%s",
                request_id,
                len(result.get("login_list") or []),
            )
        except TimeoutError as exc:
            logger.warning(
                "Login response timeout: request_id=%s timeout=%.1fs",
                request_id,
                self.settings.yuanta.login_timeout,
            )
            metrics.login_attempts_total.labels(result="timeout").inc()
            self.audit.record(
                "session.login",
                result="timeout",
                request_id=request_id,
                account=account,
            )
            raise SessionError("timed out waiting for Login response", code="LOGIN_TIMEOUT", status_code=504) from exc

        login_list = result.get("login_list") or []
        if not login_list:
            status = result.get("login_status") or {}
            message = status.get("msg_content") or "login failed"
            code = str(status.get("msg_code") or "LOGIN_FAILED")
            logger.warning(
                "Login response indicates failure: request_id=%s msg_code=%s msg_content_present=%s login_entries=%s",
                request_id,
                code,
                bool(status.get("msg_content")),
                len(login_list),
            )
            metrics.login_attempts_total.labels(result="error").inc()
            self.audit.record(
                "session.login",
                result="error",
                request_id=request_id,
                account=account,
                error=f"login failed ({code})",
                login_status={
                    "msg_code": code,
                    "msg_content_present": bool(status.get("msg_content")),
                    "count": status.get("count"),
                },
            )
            raise SessionError(message, code=code, status_code=401)

        logger.info(
            "Login response indicates success: request_id=%s login_entries=%s",
            request_id,
            len(login_list),
        )
        metrics.login_attempts_total.labels(result="success").inc()
        self.audit.record(
            "session.login",
            result="success",
            request_id=request_id,
            account=account,
            login_list=login_list,
        )
        if self.on_login_success is not None:
            try:
                recovery = self.on_login_success()
                if inspect.isawaitable(recovery):
                    await recovery
            except Exception as exc:  # noqa: BLE001 - recovery must not block login
                self.audit.record(
                    "recovery.after_login",
                    result="error",
                    request_id=request_id,
                    account=account,
                    error=str(exc),
                )
        return result

    async def logout(self, request_id: str | None = None) -> dict[str, Any]:
        request_id = request_id or str(uuid.uuid4())
        last_login = getattr(self.adapter, "last_login_result", None)
        login_list = (last_login or {}).get("login_list") or []
        account = login_list[0].get("account") if login_list else self.settings.account.account
        try:
            self.adapter.logout()
        except YuantaAdapterError as exc:
            metrics.logout_attempts_total.labels(result="error").inc()
            self.audit.record(
                "session.logout",
                result="error",
                request_id=request_id,
                account=account,
                error=str(exc),
            )
            raise SessionError(str(exc), code="ADAPTER_ERROR", status_code=400) from exc
        self._clear_login_result(self.adapter)
        metrics.logout_attempts_total.labels(result="success").inc()
        self.audit.record(
            "session.logout",
            result="success",
            request_id=request_id,
            account=account,
        )
        return {"logged_in": False}

    def status(self) -> dict[str, Any]:
        adapter = self.adapter
        event_queue = getattr(adapter, "event_queue", None)
        return {
            "opened": getattr(adapter, "opened", False),
            "logged_in": getattr(adapter, "logged_in", False),
            "disposed": getattr(adapter, "disposed", False),
            "last_login_result": getattr(adapter, "last_login_result", None),
            "event_queue_size": event_queue.qsize() if event_queue is not None else 0,
        }

    @staticmethod
    def _clear_login_result(adapter: YuantaAdapter) -> None:
        """Clear cached login result on adapters with or without a helper method."""
        reset = getattr(adapter, "reset_login_result", None)
        if callable(reset):
            reset()
            return
        try:
            adapter.last_login_result = None  # type: ignore[attr-defined]
        except Exception:
            pass

    @staticmethod
    async def _wait_for_login_result(adapter: YuantaAdapter, timeout: float) -> dict[str, Any]:
        """Wait for the adapter cache without consuming shared raw events."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            last_login_result = getattr(adapter, "last_login_result", None)
            if last_login_result is not None:
                return last_login_result

            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"timed out after {timeout:.1f}s waiting for Login response")
            await asyncio.sleep(min(0.1, remaining))


__all__ = ["LoginCredentials", "SessionError", "SessionService"]
