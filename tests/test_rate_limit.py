"""Tests for the per-FunctionID query rate limiter."""

from __future__ import annotations

from stock_broker_tw.risk.rate_limit import RateLimiter


def test_allows_up_to_second_limit() -> None:
    limiter = RateLimiter(max_per_second=2, max_per_minute=600)
    assert limiter.acquire("GetStoreSummary") is True
    assert limiter.acquire("GetStoreSummary") is True
    assert limiter.acquire("GetStoreSummary") is False


def test_allows_different_functions_independently() -> None:
    limiter = RateLimiter(max_per_second=1, max_per_minute=600)
    assert limiter.acquire("GetStoreSummary") is True
    assert limiter.acquire("GetBankBalance") is True
    assert limiter.acquire("GetStoreSummary") is False


def test_minute_limit_is_enforced() -> None:
    limiter = RateLimiter(max_per_second=100, max_per_minute=3)
    assert limiter.acquire("GetBankBalance") is True
    assert limiter.acquire("GetBankBalance") is True
    assert limiter.acquire("GetBankBalance") is True
    assert limiter.acquire("GetBankBalance") is False


def test_none_limits_are_allowed() -> None:
    limiter = RateLimiter(max_per_second=1, max_per_minute=None)
    assert limiter.acquire("GetBankBalance") is True
    assert limiter.acquire("GetBankBalance") is False
