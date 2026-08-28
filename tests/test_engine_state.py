"""M4 feature 1: order domain model and state machine."""

from __future__ import annotations

import pytest

from stock_broker_tw.engine.state import (
    InvalidOrderStateTransition,
    OrderSide,
    OrderStateMachine,
    OrderStatus,
    PriceFlag,
    StockOrderRequest,
    StockOrderState,
    TimeInForce,
)


def _make_state(status: OrderStatus = OrderStatus.PENDING) -> StockOrderState:
    return StockOrderState(
        client_order_id="C001",
        status=status,
        request=StockOrderRequest(
            client_order_id="C001",
            account="S98875005091",
            stk_code="2330",
            side=OrderSide.BUY,
            price=500.0,
            quantity=1000,
        ),
    )


def test_order_enums_and_request_roundtrip() -> None:
    assert OrderSide.BUY.value == "B"
    assert OrderSide.SELL.value == "S"
    assert TimeInForce.ROD.value == "ROD"
    assert PriceFlag.MARKET.value == "M"

    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "action": "new",
            "account": "S98875005091",
            "stk_code": "2330",
            "side": "B",
            "price": 123.0,
            "quantity": 100,
            "time_in_force": "ROD",
            "price_flag": "LIMIT",
        }
    )
    data = req.to_dict()
    assert data["client_order_id"] == "C001"
    assert data["stk_code"] == "2330"
    assert data["side"] == "B"


def test_state_roundtrip_to_dict() -> None:
    state = _make_state()
    data = state.to_dict()
    assert data["client_order_id"] == "C001"
    assert data["request"]["stk_code"] == "2330"
    restored = StockOrderState.from_dict(data)
    assert restored.client_order_id == "C001"
    assert restored.status == OrderStatus.PENDING


def test_state_machine_accepts_legal_path() -> None:
    state = _make_state()
    machine = OrderStateMachine()
    machine.transition(state, OrderStatus.SUBMITTED, reason="send")
    assert state.status == OrderStatus.SUBMITTED
    machine.transition(state, OrderStatus.ACCEPTED, reason="broker accepted")
    assert state.status == OrderStatus.ACCEPTED
    machine.transition(state, OrderStatus.PARTIALLY_FILLED, reason="report")
    assert state.status == OrderStatus.PARTIALLY_FILLED
    machine.transition(state, OrderStatus.FILLED, reason="filled")
    assert state.status == OrderStatus.FILLED
    assert len(state.transitions) == 4
    assert state.transitions[-1]["from"] == "PARTIALLY_FILLED"
    assert state.transitions[-1]["to"] == "FILLED"


def test_state_machine_allows_report_before_accept_response() -> None:
    state = _make_state(status=OrderStatus.SUBMITTED)
    machine = OrderStateMachine()
    machine.transition(state, OrderStatus.FILLED, reason="early report")
    assert state.status == OrderStatus.FILLED


def test_state_machine_rejects_illegal_transition() -> None:
    state = _make_state(status=OrderStatus.PENDING)
    machine = OrderStateMachine()
    with pytest.raises(InvalidOrderStateTransition):
        machine.transition(state, OrderStatus.FILLED, reason="not allowed")
