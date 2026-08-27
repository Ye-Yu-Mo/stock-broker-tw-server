"""Unit tests for the M1 CLI login verification flow."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from stock_broker_tw.cli import (
    build_login_config,
    execute_lifecycle,
    load_config,
    parse_args,
    wait_for_login_response,
)
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent
from stock_broker_tw.yuanta.serializer import login_result_to_dict


class FakeStatus:
    MsgCode = "0001"
    MsgContent = "成功"
    Count = 1


class FakeLoginData:
    Account = "S98875005091"
    Name = "測試用戶"
    InvestorID = "A123456789"
    SellerNo = "9527"


class FakeLoginResult:
    LoginStatus = FakeStatus()
    LoginList: ClassVar[list[FakeLoginData]] = [FakeLoginData()]


class FakeAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = False
        self.logged_in = False
        self.closed = False
        self.disposed = False
        self.login_args: tuple | None = None
        self.logout_called = False

    def open(self) -> None:
        self.opened = True

    def login(self, account: str, password: str, pfx_path=None, pfx_pass=None) -> bool:
        self.login_args = (account, password, pfx_path, pfx_pass)
        self.logged_in = True
        self.event_queue.put(
            YuantaEvent(1, 0, "Login", None, FakeLoginResult())
        )
        return True

    def logout(self) -> bool:
        self.logout_called = True
        self.logged_in = False
        return True

    def close(self) -> None:
        self.closed = True
        self.opened = False

    def dispose(self) -> None:
        self.disposed = True


def test_parse_args_defaults_and_aliases() -> None:
    args = parse_args(
        [
            "--account",
            "S98875005091",
            "--password",
            "1234",
            "--pfx-path",
            "/tmp/a.pfx",
            "--pfx-pass",
            "yuanta",
            "--timeout",
            "7",
        ]
    )
    assert args.account == "S98875005091"
    assert args.password == "1234"
    assert args.pfx_path == "/tmp/a.pfx"
    assert args.pfx_pass == "yuanta"
    assert args.timeout == 7


def test_load_config_reads_toml(tmp_path: Path) -> None:
    cfg = tmp_path / "test.toml"
    cfg.write_text(
        """
[yuanta]
environment = "PROD"
spark_api_dir = "/opt/yuanta"

[account]
account = "S98875005091"
password = "1234"
pfx_path = "/tmp/cert.pfx"
pfx_pass = "yuanta"
""",
        encoding="utf-8",
    )
    data = load_config(cfg)
    assert data["account"]["account"] == "S98875005091"
    assert data["yuanta"]["environment"] == "PROD"


def test_build_login_config_prefers_cli_over_file(tmp_path: Path) -> None:
    cfg = tmp_path / "test.toml"
    cfg.write_text(
        """
[account]
account = "file-account"
password = "file-pass"
""",
        encoding="utf-8",
    )
    class Args:
        config = str(cfg)
        account = "cli-account"
        password = "cli-pass"
        pfx_path = None
        pfx_pass = None
        environment = None
        spark_api_dir = None
        timeout = 5.0

    resolved = build_login_config(Args())  # type: ignore[arg-type]
    assert resolved["account"] == "cli-account"
    assert resolved["password"] == "cli-pass"
    assert resolved["environment"] == "UAT"


def test_wait_for_login_response_skips_other_events() -> None:
    eq = EventQueue()
    eq.put(YuantaEvent(1, 0, "GetBankBalance", None, object()))
    eq.put(YuantaEvent(1, 0, "Login", None, FakeLoginResult()))
    result = wait_for_login_response(eq, timeout=1)
    assert result == login_result_to_dict(FakeLoginResult())


def test_wait_for_login_response_timeout() -> None:
    eq = EventQueue()
    with pytest.raises(TimeoutError):
        wait_for_login_response(eq, timeout=0.02)


def test_execute_lifecycle_runs_login_and_cleanup() -> None:
    adapter = FakeAdapter()
    result = execute_lifecycle(
        adapter,
        account="S98875005091",
        password="1234",
        timeout=1,
    )
    assert result["login_list"][0]["account"] == "S98875005091"
    assert adapter.login_args == (
        "S98875005091",
        "1234",
        None,
        None,
    )
    assert adapter.logout_called is True
    assert adapter.closed is True
    assert adapter.disposed is True
