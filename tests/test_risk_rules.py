"""M4 feature 5: basic risk rules."""

from __future__ import annotations

import pytest

from stock_broker_tw.config import RiskConfig, Settings
from stock_broker_tw.engine.state import StockOrderRequest
from stock_broker_tw.risk.rules import RiskEngine, RiskError


def _request(**overrides) -> StockOrderRequest:
    data = {
        "client_order_id": "C001",
        "account": "S98875005091",
        "stk_code": "2330",
        "side": "B",
        "price": 100.0,
        "quantity": 100,
        "action": "new",
    }
    data.update(overrides)
    return StockOrderRequest.from_dict(data)


def _settings(**risk_kwargs) -> Settings:
    return Settings(risk=RiskConfig(**risk_kwargs))


def test_panic_rejects_all_orders() -> None:
    engine = RiskEngine(_settings(panic=True))
    with pytest.raises(RiskError) as exc_info:
        engine.check(_request())
    assert exc_info.value.code == "MARKET_PANIC"


def test_blacklist_rejects_stock() -> None:
    engine = RiskEngine(_settings(blacklist=["2330"]))
    with pytest.raises(RiskError) as exc_info:
        engine.check(_request(stk_code="2330"))
    assert exc_info.value.code == "BLACKLISTED_STOCK"


def test_quantity_limit() -> None:
    engine = RiskEngine(_settings(max_order_qty=100))
    with pytest.raises(RiskError) as exc_info:
        engine.check(_request(quantity=101))
    assert exc_info.value.code == "ORDER_QTY_EXCEEDED"


def test_amount_limit() -> None:
    engine = RiskEngine(_settings(max_order_amount=10_000))
    with pytest.raises(RiskError) as exc_info:
        engine.check(_request(price=200, quantity=100))
    assert exc_info.value.code == "ORDER_AMOUNT_EXCEEDED"


def test_price_deviation() -> None:
    engine = RiskEngine(_settings(reference_price=100.0, max_price_deviation_pct=10.0))
    with pytest.raises(RiskError) as exc_info:
        engine.check(_request(price=150.0))
    assert exc_info.value.code == "PRICE_DEVIATION"


def test_valid_order_passes() -> None:
    engine = RiskEngine(_settings(reference_price=100.0, max_price_deviation_pct=10.0))
    engine.check(_request(price=105.0, quantity=10))
    assert True


def test_cancel_action_skips_qty_price_checks() -> None:
    engine = RiskEngine(_settings(max_order_qty=1))
    engine.check(_request(action="cancel", quantity=0, price=None))
    assert True
