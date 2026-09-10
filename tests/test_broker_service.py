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
from stock_broker_tw.service.query import QueryError
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


class TimeoutAdapter(FakeAdapter):
    def send_stock_order(self, account: str, order: dict, timeout: float = 10.0):
        self.calls.append({"account": account, "order": order})
        raise TimeoutError("broker response timeout")


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


class FalseNotifier(RecordingNotifier):
    def send(self, event: str, title: str, fields: dict) -> bool:
        super().send(event, title, fields)
        return False


def make_env(
    tmp_path: Path,
    adapter: FakeAdapter | None = None,
    risk: RiskConfig | None = None,
    query_service: FakeQueryService | None = None,
    broadcaster=None,
    notifier=None,
    rate_limiter: RateLimiter | None = None,
    mock_quote_provider=None,
    with_query_service: bool = True,
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
        query_service=query_service if query_service is not None else (FakeQueryService() if with_query_service else None),
        broadcaster=broadcaster,
        notifier=notifier,
        rate_limiter=rate_limiter,
        mock_quote_provider=mock_quote_provider or query_service or OfflineQuoteProvider(),
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


def test_place_stock_order_normalizes_ap_code_to_int(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    request = StockOrderRequest.from_dict(
        {
            "client_order_id": "ODD-001",
            "account": "S98875005091",
            "stk_code": "00635U",
            "side": "S",
            "price": 46.25,
            "quantity": 3,
            "ap_code": "4",
        }
    )

    run(service.place_stock_order(request))

    ap_code = adapter.calls[-1]["order"]["ap_code"]
    assert ap_code == 4
    assert isinstance(ap_code, int)


def test_semantic_ap_code_maps_to_intraday_odd_lot(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)

    run(
        service.place_stock_order(
            {
                "client_order_id": "ODD-SEMANTIC",
                "account": "S98875005091",
                "stk_code": "00635U",
                "side": "S",
                "price": 46.0,
                "quantity": 1,
                "ap_code": "INTRADAY_ODD_LOT",
            }
        )
    )

    assert adapter.calls[-1]["order"]["ap_code"] == 4


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


def test_claim_conflict_with_different_parameters_is_not_reused(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path)
    first = StockOrderRequest.from_dict(
        {
            "client_order_id": "RACE001",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 500.0,
            "quantity": 10,
        }
    )
    store.claim_stock_order(
        first.client_order_id,
        first.to_dict(),
        account=first.account,
        action="new",
        mock=False,
        execution_id="first-execution",
    )
    second = StockOrderRequest.from_dict({**first.to_dict(), "price": 501.0})

    with pytest.raises(BrokerServiceError) as exc_info:
        service._claim_pending(second, execution_id="second-execution")

    assert exc_info.value.code == "IDEMPOTENCY_CONFLICT"
    assert adapter.calls == []


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
    assert call["order"]["identify"] == 1


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
    service.init_mock_account("MOCK-API", cash=100_000.0, positions=[])
    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-001",
                "account": "MOCK-API",
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
    service.init_mock_account("MOCK-API", cash=100_000.0, positions=[])
    request = {
        "client_order_id": "MOCK-002",
        "account": "MOCK-API",
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
    service.init_mock_account("MOCK-API", cash=100_000.0, positions=[])
    with pytest.raises(RiskError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-003",
                    "account": "MOCK-API",
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
                "price": 500.0,
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
                    "account": "MOCK-MISSING",
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
        "message": "ORDER_QTY_EXCEEDED: 2 > 1",
        "reason": "ORDER_QTY_EXCEEDED: 2 > 1",
    }
    assert adapter.calls == []


def test_failed_risk_notification_can_retry(tmp_path: Path) -> None:
    notifier = FalseNotifier()
    service, _adapter, _store, _ = make_env(
        tmp_path,
        risk=RiskConfig(max_order_qty=1),
        notifier=notifier,
    )
    request = {
        "client_order_id": "RISK-RETRY",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 500.0,
        "quantity": 2,
    }

    for _ in range(2):
        with pytest.raises(RiskError):
            run(service.place_stock_order(request))

    assert len(notifier.calls) == 2


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
    assert notifier.calls[0][2]["message"] == notifier.calls[0][2]["reason"]
    assert "RATE_LIMITED" in notifier.calls[0][2]["message"]
    assert adapter.calls == []


def test_real_cancel_cannot_target_mock_order(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    service.init_mock_account("MOCK-TARGET", cash=10_000.0, positions=[])
    mock_order = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-TARGET-001",
                "account": "MOCK-TARGET",
                "stk_code": "2330",
                "side": "B",
                "quantity": 1,
                "mock": True,
            }
        )
    )

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.cancel_stock_order(
                {
                    "client_order_id": "REAL-CANCEL-001",
                    "account": "S98875005091",
                    "order_no": mock_order["order_no"],
                    "stk_code": "2330",
                    "side": "B",
                }
            )
        )

    assert exc_info.value.code == "MOCK_ORDER_MODE_MISMATCH"
    assert adapter.calls == []


def test_mock_operation_cannot_target_another_mock_account(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    service.init_mock_account("MOCK-A", cash=10_000.0, positions=[])
    service.init_mock_account("MOCK-B", cash=10_000.0, positions=[])
    mock_order = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-A-001",
                "account": "MOCK-A",
                "stk_code": "2330",
                "side": "B",
                "quantity": 1,
                "mock": True,
            }
        )
    )

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.cancel_stock_order(
                {
                    "client_order_id": "MOCK-B-CANCEL",
                    "account": "MOCK-B",
                    "order_no": mock_order["order_no"],
                    "stk_code": "2330",
                    "side": "B",
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "MOCK_ACCOUNT_MISMATCH"
    assert adapter.calls == []


class OfflineQuoteProvider:
    async def snapshot(self, stk_code: str, market_type: str = "TWSE"):
        return {
            "query_watch_list": [
                {"stk_code": stk_code, "buy_price": 99.0, "sell_price": 101.0}
            ]
        }


def _mock_order(service, client_order_id: str = "MOCK-BASE") -> dict:
    service.init_mock_account("MOCK-BASE", cash=10_000.0, positions=[])
    return run(
        service.place_stock_order(
            {
                "client_order_id": client_order_id,
                "account": "MOCK-BASE",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "mock": True,
            }
        )
    )


def test_mock_cancel_never_calls_real_adapter(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    order = _mock_order(service, "MOCK-CANCEL-TARGET")

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.submit_stock_order(
                {
                    "client_order_id": "MOCK-CANCEL-OP",
                    "action": "cancel",
                    "account": "MOCK-BASE",
                    "order_no": order["order_no"],
                    "stk_code": "2330",
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "MOCK_ORDER_FINAL"
    assert adapter.calls == []


def test_mock_replace_never_calls_real_adapter(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    order = _mock_order(service, "MOCK-REPLACE-TARGET")

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.submit_stock_order(
                {
                    "client_order_id": "MOCK-REPLACE-OP",
                    "action": "replace",
                    "account": "MOCK-BASE",
                    "order_no": order["order_no"],
                    "stk_code": "2330",
                    "new_price": 102.0,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "MOCK_ORDER_FINAL"
    assert adapter.calls == []


def test_mock_order_persists_mode_and_trade(tmp_path: Path) -> None:
    service, _adapter, store, _ = make_env(tmp_path)
    order = _mock_order(service, "MOCK-PERSISTED")

    row = store.get_stock_order("MOCK-PERSISTED")
    assert row["request"]["mock"] is True
    assert row["data"]["mock"] is True
    assert len(store.get_trades(order_no=order["order_no"])) == 1


def test_mock_uses_injected_provider_without_query_service(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(
        tmp_path,
        with_query_service=False,
        mock_quote_provider=OfflineQuoteProvider(),
    )
    service.init_mock_account("MOCK-OFFLINE", cash=10_000.0, positions=[])

    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-OFFLINE-001",
                "account": "MOCK-OFFLINE",
                "stk_code": "2330",
                "side": "B",
                "price_flag": "M",
                "quantity": 10,
                "mock": True,
            }
        )
    )

    assert result["status"] == "FILLED"
    assert store.get_mock_account("MOCK-OFFLINE")["cash"] == 8_990.0
    assert adapter.calls == []


def test_mock_risk_uses_actual_fill_price(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(
        tmp_path,
        risk=RiskConfig(max_order_amount=1_000.0),
    )
    service.init_mock_account("MOCK-RISK", cash=10_000.0, positions=[])

    with pytest.raises(RiskError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-RISK-001",
                    "account": "MOCK-RISK",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 20,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "ORDER_AMOUNT_EXCEEDED"
    assert store.get_mock_account("MOCK-RISK")["cash"] == 10_000.0
    assert adapter.calls == []


def test_mock_limit_price_must_be_marketable(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path)
    service.init_mock_account("MOCK-LIMIT", cash=10_000.0, positions=[])

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-LIMIT-001",
                    "account": "MOCK-LIMIT",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 100.0,
                    "quantity": 10,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "MOCK_LIMIT_NOT_MARKETABLE"
    assert store.get_mock_account("MOCK-LIMIT")["cash"] == 10_000.0
    assert adapter.calls == []


def test_mock_high_limit_uses_actual_price_for_amount_risk(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(
        tmp_path,
        risk=RiskConfig(max_order_amount=100_000.0),
    )
    service.init_mock_account("MOCK-ACTUAL-RISK", cash=100_000.0, positions=[])

    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-ACTUAL-RISK-001",
                "account": "MOCK-ACTUAL-RISK",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 900,
                "mock": True,
            }
        )
    )

    assert result["status"] == "FILLED"
    assert result["data"]["fill_price"] == 101.0
    assert store.get_mock_account("MOCK-ACTUAL-RISK")["cash"] == 9_100.0
    assert adapter.calls == []


def test_mock_risk_uses_actual_price_for_deviation(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(
        tmp_path,
        risk=RiskConfig(reference_price=90.0, max_price_deviation_pct=1.0),
    )
    service.init_mock_account("MOCK-DEVIATION", cash=10_000.0, positions=[])

    with pytest.raises(RiskError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-DEVIATION-001",
                    "account": "MOCK-DEVIATION",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 1,
                    "mock": True,
                }
            )
        )

    assert exc_info.value.code == "PRICE_DEVIATION"
    assert store.get_mock_account("MOCK-DEVIATION")["cash"] == 10_000.0
    assert adapter.calls == []


class QueryErrorQuoteProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls = 0

    async def snapshot(self, stk_code: str, market_type: str = "TWSE"):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return {
            "query_watch_list": [
                {"stk_code": stk_code, "buy_price": 99.0, "sell_price": 101.0}
            ]
        }


class BlockingQuoteProvider(QueryErrorQuoteProvider):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def snapshot(self, stk_code: str, market_type: str = "TWSE"):
        self.calls += 1
        self.started.set()
        await self.release.wait()
        return {
            "query_watch_list": [
                {"stk_code": stk_code, "buy_price": 99.0, "sell_price": 101.0}
            ]
        }


def test_mock_concurrent_same_client_id_claims_once(tmp_path: Path) -> None:
    provider = BlockingQuoteProvider()
    service, adapter, store, _ = make_env(tmp_path, mock_quote_provider=provider)
    service.init_mock_account("MOCK-CONCURRENT", cash=10_000.0, positions=[])
    request = {
        "client_order_id": "MOCK-CONCURRENT-001",
        "account": "MOCK-CONCURRENT",
        "stk_code": "2330",
        "side": "B",
        "quantity": 10,
        "mock": True,
    }

    async def gather_orders():
        first_task = asyncio.create_task(service.place_stock_order(request))
        await provider.started.wait()
        second_task = asyncio.create_task(service.place_stock_order(request))
        await asyncio.sleep(0)
        provider.release.set()
        return await asyncio.gather(first_task, second_task)

    first, second = run(gather_orders())

    assert provider.calls == 1
    assert {first["status"], second["status"]} == {"PENDING", "FILLED"}
    assert len(store.get_trades()) == 1
    assert store.get_mock_account("MOCK-CONCURRENT")["cash"] == 8_990.0
    assert adapter.calls == []


def test_mock_query_error_preserves_error_contract(tmp_path: Path) -> None:
    from stock_broker_tw.service.query import QueryError

    provider = QueryErrorQuoteProvider(
        QueryError(
            "quote rate limited",
            code="RATE_LIMITED",
            status_code=429,
            detail={"function": "GetWatchListAll", "retry_after": 1},
        )
    )
    service, adapter, store, _ = make_env(tmp_path, mock_quote_provider=provider)
    service.init_mock_account("MOCK-QUERY-ERROR", cash=10_000.0, positions=[])

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-QUERY-ERROR-001",
                    "account": "MOCK-QUERY-ERROR",
                    "stk_code": "2330",
                    "side": "B",
                    "quantity": 1,
                    "mock": True,
                }
            )
        )

    error = exc_info.value
    assert (error.code, error.status_code, error.detail) == (
        "RATE_LIMITED",
        429,
        {"function": "GetWatchListAll", "retry_after": 1},
    )
    assert provider.calls == 1
    assert store.get_stock_order("MOCK-QUERY-ERROR-001")["status"] == "FAILED"
    assert adapter.calls == []


def test_mock_query_failure_can_be_retried_once(tmp_path: Path) -> None:
    provider = QueryErrorQuoteProvider(
        QueryError("temporary timeout", code="QUERY_TIMEOUT", status_code=504, detail={"retry": True})
    )
    service, adapter, store, _ = make_env(tmp_path, mock_quote_provider=provider)
    service.init_mock_account("MOCK-RETRY", cash=10_000.0, positions=[])
    request = {
        "client_order_id": "MOCK-RETRY-001",
        "account": "MOCK-RETRY",
        "stk_code": "2330",
        "side": "B",
        "quantity": 10,
        "mock": True,
    }

    with pytest.raises(BrokerServiceError) as first_error:
        run(service.place_stock_order(request))
    assert first_error.value.code == "QUERY_TIMEOUT"
    assert store.get_stock_order("MOCK-RETRY-001")["status"] == "FAILED"

    provider.error = None
    result = run(service.place_stock_order(request))

    assert result["status"] == "FILLED"
    assert provider.calls == 2
    assert len(store.get_trades(order_no=result["order_no"])) == 1
    assert store.get_mock_account("MOCK-RETRY")["cash"] == 8_990.0
    assert adapter.calls == []


def test_same_client_id_different_mock_accounts_is_conflict(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path)
    service.init_mock_account("MOCK-ACCOUNT-A", cash=10_000.0, positions=[])
    service.init_mock_account("MOCK-ACCOUNT-B", cash=10_000.0, positions=[])
    first = {
        "client_order_id": "MOCK-SHARED-ID",
        "account": "MOCK-ACCOUNT-A",
        "stk_code": "2330",
        "side": "B",
        "quantity": 1,
        "mock": True,
    }
    run(service.place_stock_order(first))

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {**first, "account": "MOCK-ACCOUNT-B"}
            )
        )

    assert exc_info.value.code == "IDEMPOTENCY_CONFLICT"
    assert store.get_mock_account("MOCK-ACCOUNT-B")["cash"] == 10_000.0
    assert adapter.calls == []


def test_mock_account_requires_mock_namespace(tmp_path: Path) -> None:
    service, _adapter, _store, _ = make_env(tmp_path)

    with pytest.raises(BrokerServiceError) as exc_info:
        service.init_mock_account("S98875005091", cash=10_000.0, positions=[])

    assert exc_info.value.code == "INVALID_MOCK_ACCOUNT"


def test_real_order_rejects_mock_namespace_even_without_initialized_account(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "REAL-MOCK-NAMESPACE",
                    "account": "MOCK-UNINITIALIZED",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 100.0,
                    "quantity": 1,
                    "mock": False,
                }
            )
        )

    assert exc_info.value.code == "MOCK_ACCOUNT_REQUIRES_MOCK"
    assert adapter.calls == []


def test_deactivate_mock_account_preserves_history_and_blocks_new_orders(tmp_path: Path) -> None:
    service, _adapter, store, _ = make_env(tmp_path)
    service.init_mock_account("MOCK-LIFECYCLE", cash=10_000.0, positions=[])

    assert store.deactivate_mock_account("MOCK-LIFECYCLE") is True
    account = store.get_mock_account("MOCK-LIFECYCLE")
    assert account["active"] is False

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "MOCK-INACTIVE-001",
                    "account": "MOCK-LIFECYCLE",
                    "stk_code": "2330",
                    "side": "B",
                    "quantity": 1,
                    "mock": True,
                }
            )
        )
    assert exc_info.value.code == "MOCK_ACCOUNT_INACTIVE"


def test_mock_account_rejects_non_finite_cash_and_position_price(tmp_path: Path) -> None:
    service, _adapter, store, _ = make_env(tmp_path)

    for cash in (float("inf"), float("nan")):
        with pytest.raises(BrokerServiceError) as exc_info:
            service.init_mock_account("MOCK-NONFINITE", cash=cash, positions=[])
        assert exc_info.value.code == "INVALID_MOCK_ACCOUNT"

    with pytest.raises(BrokerServiceError) as exc_info:
        service.init_mock_account(
            "MOCK-NONFINITE",
            cash=10_000.0,
            positions=[{"stk_code": "2330", "quantity": 1, "avg_price": float("inf")}],
        )
    assert exc_info.value.code == "INVALID_MOCK_POSITION"
    assert store.get_mock_account("MOCK-NONFINITE") is None


def test_basket_no_is_bounded_without_changing_client_id(tmp_path: Path) -> None:
    service, adapter, store, _ = make_env(tmp_path)
    client_order_id = "client-order-with-more-than-thirty-two-characters-001"

    result = run(
        service.place_stock_order(
            {
                "client_order_id": client_order_id,
                "account": "S98875005091",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 1,
            }
        )
    )

    basket_no = adapter.calls[0]["order"]["basket_no"]
    assert result["client_order_id"] == client_order_id
    assert len(basket_no) <= 32
    assert basket_no.isascii() and basket_no.isalnum()
    assert store.get_stock_order(client_order_id) is not None


def test_new_order_without_trade_date_uses_today(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)

    run(
        service.place_stock_order(
            {
                "client_order_id": "TODAY001",
                "account": "S98875005091",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 1,
            }
        )
    )

    assert adapter.calls[0]["order"]["trade_date"] == datetime.now(UTC).strftime("%Y/%m/%d")


@pytest.mark.parametrize(
    ("field", "value"),
    (("side", "X"), ("price_flag", "INVALID"), ("time_in_force", "INVALID"), ("ap_code", 1)),
)
def test_invalid_order_fields_are_rejected_before_adapter(
    tmp_path: Path, field: str, value: object
) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    request = {
        "client_order_id": "INVALID001",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 500.0,
        "quantity": 1,
    }
    request[field] = value

    with pytest.raises(BrokerServiceError) as exc_info:
        run(service.place_stock_order(request))

    assert exc_info.value.code == "INVALID_ORDER_FIELD"
    assert adapter.calls == []


def test_replace_non_positive_quantity_is_rejected_before_adapter(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.replace_stock_order(
                {
                    "client_order_id": "REPLACE001",
                    "account": "S98875005091",
                    "order_no": "H00001",
                    "stk_code": "2330",
                    "side": "B",
                    "new_quantity": 0,
                }
            )
        )

    assert exc_info.value.code == "INVALID_ORDER_FIELD"
    assert adapter.calls == []


def test_mock_retry_with_changed_request_is_conflict(tmp_path: Path) -> None:
    provider = QueryErrorQuoteProvider(
        QueryError("temporary", code="QUERY_TIMEOUT", status_code=504)
    )
    service, adapter, store, _ = make_env(tmp_path, mock_quote_provider=provider)
    service.init_mock_account("MOCK-FINGERPRINT", cash=10_000.0, positions=[])
    request = {
        "client_order_id": "MOCK-FINGERPRINT-001",
        "account": "MOCK-FINGERPRINT",
        "stk_code": "2330",
        "side": "B",
        "quantity": 1,
        "mock": True,
    }

    with pytest.raises(BrokerServiceError):
        run(service.place_stock_order(request))

    with pytest.raises(BrokerServiceError) as exc_info:
        run(service.place_stock_order({**request, "stk_code": "2885"}))

    assert exc_info.value.code == "IDEMPOTENCY_CONFLICT"
    assert store.get_mock_account("MOCK-FINGERPRINT")["cash"] == 10_000.0
    assert adapter.calls == []


def test_update_status_preserves_full_transition_history(tmp_path: Path) -> None:
    service, _adapter, store, _ = make_env(tmp_path)

    run(
        service.place_stock_order(
            {
                "client_order_id": "HISTORY001",
                "account": "S98875005091",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 1,
            }
        )
    )

    transitions = store.get_stock_order("HISTORY001")["data"]["transitions"]
    assert [item["to"] for item in transitions] == ["SUBMITTED", "ACCEPTED"]


def test_mock_order_is_not_blocked_by_real_circuit_breaker(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)
    service.init_mock_account("MOCK-CIRCUIT", cash=10_000.0, positions=[])
    service.circuit_breaker.failure_threshold = 1
    service.circuit_breaker.record_failure("real broker outage")

    result = run(
        service.place_stock_order(
            {
                "client_order_id": "MOCK-CIRCUIT-001",
                "account": "MOCK-CIRCUIT",
                "stk_code": "2330",
                "side": "B",
                "quantity": 1,
                "mock": True,
            }
        )
    )

    assert result["status"] == "FILLED"
    assert adapter.calls == []


def test_real_order_rejects_non_default_account(tmp_path: Path) -> None:
    service, adapter, _store, _ = make_env(tmp_path)

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "OTHER001",
                    "account": "S00000000000",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 1,
                }
            )
        )

    assert exc_info.value.code == "ACCOUNT_NOT_ALLOWED"
    assert adapter.calls == []


def test_real_timeout_is_manual_review_not_failed(tmp_path: Path) -> None:
    adapter = TimeoutAdapter()
    service, _adapter, store, _ = make_env(tmp_path, adapter=adapter)

    with pytest.raises(BrokerServiceError) as exc_info:
        run(
            service.place_stock_order(
                {
                    "client_order_id": "TIMEOUT001",
                    "account": "S98875005091",
                    "stk_code": "2330",
                    "side": "B",
                    "price": 500.0,
                    "quantity": 1,
                }
            )
        )

    row = store.get_stock_order("TIMEOUT001")
    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "ORDER_SUBMIT_FAILED"
    assert exc_info.value.detail == {"execution_uncertain": True, "retryable": False}
    assert row["status"] == "NEED_MANUAL_REVIEW"
    assert row["data"]["execution_uncertain"] is True
    assert row["data"]["retryable"] is False


def test_uncertain_real_order_is_not_automatically_retried(tmp_path: Path) -> None:
    adapter = TimeoutAdapter()
    service, _adapter, store, _ = make_env(tmp_path, adapter=adapter)
    request = {
        "client_order_id": "TIMEOUT002",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 500.0,
        "quantity": 1,
    }

    with pytest.raises(BrokerServiceError):
        run(service.place_stock_order(request))
    second = run(service.place_stock_order(request))

    assert len(adapter.calls) == 1
    assert second["status"] == "NEED_MANUAL_REVIEW"
    assert store.get_stock_order("TIMEOUT002")["status"] == "NEED_MANUAL_REVIEW"
