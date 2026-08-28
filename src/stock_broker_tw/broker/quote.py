"""M5 quote subscription domain model.

This module centralises the public quote type names and the mapping to Yuanta
``Subscribe*`` / ``UnSubscribe*`` function names so API and broker layers share
one source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QuoteType(str, Enum):
    """Client-facing quote subscription type."""

    WATCHLIST = "watchlist"
    WATCHLIST_ALL = "watchlist_all"
    FIVE_TICK = "five_tick"
    STOCK_TICK = "stock_tick"
    MARKET_INFO = "market_info"
    STOCK_INFO = "stock_info"

    @property
    def subscribe_function(self) -> str:
        return _SUBSCRIPTION_MAP[self]["subscribe"]

    @property
    def unsubscribe_function(self) -> str:
        return _SUBSCRIPTION_MAP[self]["unsubscribe"]

    @classmethod
    def from_value(cls, value: Any) -> QuoteType:
        if isinstance(value, QuoteType):
            return value
        try:
            return cls(str(value).lower())
        except ValueError as exc:
            valid = ", ".join(member.value for member in cls)
            raise ValueError(f"invalid quote type: {value!r} (expected one of: {valid})") from exc


_SUBSCRIPTION_MAP: dict[QuoteType, dict[str, str]] = {
    QuoteType.WATCHLIST: {
        "subscribe": "SubscribeWatchlist",
        "unsubscribe": "UnSubscribeWatchlist",
    },
    QuoteType.WATCHLIST_ALL: {
        "subscribe": "SubscribeWatchlistAll",
        "unsubscribe": "UnSubscribeWatchlistAll",
    },
    QuoteType.FIVE_TICK: {
        "subscribe": "SubscribeFiveTickA",
        "unsubscribe": "UnSubscribeFiveTickA",
    },
    QuoteType.STOCK_TICK: {
        "subscribe": "SubscribeStockTick",
        "unsubscribe": "UnSubscribeStockTick",
    },
    QuoteType.MARKET_INFO: {
        "subscribe": "SubscribeMarketInformation",
        "unsubscribe": "UnSubscribeMarketInformation",
    },
    QuoteType.STOCK_INFO: {
        "subscribe": "SubscribeStockInformation",
        "unsubscribe": "UnSubscribeStockInformation",
    },
}


@dataclass(frozen=True)
class SubscribedQuote:
    """A single locally subscribed quote item."""

    account: str
    type: QuoteType
    symbol: str
    market_type: str = "TWSE"

    @property
    def quote_type(self) -> QuoteType:
        return self.type

    def to_dict(self) -> dict[str, Any]:
        return {
            "account": self.account,
            "type": self.type.value,
            "symbol": self.symbol,
            "market_type": self.market_type,
        }


@dataclass
class SubscribeRequest:
    """Normalised quote subscribe/unsubscribe request."""

    type: QuoteType
    symbols: list[str] = field(default_factory=list)
    account: str | None = None
    market_type: str = "TWSE"
    index_flag: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | SubscribeRequest) -> SubscribeRequest:
        if isinstance(data, SubscribeRequest):
            return data
        raw_type = data.get("type")
        quote_type = QuoteType.from_value(raw_type)
        symbols = list(
            dict.fromkeys(str(s).strip() for s in data.get("symbols", []) if str(s).strip())
        )
        return cls(
            type=quote_type,
            symbols=symbols,
            account=data.get("account"),
            market_type=(data.get("market_type") or "TWSE").upper(),
            index_flag=data.get("index_flag"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "symbols": self.symbols,
            "account": self.account,
            "market_type": self.market_type,
            "index_flag": self.index_flag,
        }


__all__ = ["QuoteType", "SubscribeRequest", "SubscribedQuote"]
