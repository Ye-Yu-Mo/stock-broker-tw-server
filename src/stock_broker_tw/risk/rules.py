"""M4 basic trading risk rules.

The risk engine is intentionally synchronous and side-effect free.  Broker
service calls :meth:`RiskEngine.check` before an order enters the serial queue,
so a rejected request never reaches the Yuanta adapter.
"""

from __future__ import annotations

from typing import Any

from stock_broker_tw.config import Settings
from stock_broker_tw.engine.state import OrderAction, StockOrderRequest


class RiskError(Exception):
    """Raised when a request violates a risk rule."""

    def __init__(
        self,
        message: str,
        code: str = "RISK_REJECTED",
        status_code: int = 400,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}


class RiskEngine:
    """Evaluate configured rules against a :class:`StockOrderRequest`."""

    def __init__(self, settings: Settings | Any) -> None:
        self.settings = settings

    @property
    def config(self) -> Any:
        if hasattr(self.settings, "risk"):
            return self.settings.risk
        # Accept a bare RiskConfig object as well as a full Settings object.
        return self.settings if hasattr(self.settings, "panic") else None

    def validate(self, request: StockOrderRequest | dict[str, Any]) -> list[str]:
        """Return a list of violation messages (empty when the request is OK)."""
        req = StockOrderRequest.from_dict(request) if not isinstance(request, StockOrderRequest) else request
        failures: list[str] = []

        if self.config is None:
            return failures

        if self.config.panic:
            failures.append("MARKET_PANIC: trading is stopped by panic switch")

        if self.config.blacklist and req.stk_code in self.config.blacklist:
            failures.append(f"BLACKLISTED_STOCK: {req.stk_code} is blacklisted")

        action = req.action.value if isinstance(req.action, OrderAction) else str(req.action)
        if action in {OrderAction.NEW.value, OrderAction.REPLACE.value}:
            if action == OrderAction.NEW.value and req.quantity <= 0:
                failures.append("ORDER_QTY_INVALID: quantity must be positive")
            if req.quantity > 0 and req.quantity > self.config.max_order_qty:
                failures.append(f"ORDER_QTY_EXCEEDED: {req.quantity} > {self.config.max_order_qty}")

            price = req.price or 0
            amount = price * req.quantity
            if amount > self.config.max_order_amount:
                failures.append(
                    f"ORDER_AMOUNT_EXCEEDED: {amount} > {self.config.max_order_amount}"
                )

            reference = self.config.reference_price
            max_dev = self.config.max_price_deviation_pct
            if reference and price:
                deviation = abs(price - reference) / reference * 100.0
                if deviation > max_dev:
                    failures.append(
                        f"PRICE_DEVIATION: {deviation:.2f}% > {max_dev}%"
                    )

        return failures

    def check(self, request: StockOrderRequest | dict[str, Any]) -> None:
        """Raise :class:`RiskError` on the first violation."""
        failures = self.validate(request)
        if failures:
            first = failures[0]
            code = first.split(":")[0]
            raise RiskError(
                message=first,
                code=code,
                status_code=400,
                detail={"violations": failures},
            )

    def evaluate(self, request: StockOrderRequest | dict[str, Any]) -> list[str]:
        """Alias for :meth:`validate`."""
        return self.validate(request)


__all__ = ["RiskEngine", "RiskError"]
