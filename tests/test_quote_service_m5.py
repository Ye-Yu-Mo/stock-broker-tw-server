"""M5 quote subscription model and service tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from stock_broker_tw.broker.quote import QuoteType, SubscribeRequest
from stock_broker_tw.config import AccountConfig, QuoteConfig, Settings, StateConfig
from stock_broker_tw.risk.rate_limit import RateLimiter
from stock_broker_tw.service.quote import QuoteService, QuoteServiceError
from stock_broker_tw.state.store import StateStore


class FakeAdapter:
    def __init__(self) -> None:
        self.subscribe_calls: list[tuple[str, str, list]] = []
        self.unsubscribe_calls: list[tuple[str, str, list]] = []

    def subscribe(self, function_name: str, account: str, symbols: list):
        self.subscribe_calls.append((function_name, account, symbols))
        return True

    def unsubscribe(self, function_name: str, account: str, symbols: list):
        self.unsubscribe_calls.append((function_name, account, symbols))
        return True


def make_service(
    tmp_path: Path,
    adapter: FakeAdapter | None = None,
    quote_config: QuoteConfig | None = None,
    rate_limiter: RateLimiter | None = None,
) -> tuple[QuoteService, FakeAdapter]:
    adapter = adapter or FakeAdapter()
    settings = Settings(
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
        quote=quote_config or QuoteConfig(),
    )
    store = StateStore(settings.state.db_path)
    service = QuoteService(
        adapter,
        settings,
        store=store,
        rate_limiter=rate_limiter,
    )
    return service, adapter


def run(coro):
    return asyncio.run(coro)


def test_quote_type_mapping() -> None:
    assert QuoteType.WATCHLIST.subscribe_function == "SubscribeWatchlist"
    assert QuoteType.WATCHLIST.unsubscribe_function == "UnSubscribeWatchlist"
    assert QuoteType.WATCHLIST_ALL.subscribe_function == "SubscribeWatchlistAll"
    assert QuoteType.WATCHLIST_ALL.unsubscribe_function == "UnSubscribeWatchlistAll"
    assert QuoteType.FIVE_TICK.subscribe_function == "SubscribeFiveTickA"
    assert QuoteType.FIVE_TICK.unsubscribe_function == "UnSubscribeFiveTickA"
    assert QuoteType.STOCK_TICK.subscribe_function == "SubscribeStockTick"
    assert QuoteType.STOCK_TICK.unsubscribe_function == "UnSubscribeStockTick"
    assert QuoteType.MARKET_INFO.subscribe_function == "SubscribeMarketInformation"
    assert QuoteType.MARKET_INFO.unsubscribe_function == "UnSubscribeMarketInformation"
    assert QuoteType.STOCK_INFO.subscribe_function == "SubscribeStockInformation"
    assert QuoteType.STOCK_INFO.unsubscribe_function == "UnSubscribeStockInformation"


def test_subscribe_request_from_dict() -> None:
    req = SubscribeRequest.from_dict(
        {"type": "five_tick", "symbols": ["2330", " 2885 "], "account": "S1"}
    )
    assert req.type is QuoteType.FIVE_TICK
    assert req.symbols == ["2330", "2885"]
    assert req.account == "S1"
    assert req.market_type == "TWSE"


def test_subscribe_returns_list_and_saves(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path)
    result = run(service.subscribe({"type": "five_tick", "symbols": ["2330"]}))
    assert adapter.subscribe_calls == [
        ("SubscribeFiveTickA", "S98875005091", [{"market_type": "TWSE", "stk_code": "2330"}])
    ]
    assert result == [
        {"account": "S98875005091", "type": "five_tick", "symbol": "2330", "market_type": "TWSE"}
    ]


def test_duplicate_subscribe_does_not_call_adapter_twice(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path)
    run(service.subscribe({"type": "five_tick", "symbols": ["2330"]}))
    run(service.subscribe({"type": "five_tick", "symbols": ["2330", "2885"]}))
    assert len(adapter.subscribe_calls) == 2
    assert adapter.subscribe_calls[1] == (
        "SubscribeFiveTickA",
        "S98875005091",
        [{"market_type": "TWSE", "stk_code": "2885"}],
    )
    assert len(service.list_subscribed()) == 2


def test_unsubscribe_removes_and_calls_adapter(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path)
    run(service.subscribe({"type": "five_tick", "symbols": ["2330", "2885"]}))
    result = run(service.unsubscribe({"type": "five_tick", "symbols": ["2330"]}))
    assert adapter.unsubscribe_calls == [
        ("UnSubscribeFiveTickA", "S98875005091", [{"market_type": "TWSE", "stk_code": "2330"}])
    ]
    assert result == [
        {"account": "S98875005091", "type": "five_tick", "symbol": "2885", "market_type": "TWSE"}
    ]


def test_unsubscribe_missing_is_noop(tmp_path: Path) -> None:
    service, adapter = make_service(tmp_path)
    result = run(service.unsubscribe({"type": "five_tick", "symbols": ["9999"]}))
    assert result == []
    assert adapter.unsubscribe_calls == []


def test_max_per_request_limit(tmp_path: Path) -> None:
    service, _ = make_service(
        tmp_path,
        quote_config=QuoteConfig(max_per_request=2),
    )
    with pytest.raises(QuoteServiceError) as exc:
        run(service.subscribe({"type": "five_tick", "symbols": ["1", "2", "3"]}))
    assert exc.value.status_code == 400
    assert exc.value.code == "MAX_PER_REQUEST_EXCEEDED"


def test_max_total_limit(tmp_path: Path) -> None:
    service, _ = make_service(
        tmp_path,
        quote_config=QuoteConfig(max_per_request=200, max_total_subscriptions=2),
    )
    run(service.subscribe({"type": "five_tick", "symbols": ["2330", "2885"]}))
    with pytest.raises(QuoteServiceError) as exc:
        run(service.subscribe({"type": "five_tick", "symbols": ["2317"]}))
    assert exc.value.status_code == 400
    assert exc.value.code == "MAX_TOTAL_EXCEEDED"


def test_rate_limited(tmp_path: Path) -> None:
    limiter = RateLimiter(max_per_second=0, max_per_minute=None)
    service, _ = make_service(tmp_path, rate_limiter=limiter)
    with pytest.raises(QuoteServiceError) as exc:
        run(service.subscribe({"type": "five_tick", "symbols": ["2330"]}))
    assert exc.value.status_code == 429
    assert exc.value.code == "RATE_LIMITED"


def test_invalid_type_raises(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    with pytest.raises(QuoteServiceError):
        run(service.subscribe({"type": "bad", "symbols": ["2330"]}))
