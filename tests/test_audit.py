"""Tests for structured audit logging and secret redaction."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from stock_broker_tw.audit import AuditLogger, setup_logging


def test_audit_redacts_password_and_writes_json_lines(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.jsonl"
    logger = AuditLogger(enabled=True, file_path=str(audit_file))
    logger.record(
        "session.login",
        result="success",
        request_id="req-123",
        account="S98875005091",
        password="supersecret",
        nested={"password": "another-secret", "keep": "visible"},
    )

    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["action"] == "session.login"
    assert entry["result"] == "success"
    assert entry["request_id"] == "req-123"
    assert entry["account"] == "S98875005091"
    assert entry["password"] == "[REDACTED]"
    assert entry["nested"]["password"] == "[REDACTED]"
    assert entry["nested"]["keep"] == "visible"
    assert "supersecret" not in audit_file.read_text(encoding="utf-8")
    assert "another-secret" not in audit_file.read_text(encoding="utf-8")


def test_audit_preserves_event_action_with_extra_order_action(tmp_path: Path) -> None:
    audit_file = tmp_path / "compat.jsonl"
    logger = AuditLogger(enabled=True, file_path=str(audit_file))

    logger.record("order.rate_limited", account="A", order_action="place")

    entry = json.loads(audit_file.read_text(encoding="utf-8").strip())
    assert entry["action"] == "order.rate_limited"
    assert entry["order_action"] == "place"


def test_audit_disabled_does_not_write(tmp_path: Path) -> None:
    audit_file = tmp_path / "disabled.jsonl"
    logger = AuditLogger(enabled=False, file_path=str(audit_file))
    logger.record("session.logout", result="success", request_id="r2")
    assert not audit_file.exists()


def test_setup_logging_does_not_double_write_audit_file(tmp_path: Path) -> None:
    audit_file = tmp_path / "single.jsonl"
    settings = SimpleNamespace(
        server=SimpleNamespace(log_level="INFO", log_json=True),
        audit=SimpleNamespace(file=str(audit_file)),
    )
    setup_logging(settings)

    AuditLogger(enabled=True, file_path=str(audit_file)).record("test.event")

    assert len(audit_file.read_text(encoding="utf-8").strip().splitlines()) == 1
