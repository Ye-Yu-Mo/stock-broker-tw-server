"""Unit tests for YuantaAdapter state machine and event registration."""

from __future__ import annotations

import sys
import threading
import time
import types
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
        self.login_result = True
        self.login_error: Exception | None = None

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
        if self.login_error is not None:
            raise self.login_error
        return self.login_result

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


def test_login_false_logs_result_without_credentials(caplog) -> None:
    adapter, trader = make_adapter(environment="PROD")
    trader.login_result = False
    adapter.open()

    with caplog.at_level("DEBUG", logger="stock_broker_tw.yuanta.adapter"):
        assert adapter.login(
            "S98875005091",
            "password-secret",
            pfx_path="/private/account.pfx",
            pfx_pass="pfx-secret",
        ) is False

    assert "accepted=False" in caplog.text
    assert "environment=PROD" in caplog.text
    assert "password-secret" not in caplog.text
    assert "pfx-secret" not in caplog.text


def test_login_exception_logs_type_without_credentials(caplog) -> None:
    adapter, trader = make_adapter()
    trader.login_error = RuntimeError("password-secret pfx-secret")
    adapter.open()

    with (
        caplog.at_level("DEBUG", logger="stock_broker_tw.yuanta.adapter"),
        pytest.raises(RuntimeError),
    ):
        adapter.login(
            "S98875005091",
            "password-secret",
            pfx_path="/private/account.pfx",
            pfx_pass="pfx-secret",
        )

    assert "Login() raised" in caplog.text
    assert "RuntimeError" in caplog.text
    assert "password-secret" not in caplog.text
    assert "pfx-secret" not in caplog.text


def test_login_response_logs_safe_status(caplog) -> None:
    adapter, trader = make_adapter()
    adapter.open()
    result = types.SimpleNamespace(
        LoginStatus=types.SimpleNamespace(MsgCode="9999", MsgContent="login failed", Count=0),
        LoginList=[],
    )

    with caplog.at_level("DEBUG", logger="stock_broker_tw.yuanta.adapter"):
        trader.OnResponse[0](1, 7, "Login", None, result)

    assert "Login response received" in caplog.text
    assert "msg_code=9999" in caplog.text
    assert "login_entries=0" in caplog.text
    assert "login failed" not in caplog.text


def test_login_response_parse_failure_is_logged(caplog, monkeypatch) -> None:
    adapter, trader = make_adapter()
    adapter.open()

    def fail_parse(_value):
        raise ValueError("bad login payload")

    monkeypatch.setattr("stock_broker_tw.yuanta.adapter.login_result_to_dict", fail_parse)
    with caplog.at_level("DEBUG", logger="stock_broker_tw.yuanta.adapter"):
        trader.OnResponse[0](1, 7, "Login", None, object())

    assert "failed to parse Login response" in caplog.text
    assert "ValueError" in caplog.text
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


class FakeQueryConcurrentTrader(FakeTrader):
    """Returns True from the query call without emitting a response.

    Tests control response arrival explicitly through ``adapter._on_response``
    so they can simulate out-of-order / concurrent callbacks.
    """

    def GetStoreSummary(self, Account=None, **kwargs):
        return True


def test_query_waits_only_for_its_own_request_id() -> None:
    trader = FakeQueryConcurrentTrader()
    adapter = YuantaAdapter(trader=trader)
    adapter.open()

    results: dict[str, object] = {}
    errors: list[BaseException] = []
    barrier = threading.Barrier(3)

    def run_query(request_id: str) -> None:
        barrier.wait()
        try:
            results[request_id] = adapter.query(
                "GetStoreSummary", request_id=request_id, timeout=2
            )
        except BaseException as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [
        threading.Thread(target=run_query, args=("A",)),
        threading.Thread(target=run_query, args=("B",)),
    ]
    for t in threads:
        t.start()
    barrier.wait()
    # Give both queries time to enter the condition wait before feeding responses.
    time.sleep(0.05)
    adapter._on_response(1, 0, "GetStoreSummary", None, {"request_id": "B", "data": "B"})
    adapter._on_response(1, 0, "GetStoreSummary", None, {"request_id": "A", "data": "A"})
    for t in threads:
        t.join(timeout=3)
    assert not errors
    assert results == {"A": {"request_id": "A", "data": "A"}, "B": {"request_id": "B", "data": "B"}}


def test_timeout_request_does_not_consume_other_request_response() -> None:
    trader = FakeQueryConcurrentTrader()
    adapter = YuantaAdapter(trader=trader)
    adapter.open()

    barrier = threading.Barrier(2)
    holder: dict[str, object] = {}
    errors: list[BaseException] = []

    def run_query() -> None:
        barrier.wait()
        try:
            holder["result"] = adapter.query(
                "GetStoreSummary", request_id="A", timeout=0.1
            )
        except BaseException as exc:
            errors.append(exc)

    t = threading.Thread(target=run_query)
    t.start()
    barrier.wait()
    time.sleep(0.02)
    adapter._on_response(1, 0, "GetStoreSummary", None, {"request_id": "B", "data": "B"})
    t.join(timeout=1)
    assert errors and isinstance(errors[0], TimeoutError)
    assert "result" not in holder

    result = adapter.query("GetStoreSummary", request_id="B", timeout=1)
    assert result == {"request_id": "B", "data": "B"}


class FakeSendOrderTrader(FakeTrader):
    def SendStockOrder(self, account, payload):
        return True


def test_send_stock_order_matches_by_request_id_identify() -> None:
    trader = FakeSendOrderTrader()
    adapter = YuantaAdapter(trader=trader)
    adapter.open()

    barrier = threading.Barrier(2)
    holder: dict[str, object] = {}
    errors: list[BaseException] = []

    def run_send() -> None:
        barrier.wait()
        try:
            holder["result"] = adapter.send_stock_order(
                "S98875005091",
                {"identify": "order-1", "stk_code": "2330"},
                request_id="order-1",
                timeout=2,
            )
        except BaseException as exc:  # pragma: no cover - failure path
            errors.append(exc)

    t = threading.Thread(target=run_send)
    t.start()
    barrier.wait()
    time.sleep(0.02)
    adapter._on_response(
        1,
        0,
        "SendStockOrder",
        None,
        {"result_list": [{"identify": "order-1", "reply_code": 0, "order_no": "H00001"}]},
    )
    t.join(timeout=3)
    assert not errors
    assert holder["result"]["result_list"][0]["order_no"] == "H00001"


def test_request_id_waiter_falls_back_to_unmatched_response() -> None:
    trader = FakeQueryConcurrentTrader()
    adapter = YuantaAdapter(trader=trader)
    adapter.open()

    barrier = threading.Barrier(2)
    holder: dict[str, object] = {}
    errors: list[BaseException] = []

    def run_query() -> None:
        barrier.wait()
        try:
            holder["result"] = adapter.query(
                "GetStoreSummary", request_id="A", timeout=1
            )
        except BaseException as exc:  # pragma: no cover - failure path
            errors.append(exc)

    t = threading.Thread(target=run_query)
    t.start()
    barrier.wait()
    time.sleep(0.02)
    # Real Yuanta query responses may not echo request_id; they should still be
    # consumable when QueryService serializes same-function queries.
    adapter._on_response(1, 0, "GetStoreSummary", None, {"stk_code": "2330"})
    t.join(timeout=2)
    assert not errors
    assert holder["result"] == {"stk_code": "2330"}


class FakeMarketType:
    def __str__(self) -> str:
        return "TWSE"


class FakeStkStore:
    MarketNo = FakeMarketType()


class FakeStoreResultWithHolding:
    StkStoreList: ClassVar[list[FakeStkStore]] = [FakeStkStore()]
    OVStkStoreList: ClassVar[list] = []


class FakeHoldingQueryTrader(FakeQueryTrader):
    def GetStoreSummary(self, Account=None, **kwargs):
        if self.on_response is not None:
            self.on_response(1, 0, "GetStoreSummary", None, FakeStoreResultWithHolding())
        return True


def test_query_serializes_store_summary_market_enum() -> None:
    trader = FakeHoldingQueryTrader()
    adapter = YuantaAdapter(trader=trader)
    trader.on_response = adapter._on_response
    adapter.open()

    result = adapter.query("GetStoreSummary", Account="S98875005091", timeout=1)

    assert result["stk_store_list"][0]["market_no"] == "TWSE"


class FakeRealizedGainLoss:
    Account = None
    MarketNo = None
    StkCode = None
    TradeDate = None
    TradeKind = None
    Price = None
    Qty = None
    ProfitLoss = None
    OrderNo = None
    TermSplit = None
    TermExt = None
    Charge = None
    Cost = None
    Tax = None
    TotalAMT = None


class FakeEnumMarketType:
    TWSE = "enum-twse"


def test_reversal_dict_is_converted_to_typed_object(monkeypatch) -> None:
    yuanta_module = types.ModuleType("YuantaOneAPI")
    yuanta_module.RealizedGainLoss = FakeRealizedGainLoss
    yuanta_module.enumMarketType = FakeEnumMarketType
    monkeypatch.setitem(sys.modules, "YuantaOneAPI", yuanta_module)

    result = YuantaAdapter._convert_query_object_params(
        "GetStkHistoryReportReversal",
        {
            "Account": "S98875005091",
            "ReGainLoss": {
                "account": "S98875005091",
                "market_no": "TWSE",
                "stk_code": "2330",
                "trade_date": "2026/08/01",
                "total_amt": 105000,
            },
        },
    )

    typed = result["ReGainLoss"]
    assert isinstance(typed, FakeRealizedGainLoss)
    assert typed.Account == "S98875005091"
    assert typed.MarketNo == "enum-twse"
    assert typed.StkCode == "2330"
    assert typed.TradeDate == "2026/08/01"
    assert typed.TotalAMT == 105000
