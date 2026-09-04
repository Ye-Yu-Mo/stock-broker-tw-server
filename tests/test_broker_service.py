"""M4 feature 3: broker service order actions and idempotency."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from stock_broker_tw.broker.service import BrokerService, BrokerServiceError
from stock_broker_tw.config import AccountConfig, RiskConfig, ServerConfig, Settings, StateConfig
from stock_broker_tw.engine.queue import SerialOrderQueue
from stock_broker_tw.engine.state import StockOrderRequest
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.risk.rules import RiskError
from stock_broker_tw.state.store import StateStore


class FakeAdapter:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.responses: dict[str, dict] = {}
        self.fail_send = False

    def send_stock_order(self, account: str, order: dict, timeout: float = 10.0):
        self.calls.append({"account": account, "order": order})
        if self.fail_send:
            raise RuntimeError("adapter rejected")
        return self.responses.pop(
            order["basket_no"],
            {
                "result_count": {"msg_code": "0001", "msg_content": "ok", "count": 1},
                "result_list": [
                    {
                        "identify": order.get("identify", 1),
                        "reply_code": 0,
                        "order_no": "H00001",
                        "trade_date": "2026/08/28",
                        "err_type": "",
                        "err_no": "",
                        "advisory": "",
                    }
                ],
            },
        )


class FakeQueryService:
    def __init__(self, bid1: float = 99.0, ask1: float = 101.0) -> None:
        self.bid1 = bid1
        self.ask1 = ask1
        self.calls: list[dict] = []

    async def watchlist_snapshot(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "query_watch_list": [
                {
                    "stk_code": kwargs["stk_code"],
                    "buy_price": self.bid1,
                    "sell_price": self.ask1,
                }
            ]
        }


class FakeBroadcaster:
    def __init__(self) -> None:
        self.updates: list[dict] = []

    async def broadcast_order_update(self, state: dict) -> None:
        self.updates.append(state)


class RecordingNotifier:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str, dict]] = []

    def send(self, event: str, title: str, fields: dict) -> bool:
        self.calls.append((event, title, fields))
        if self.fail:
            raise RuntimeError("notification unavailable")
        return True


def make_env(
    tmp_path: Path,
    adapter: FakeAdapter | None = None,
    risk: RiskConfig | None = None,
    query_service: FakeQueryService | None = None,
    broadcaster=None,
    notifier=None,
    rate_limiter: RateLimiter | None = None,
):
    adapter = adapter or FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        risk=risk or RiskConfig(),
    )
    store = StateStore(settings.state.db_path)
    queue = SerialOrderQueue()
    service = BrokerService(
        adapter,
        settings,
        store=store,
        queue=queue,
        query_service=query_service or FakeQueryService(),
        broadcaster=broadcaster,
        notifier=notifier,
        rate_limiter=rate_limiter,
    )
    return service, adapter, store, settings


def run(coro):
    return asyncio.run(coro)


def test_place_stock_order_calls_send_and_persists_order_no(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path)
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 10,
        }
    )
    result = run(service.place_stock_order(req))
    assert result["status"] == "ACCEPTED"
    assert result["order_no"] == "H00001"
    assert len(adapter.calls) == 1
    call = adapter.calls[0]
    assert call["order"]["basket_no"] == "C001"
    assert call["order"]["trade_kind"] == 0
    assert call["order"]["stk_code"] == "2330"
    assert call["order"]["buy_sell"] == "B"
    assert store.get_stock_order("C001")["order_no"] == "H00001"


def test_duplicate_client_order_id_is_idempotent(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 10,
        }
    )
    run(service.place_stock_order(req))
    run(service.place_stock_order(req))
    assert len(adapter.calls) == 1


def test_same_client_order_id_with_different_action_is_conflict(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 10,
        }
    )
    run(service.place_stock_order(req))
    cancel_req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "action": "cancel",
            "account": "S98875005091",
            "order_no": "H00001",
            "stk_code": "2330",
        }
    )
    with pytest.raises(BrokerServiceError) as exc_info:
        run(service.cancel_stock_order(cancel_req))
    assert exc_info.value.code == "IDEMPOTENCY_CONFLICT"
    assert len(adapter.calls) == 1


def test_risk_rejected_order_never_calls_adapter(tmp_path: Path) -> None:
    risk = RiskConfig(max_order_qty=1)
    service, adapter, _store, _ = make_env(tmp_path, risk=risk)
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 100,
        }
    )
    with pytest.raises(RiskError):
        run(service.place_stock_order(req))
    assert adapter.calls == []


def test_cancel_stock_order_uses_trade_kind_04_and_order_no(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    # First place an order so local order_no mapping exists.
    run(
        service.place_stock_order(
            StockOrderRequest.from_dict(
                {
                    "client_order_id": "C001",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 10,
                }
            )
        )
    )
    cancel_req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C002",
            "action": "cancel",
            "account": "S98875005091",
            "order_no": "H00001",
            "trade_date": "2026/08/28",
            "stk_code": "2330",
            "side": "B",
            "quantity": 10,
        }
    )
    result = run(service.cancel_stock_order(cancel_req))
    assert result["status"] in {"SUBMITTED", "ACCEPTED"}
    cancel_call = adapter.calls[-1]
    assert cancel_call["order"]["trade_kind"] == 4
    assert cancel_call["order"]["order_no"] == "H00001"
    assert cancel_call["order"]["basket_no"] == "C002"


def test_replace_stock_order_uses_trade_kind_for_qty_or_price(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    run(
        service.place_stock_order(
            StockOrderRequest.from_dict(
                {
                    "client_order_id": "C001",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 10,
                }
            )
        )
    )
    replace_req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C003",
            "action": "replace",
            "account": "S98875005091",
            "order_no": "H00001",
            "trade_date": "2026/08/28",
            "stk_code": "2330",
            "side": "B",
            "price": 510.0,
            "quantity": 20,
        }
    )
    result = run(service.replace_stock_order(replace_req))
    assert result["status"] in {"SUBMITTED", "ACCEPTED"}
    replace_call = adapter.calls[-1]
    assert replace_call["order"]["trade_kind"] in {3, 7}
    assert replace_call["order"]["order_no"] == "H00001"


def test_cancel_missing_order_no_raises(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    cancel_req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C002",
            "action": "cancel",
            "account": "S98875005091",
            "stk_code": "2330",
            "quantity": 10,
        }
    )
    with pytest.raises(BrokerServiceError) as exc_info:
        run(service.cancel_stock_order(cancel_req))
    assert exc_info.value.code == "ORDER_NOT_FOUND"
    assert adapter.calls == []


def test_trade_kind_constants_match_yuanta_docs(tmp_path: Path) -> None:
    service, _adapter, _store, _ = make_env(tmp_path)
    cancel = StockOrderRequest.from_dict(
        {
            "client_order_id": "C_CANCEL",
            "action": "cancel",
            "account": "S98875005091",
            "order_no": "H00001",
            "stk_code": "2330",
        }
    )
    assert service._trade_kind(cancel) == 4

    replace_qty = StockOrderRequest.from_dict(
        {
            "client_order_id": "C_QTY",
            "action": "replace",
            "account": "S98875005091",
            "order_no": "H00001",
            "stk_code": "2330",
            "quantity": 20,
            "price": None,
        }
    )
    assert service._trade_kind(replace_qty) == 3

    replace_price = StockOrderRequest.from_dict(
        {
            "client_order_id": "C_PRICE",
            "action": "replace",
            "account": "S98875005091",
            "order_no": "H00001",
            "stk_code": "2330",
            "price": 510.0,
        }
    )
    assert service._trade_kind(replace_price) == 7


def test_send_passes_request_id_as_identify(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C_REQ",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 10,
        }
    )
    run(service.place_stock_order(req, request_id="REQ-123"))
    call = adapter.calls[-1]
    assert call["order"]["identify"] == "REQ-123"


class RequestIdFakeAdapter(FakeAdapter):
    def send_stock_order(self, account: str, order: dict, timeout: float = 10.0, request_id: str | None = None):
        self.calls.append({"account": account, "order": order, "request_id": request_id})
        return {
            "result_count": {"msg_code": "0001", "msg_content": "ok", "count": 1},
            "result_list": [
                {
                    "identify": order.get("identify", 1),
                    "reply_code": 0,
                    "order_no": "H00001",
                    "trade_date": "2026/08/28",
                    "err_type": "",
                    "err_no": "",
                    "advisory": "",
                }
            ],
        }


def test_send_forwards_request_id_to_adapter(tmp_path: Path) -> None:
    adapter = RequestIdFakeAdapter()
    service, _adapter, _store, _ = make_env(tmp_path, adapter)
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C_REQ2",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 10,
        }
    )
    run(service.place_stock_order(req, request_id="REQ-456"))
    assert adapter.calls[-1]["request_id"] == "REQ-456"


def test_mock_place_stock_order_fills_without_adapter(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path)
    service.init_mock_account("S98875005091", cash=100_000.0, positions=[])
    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-001",
                "account": "S98875005091",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "mock": True,
            }
        )
    )

    assert result["status"] == "FILLED"
    assert result["order_no"].startswith("MOCK-")
    assert result["avg_price"] == 101.0
    assert result["filled_qty"] == 10
    assert adapter.calls == []
    assert store.get_stock_order("MOCK-001")["status"] == "FILLED"


def test_mock_place_stock_order_is_idempotent(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    service.init_mock_account("S98875005091", cash=100_000.0, positions=[])
    request = {
        "client_order_id": "MOCK-002",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 500.0,
        "quantity": 10,
        "mock": True,
    }

    first = run(service.place_stock_order(request))
    second = run(service.place_stock_order(request))

    assert second == first
    assert adapter.calls == []


def test_mock_place_stock_order_still_runs_risk_checks(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path, risk=RiskConfig(max_order_qty=1))
    service.init_mock_account("S98875005091", cash=100_000.0, positions=[])
    with pytest.raises(RiskError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-003",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 10,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "ORDER_QTY_EXCEEDED"
    assert adapter.calls == []
    assert store.get_stock_order("MOCK-003") is None


def test_mock_account_initialization_persists_cash_and_positions(tmp_path: Path) -> None:
    service, _adapter, store, _ = make_env(tmp_path)

    result = service.init_mock_account(
        "MOCK-BUY",
        cash=10_000.0,
        positions=[{"stk_code": "2330", "quantity": 12, "avg_price": 90.0}],
    )

    assert result == store.get_mock_account("MOCK-BUY")
    assert result["cash"] == 10_000.0
    assert result["positions"]["2330"]["quantity"] == 12
    assert result["positions"]["2330"]["avg_price"] == 90.0


def test_mock_buy_fills_at_ask1_and_updates_account_and_ws(tmp_path: Path) -> None:
    quote_service = FakeQueryService(bid1=99.0, ask1=101.0)
    broadcaster = FakeBroadcaster()
    service, adapter, store, _ = make_env(
        tmp_path,
        query_service=quote_service,
        broadcaster=broadcaster,
    )
    service.init_mock_account("MOCK-BUY", cash=10_000.0, positions=[])
    before = datetime.now(UTC)

    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-BUY-001",
                "account": "MOCK-BUY",
                "stk_code": "2330",
                "side": "B",
                "price": 1.0,
                "quantity": 10,
                "mock": True,
            }
        )
    )

    after = datetime.now(UTC)
    row = store.get_stock_order("MOCK-BUY-001")
    timestamp = datetime.fromisoformat(row["data"]["timestamp"])
    UUID(result["order_no"][len("MOCK-"):])
    assert result["status"] == "FILLED"
    assert result["order_no"].startswith("MOCK-")
    assert result["avg_price"] == 101.0
    assert result["filled_qty"] == 10
    assert row["data"]["ask1"] == 101.0
    assert row["data"]["bid1"] == 99.0
    assert before <= timestamp <= after
    assert adapter.calls == []
    assert store.get_mock_account("MOCK-BUY")["cash"] == 8_990.0
    assert store.get_mock_account("MOCK-BUY")["positions"]["2330"]["quantity"] == 10
    assert row["data"]["mock"] is True
    assert [update["status"] for update in broadcaster.updates[-2:]] == ["ACCEPTED", "FILLED"]


def test_mock_sell_fills_at_bid1_and_reduces_position(tmp_path: Path) -> None:
    quote_service = FakeQueryService(bid1=99.0, ask1=101.0)
    service, adapter, store, _ = make_env(tmp_path, query_service=quote_service)
    service.init_mock_account(
        "MOCK-SELL",
        cash=0.0,
        positions=[{"stk_code": "2330", "quantity": 10, "avg_price": 90.0}],
    )

    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-SELL-001",
                "account": "MOCK-SELL",
                "stk_code": "2330",
                "side": "S",
                "price": 1.0,
                "quantity": 4,
                "mock": True,
            }
        )
    )

    assert result["status"] == "FILLED"
    assert result["avg_price"] == 99.0
    assert result["data"]["fill_price"] == 99.0
    assert result["data"]["bid1"] == 99.0
    assert adapter.calls == []
    account = store.get_mock_account("MOCK-SELL")
    assert account["cash"] == 396.0
    assert account["positions"]["2330"]["quantity"] == 6


def test_mock_order_requires_initialized_mock_account(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path, query_service=FakeQueryService())

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-MISSING-001",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "quantity": 1,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "MOCK_ACCOUNT_NOT_FOUND"
    assert adapter.calls == []
    assert store.get_stock_order("MOCK-MISSING-001") is None


def test_mock_buy_rejects_insufficient_cash_without_mutating_account(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(
        tmp_path,
        query_service=FakeQueryService(bid1=99.0, ask1=101.0),
    )
    service.init_mock_account("MOCK-CASH", cash=100.0, positions=[])

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-CASH-001",
                    "account": "MOCK-CASH",
                    "stk_code": "2330",
                    "side": "B",
                    "quantity": 2,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "INSUFFICIENT_CASH"
    assert store.get_stock_order("MOCK-CASH-001")["status"] == "REJECTED"
    assert store.get_mock_account("MOCK-CASH")["cash"] == 100.0
    assert adapter.calls == []


def test_risk_rejection_notifies_with_full_context_and_deduplicates(tmp_path: Path) -> None:
    notifier = RecordingNotifier()
    service, adapter, _store, _ = make_env(
        tmp_path,
        risk=RiskConfig(max_order_qty=1, max_order_amount=100.0),
        notifier=notifier,
    )
    request = {
        "client_order_id": "RISK-001",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 100.0,
        "quantity": 2,
    }

    for _ in range(2):
        with pytest.raises(RiskError):
            run(service.place_stock_order(request))

    assert len(notifier.calls) == 1
    event, _title, fields = notifier.calls[0]
    assert event == "risk.rejected"
    assert fields == {
        "client_order_id": "RISK-001",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 100.0,
        "quantity": 2,
        "action": "place",
        "code": "ORDER_QTY_EXCEEDED",
        "reason": "ORDER_QTY_EXCEEDED: 2 > 1",
    }
    assert adapter.calls == []


def test_changed_risk_reason_sends_new_alert(tmp_path: Path) -> None:
    notifier = RecordingNotifier()
    service, _adapter, _store, _ = make_env(
        tmp_path,
        risk=RiskConfig(max_order_qty=1, max_order_amount=100.0),
        notifier=notifier,
    )
    first = {
        "client_order_id": "RISK-002",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "S",
        "price": 100.0,
        "quantity": 2,
    }
    second = {**first, "quantity": 1, "price": 200.0}

    for request in (first, second):
        with pytest.raises(RiskError):
            run(service.place_stock_order(request))

    assert [call[2]["code"] for call in notifier.calls] == [
        "ORDER_QTY_EXCEEDED",
        "ORDER_AMOUNT_EXCEEDED",
    ]


def test_notification_failure_preserves_risk_rejection(tmp_path: Path) -> None:
    notifier = RecordingNotifier(fail=True)
    service, adapter, _store, _ = make_env(
        tmp_path,
        risk=RiskConfig(max_order_qty=1),
        notifier=notifier,
    )

    with pytest.raises(RiskError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "RISK-003",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 2,
                }
            )
        )

    assert exc_info.value.code == "ORDER_QTY_EXCEEDED"
    assert adapter.calls == []


def test_rate_limit_rejection_notifies_with_context(tmp_path: Path) -> None:
    notifier = RecordingNotifier()
    service, adapter, _store, _ = make_env(
        tmp_path,
        notifier=notifier,
        rate_limiter=RateLimiter(max_per_second=0, max_per_minute=None),
    )

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "RISK-004",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 1,
                }
            )
        )

    assert exc_info.value.code == "RATE_LIMITED"
    assert notifier.calls[0][0] == "risk.rejected"
    assert notifier.calls[0][2]["account"] == "S98875005091"
    assert adapter.calls == []
