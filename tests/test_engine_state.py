"""M4 feature 1: order domain model and state machine."""

from __future__ import annotations

import pytest

from stock_broker_tw.engine.state import (
    ApCode,
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


def test_order_request_roundtrip_preserves_mock_mode() -> None:
    req = StockOrderRequest.from_dict(
        {
            "client_order_id": "MOCK-001",
            "action": "new",
            "account": "MOCK",
            "stk_code": "2330",
            "side": "B",
            "quantity": 10,
            "mock": True,
        }
    )

    assert req.mock is True
    assert req.to_dict()["mock"] is True
    assert StockOrderRequest.from_dict(req.to_dict()).mock is True


def test_order_request_normalizes_sdk_integer_fields() -> None:
    request = StockOrderRequest.from_dict(
        {
            "client_order_id": "C001",
            "account": "S98875005091",
            "stk_code": "2330",
            "ap_code": "0",
            "identify": "123",
        }
    )

    assert request.ap_code == 0
    assert isinstance(request.ap_code, int)
    assert request.identify == 123
    assert isinstance(request.identify, int)


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


def test_state_machine_allows_retry_after_failed_mock_execution() -> None:
    state = _make_state(status=OrderStatus.FAILED)
    machine = OrderStateMachine()

    machine.transition(state, OrderStatus.PENDING, reason="retry mock execution")

    assert state.status == OrderStatus.PENDING
    assert state.transitions[-1]["to"] == "PENDING"


def test_ap_code_has_semantic_names_and_sdk_values() -> None:
    assert ApCode.REGULAR.value == "REGULAR"
    assert ApCode.ODD_LOT.value == "ODD_LOT"
    assert ApCode.INTRADAY_ODD_LOT.value == "INTRADAY_ODD_LOT"
    assert ApCode.AFTER_HOURS.value == "AFTER_HOURS"
    assert ApCode.INTRADAY_ODD_LOT.to_sdk_value() == 4


def test_external_request_accepts_semantic_and_legacy_ap_code_values() -> None:
    for value, expected in (
        ("REGULAR", 0),
        ("ODD_LOT", 2),
        ("INTRADAY_ODD_LOT", 4),
        ("AFTER_HOURS", 7),
        (0, 0),
        ("4", 4),
    ):
        request = StockOrderRequest.from_external_dict(
            {
                "client_order_id": "APCODE001",
                "stk_code": "2330",
                "side": "B",
                "quantity": 1,
                "ap_code": value,
            }
        )
        assert request.ap_code.to_sdk_value() == expected


def test_external_request_rejects_unknown_ap_code() -> None:
    with pytest.raises(ValueError, match="ap_code"):
        StockOrderRequest.from_external_dict(
            {
                "client_order_id": "APCODE002",
                "stk_code": "2330",
                "side": "B",
                "quantity": 1,
                "ap_code": "UNKNOWN",
            }
        )
