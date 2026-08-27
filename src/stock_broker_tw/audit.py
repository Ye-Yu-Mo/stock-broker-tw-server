"""Audit logging and structured log setup."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REDACTED = "[REDACTED]"


class AuditLogger:
    """Write JSON-lines audit records with password/secret redaction."""

    def __init__(self, enabled: bool = True, file_path: str | None = None) -> None:
        self.enabled = enabled
        self.file_path = file_path

    def record(
        self,
        action: str,
        result: str = "success",
        request_id: str | None = None,
        account: str | None = None,
        **details: Any,
    ) -> None:
        if not self.enabled:
            return
        entry = {
            "time": datetime.now(UTC).isoformat(),
            "action": action,
            "result": result,
            "request_id": request_id,
            "account": account,
            **self._redact(details),
        }
        line = json.dumps(entry, ensure_ascii=False, default=str)
        logger.info("audit %s", line)
        if self.file_path:
            path = Path(self.file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    @staticmethod
    def _redact(value: Any) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                key_lower = str(key).lower()
                if (
                    "password" in key_lower
                    or "passwd" in key_lower
                    or "pass" in key_lower
                    or "secret" in key_lower
                    or "token" in key_lower
                ):
                    redacted[key] = _REDACTED
                else:
                    redacted[key] = AuditLogger._redact(item)
            return redacted
        if isinstance(value, list):
            return [AuditLogger._redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(AuditLogger._redact(item) for item in value)
        return value


class JsonFormatter(logging.Formatter):
    """Minimal JSON-lines log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(settings: Any) -> None:
    """Configure root logging according to service settings."""
    level = getattr(settings.server, "log_level", "INFO").upper()
    log_json = getattr(settings.server, "log_json", True)

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    audit_file = getattr(settings.audit, "file", None)
    if audit_file:
        Path(audit_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(audit_file, encoding="utf-8"))

    formatter: logging.Formatter
    if log_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in handlers:
        handler.setFormatter(formatter)
        root.addHandler(handler)


__all__ = ["AuditLogger", "JsonFormatter", "setup_logging"]
