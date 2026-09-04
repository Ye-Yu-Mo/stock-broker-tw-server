"""Tests for the session service layer (login/logout/status)."""

from __future__ import annotations

import asyncio
from typing import ClassVar

import pytest

from stock_broker_tw.config import AccountConfig, Settings, YuantaConfig
from stock_broker_tw.service.session import LoginCredentials, SessionError, SessionService
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


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


class FakeFailureResult:
    LoginStatus = FakeStatus.__new__(FakeStatus)
    LoginList: ClassVar[list] = []


FakeFailureResult.LoginStatus.MsgCode = "9999"
FakeFailureResult.LoginStatus.MsgContent = "密碼錯誤"
FakeFailureResult.LoginStatus.Count = 0


class FakeAdapter:
    def __init__(self, success: bool = True, reject: bool = False) -> None:
        self.event_queue = EventQueue()
        self.opened = False
        self.logged_in = False
        self.disposed = False
        self.last_login_result = None
        self.login_args: tuple | None = None
        self.logout_called = False
        self.success = success
        self.reject = reject

    def open(self) -> None:
        self.opened = True

    def reset_login_result(self) -> None:
        self.last_login_result = None

    def login(self, account: str, password: str, pfx_path=None, pfx_pass=None) -> bool:
        self.login_args = (account, password, pfx_path, pfx_pass)
        if self.reject:
            return False
        self.logged_in = True
        if self.success:
            from stock_broker_tw.yuanta.serializer import login_result_to_dict

            self.last_login_result = login_result_to_dict(FakeLoginResult())
            self.event_queue.put(YuantaEvent(1, 0, "Login", None, FakeLoginResult()))
        else:
            from stock_broker_tw.yuanta.serializer import login_result_to_dict

            self.last_login_result = login_result_to_dict(FakeFailureResult())
            self.logged_in = False
            self.event_queue.put(YuantaEvent(1, 0, "Login", None, FakeFailureResult()))
        return True

    def logout(self) -> bool:
        self.logout_called = True
        self.logged_in = False
        return True
class AcceptedNoResponseAdapter(FakeAdapter):
    def login(self, account: str, password: str, pfx_path=None, pfx_pass=None) -> bool:
        self.login_args = (account, password, pfx_path, pfx_pass)
        return True


def make_service(adapter: FakeAdapter | None = None) -> tuple[SessionService, FakeAdapter]:
    adapter = adapter or FakeAdapter()
    settings = Settings(
        yuanta=YuantaConfig(login_timeout=0.5),
        account=AccountConfig(account="S98875005091", password="1234"),
    )
    return SessionService(adapter, settings), adapter


def run(coro):
    return asyncio.run(coro)


def test_login_success_uses_config_account_and_returns_login_result() -> None:
    service, adapter = make_service()
    result = run(service.login(LoginCredentials()))
    assert result["login_list"][0]["account"] == "S98875005091"
    assert adapter.login_args == (
        "S98875005091",
        "1234",
        None,
        None,
    )
    assert adapter.logged_in is True


def test_login_accepts_explicit_credentials() -> None:
    service, adapter = make_service()
    result = run(
        service.login(
            LoginCredentials(account="S111", password="p", pfx_path="/tmp/a.pfx", pfx_pass="x")
        )
    )
    assert result["login_list"][0]["account"] == "S98875005091"
    assert adapter.login_args == ("S111", "p", "/tmp/a.pfx", "x")


def test_login_rejected_raises_session_error(caplog) -> None:
    service, _ = make_service(FakeAdapter(reject=True))
    with (
        caplog.at_level("DEBUG", logger="stock_broker_tw.service.session"),
        pytest.raises(SessionError) as exc_info,
    ):
        run(service.login(LoginCredentials(account="A", password="P")))
    assert exc_info.value.code == "LOGIN_REJECTED"
    assert "accepted=False" in caplog.text


def test_login_failure_result_raises_session_error() -> None:
    service, _ = make_service(FakeAdapter(success=False))
    with pytest.raises(SessionError) as exc_info:
        run(service.login(LoginCredentials(account="A", password="P")))
    assert "密碼錯誤" in str(exc_info.value)


def test_login_accepted_without_response_logs_wait_and_times_out(caplog) -> None:
    service, _ = make_service(AcceptedNoResponseAdapter())
    with (
        caplog.at_level("DEBUG", logger="stock_broker_tw.service.session"),
        pytest.raises(SessionError) as exc_info,
    ):
        run(service.login(LoginCredentials(account="A", password="P")))
    assert exc_info.value.code == "LOGIN_TIMEOUT"
    assert "accepted=True" in caplog.text
    assert "Login response" in caplog.text


def test_logout_marks_not_logged_in() -> None:
    service, adapter = make_service()
    adapter.open()
    adapter.logged_in = True
    adapter.last_login_result = {"login_list": [{"account": "S"}]}
    run(service.logout())
    assert adapter.logged_in is False
    assert adapter.logout_called is True
    assert adapter.last_login_result is None


def test_status_reflects_lifecycle() -> None:
    service, adapter = make_service()
    adapter.open()
    adapter.logged_in = True
    status = service.status()
    assert status["opened"] is True
    assert status["logged_in"] is True
    assert "event_queue_size" in status


def test_wait_for_login_result_does_not_consume_other_events() -> None:
    async def scenario() -> None:
        service, adapter = make_service()
        adapter.event_queue.put(YuantaEvent(2, 0, "SubscribeStockTick", None, {}))

        async def publish_login() -> None:
            await asyncio.sleep(0.02)
            adapter.last_login_result = {"login_list": [{"account": "S"}]}

        publisher = asyncio.create_task(publish_login())
        result = await service._wait_for_login_result(adapter, timeout=0.5)
        await publisher

        assert result["login_list"][0]["account"] == "S"
        assert adapter.event_queue.get_nowait().str_index == "SubscribeStockTick"

    run(scenario())


def test_login_runs_success_callback() -> None:
    async def scenario() -> None:
        calls: list[str] = []

        async def on_login_success() -> None:
            calls.append("recovery")

        service, _ = make_service()
        service.on_login_success = on_login_success
        result = await service.login(LoginCredentials())

        assert result["login_list"]
        assert calls == ["recovery"]

    run(scenario())
