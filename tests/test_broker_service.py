"""M4 feature 3: broker service order actions and idempotency."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from stock_broker_tw.broker.service import BrokerService, BrokerServiceError
from stock_broker_tw.config import AccountConfig, RiskConfig, ServerConfig, Settings, StateConfig
from stock_broker_tw.engine.queue import SerialOrderQueue
from stock_broker_tw.engine.state import StockOrderRequest
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


def make_env(tmp_path: Path, adapter: FakeAdapter | None = None, risk: RiskConfig | None = None):
    adapter = adapter or FakeAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        risk=risk or RiskConfig(),
    )
    store = StateStore(settings.state.db_path)
    queue = SerialOrderQueue()
    service = BrokerService(adapter, settings, store=store, queue=queue)
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
