"""M6 unified rate limiter tests."""

from __future__ import annotations

from stock_broker_tw.risk.rate_limit import RateLimiter


def test_rate_limiter_counts_function_and_account_dimension() -> None:
    limiter = RateLimiter(max_per_second=2, max_per_minute=None)
    assert limiter.acquire("SendStockOrder", key="A") is True
    assert limiter.acquire("SendStockOrder", key="A") is True
    assert limiter.acquire("SendStockOrder", key="B") is True
    assert limiter.acquire("SendStockOrder", key="B") is True
    assert limiter.acquire("SendStockOrder", key="A") is False
    assert limiter.acquire("SendStockOrder", key="B") is False


def test_trade_rate_limit_ten_per_second() -> None:
    limiter = RateLimiter(max_per_second=10, max_per_minute=None)
    for _ in range(10):
        assert limiter.acquire("SendStockOrder", key="A") is True
    assert limiter.acquire("SendStockOrder", key="A") is False
