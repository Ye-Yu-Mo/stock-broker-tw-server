"""Tests for structured audit logging and secret redaction."""

from __future__ import annotations

import json
from pathlib import Path

from stock_broker_tw.audit import AuditLogger


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


def test_audit_disabled_does_not_write(tmp_path: Path) -> None:
    audit_file = tmp_path / "disabled.jsonl"
    logger = AuditLogger(enabled=False, file_path=str(audit_file))
    logger.record("session.logout", result="success", request_id="r2")
    assert not audit_file.exists()
