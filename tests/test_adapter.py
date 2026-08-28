"""Unit tests for YuantaAdapter state machine and event registration."""

from __future__ import annotations

from typing import ClassVar

import pytest

from stock_broker_tw.yuanta.adapter import YuantaAdapter, YuantaAdapterError
from stock_broker_tw.yuanta.events import YuantaEvent


class FakeTrader:
    def __init__(self) -> None:
        self.OnResponse = []
        self.open_count = 0
        self.close_count = 0
        self.dispose_count = 0
        self.logout_count = 0
        self.login_args: tuple | None = None
        self.log_type = None
        self.pmm_server_check = None
        self.mode = None

    def Open(self, mode) -> None:
        self.mode = mode
        self.open_count += 1

    def Close(self) -> None:
        self.close_count += 1

    def Dispose(self) -> None:
        self.dispose_count += 1

    def LogOut(self) -> bool:
        self.logout_count += 1
        return True

    def Login(self, *args) -> bool:
        self.login_args = args
        return True

    def SetLogType(self, log_type) -> None:
        self.log_type = log_type

    def SetPMMServerCheck(self, flag) -> None:
        self.pmm_server_check = flag


def make_adapter(**kwargs) -> tuple[YuantaAdapter, FakeTrader]:
    trader = FakeTrader()
    adapter = YuantaAdapter(trader=trader, **kwargs)
    return adapter, trader


def test_open_login_logout_close_lifecycle() -> None:
    adapter, trader = make_adapter()
    assert adapter.open() is None
    assert trader.open_count == 1
    assert adapter.opened is True

    assert adapter.login("S98875005091", "1234") is True
    assert trader.login_args == ("S98875005091", "1234")
    assert adapter.logged_in is True

    assert adapter.logout() is True
    assert trader.logout_count == 1
    assert adapter.logged_in is False

    adapter.close()
    assert trader.close_count == 1
    assert adapter.opened is False


def test_pfx_login_uses_four_argument_form() -> None:
    adapter, trader = make_adapter()
    adapter.open()
    adapter.login("S98875005091", "1234", pfx_path="/tmp/a.pfx", pfx_pass="yuanta")
    assert trader.login_args == ("/tmp/a.pfx", "yuanta", "S98875005091", "1234")


def test_login_before_open_raises() -> None:
    adapter, _ = make_adapter()
    with pytest.raises(YuantaAdapterError, match="open"):
        adapter.login("S98875005091", "1234")


def test_duplicate_login_raises() -> None:
    adapter, _ = make_adapter()
    adapter.open()
    adapter.login("S98875005091", "1234")
    with pytest.raises(YuantaAdapterError, match="already logged in|重複"):
        adapter.login("S98875005091", "1234")


def test_logout_before_open_raises() -> None:
    adapter, _ = make_adapter()
    with pytest.raises(YuantaAdapterError, match="open"):
        adapter.logout()


def test_logout_without_login_is_safe() -> None:
    adapter, trader = make_adapter()
    adapter.open()
    assert adapter.logout() is True
    assert trader.logout_count == 1


def test_close_is_idempotent() -> None:
    adapter, trader = make_adapter()
    adapter.close()
    adapter.close()
    assert trader.close_count == 1


def test_dispose_is_idempotent() -> None:
    adapter, trader = make_adapter()
    adapter.close()
    adapter.dispose()
    adapter.dispose()
    assert trader.dispose_count == 1


def test_on_response_writes_to_event_queue() -> None:
    adapter, trader = make_adapter()
    adapter.open()
    assert len(trader.OnResponse) == 1
    handler = trader.OnResponse[0]
    handler(1, 0, "Login", None, object())
    event = adapter.event_queue.get(timeout=0.1)
    assert isinstance(event, YuantaEvent)
    assert event.int_mark == 1
    assert event.dw_index == 0
    assert event.str_index == "Login"
    assert event.obj_handle is None
    assert event.obj_value is not None


class FakeStoreResult:
    StkStoreList: ClassVar[list] = []
    OVStkStoreList: ClassVar[list] = []


class FakeQueryTrader(FakeTrader):
    def __init__(self) -> None:
        super().__init__()
        self.query_calls: list[tuple[tuple, dict]] = []
        self.on_response = None

    def GetStoreSummary(self, Account=None, **kwargs):
        self.query_calls.append(((Account,), kwargs))
        if self.on_response is not None:
            self.on_response(1, 0, "GetStoreSummary", None, FakeStoreResult())
        return True


def test_query_calls_trader_and_waits_for_matching_response() -> None:
    trader = FakeQueryTrader()
    adapter = YuantaAdapter(trader=trader)
    trader.on_response = adapter._on_response
    adapter.open()
    result = adapter.query("GetStoreSummary", Account="S98875005091", timeout=1)
    assert result == {"stk_store_list": [], "ov_stk_store_list": []}
    assert trader.query_calls == [(("S98875005091",), {})]

    # A different response first must not be consumed by the query.
    trader2 = FakeQueryTrader()
    adapter2 = YuantaAdapter(trader=trader2)
    trader2.on_response = adapter2._on_response
    adapter2.open()
    adapter2._on_response(1, 0, "GetBankBalance", None, object())
    result2 = adapter2.query("GetStoreSummary", Account="A", timeout=1)
    assert result2 == {"stk_store_list": [], "ov_stk_store_list": []}
    # The unrelated event remains available to WebSocket consumers.
    event = adapter2.event_queue.get(timeout=0.1)
    assert event.str_index == "GetBankBalance"


class FakePositionalOnlyQueryTrader(FakeTrader):
    def __init__(self) -> None:
        super().__init__()
        self.args: tuple | None = None
        self.on_response = None

    def GetStoreSummary(self, Account):
        self.args = (Account,)
        if self.on_response is not None:
            self.on_response(1, 0, "GetStoreSummary", None, FakeStoreResult())
        return True


def test_query_retries_positionally_when_trader_rejects_keywords() -> None:
    trader = FakePositionalOnlyQueryTrader()
    adapter = YuantaAdapter(trader=trader)
    trader.on_response = adapter._on_response
    adapter.open()
    result = adapter.query("GetStoreSummary", Account="S98875005091", timeout=1)
    assert result == {"stk_store_list": [], "ov_stk_store_list": []}
    assert trader.args == ("S98875005091",)
