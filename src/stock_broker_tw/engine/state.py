"""M4 order domain models and state machine.

This module is the single source of truth for order-related enums, request
dataclasses, persisted order state, and legal lifecycle transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class OrderAction(str, Enum):
    NEW = "new"
    CANCEL = "cancel"
    REPLACE = "replace"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    NEED_MANUAL_REVIEW = "NEED_MANUAL_REVIEW"


class OrderSide(str, Enum):
    BUY = "B"
    SELL = "S"


class TimeInForce(str, Enum):
    ROD = "ROD"
    IOC = "IOC"
    FOK = "FOK"


class PriceFlag(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "M"
    HIGH_LIMIT = "H"
    LOW_LIMIT = "L"
    FLAT = "-"



_AP_CODE_VALUES = {
    "REGULAR": 0,
    "ODD_LOT": 2,
    "INTRADAY_ODD_LOT": 4,
    "AFTER_HOURS": 7,
}


class ApCode(str, Enum):
    """Readable names for Yuanta domestic stock order categories."""

    REGULAR = "REGULAR"
    ODD_LOT = "ODD_LOT"
    INTRADAY_ODD_LOT = "INTRADAY_ODD_LOT"
    AFTER_HOURS = "AFTER_HOURS"

    @classmethod
    def from_value(cls, value: Any) -> ApCode:
        if isinstance(value, cls):
            return value
        if isinstance(value, bool):
            raise TypeError("ap_code must be REGULAR, ODD_LOT, INTRADAY_ODD_LOT, or AFTER_HOURS")
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in _AP_CODE_VALUES:
                return cls(normalized)
            try:
                value = int(normalized)
            except ValueError:
                value = None
        try:
            sdk_value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "ap_code must be REGULAR, ODD_LOT, INTRADAY_ODD_LOT, or AFTER_HOURS"
            ) from exc
        for name, candidate in _AP_CODE_VALUES.items():
            if candidate == sdk_value:
                return cls(name)
        raise ValueError(
            "ap_code must be REGULAR, ODD_LOT, INTRADAY_ODD_LOT, or AFTER_HOURS"
        )

    def to_sdk_value(self) -> int:
        return _AP_CODE_VALUES[self.value]


FINAL_STATUSES = frozenset(
    {
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
    }
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _coerce_enum(enum_type: type[Enum], value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError:
        normalized = str(value).lower()
        for member in enum_type:
            if str(member.value).lower() == normalized:
                return member
        return default


@dataclass
class StockOrderRequest:
    """A normalized domestic stock order request.

    The same structure is used for new, cancel, replace-qty and replace-price
    operations; ``action`` tells the broker service how to map it to Yuanta.
    """

    client_order_id: str
    action: OrderAction | str = OrderAction.NEW
    account: str = ""
    order_no: str | None = None
    trade_date: str | None = None
    stk_code: str = ""
    side: OrderSide | str = OrderSide.BUY
    price: float | None = None
    quantity: int = 0
    time_in_force: TimeInForce | str = TimeInForce.ROD
    price_flag: PriceFlag | str = PriceFlag.LIMIT
    ap_code: ApCode | int = ApCode.REGULAR
    order_type: str | int = "0"
    identify: int = 1
    mock: bool = False
    broker_basket_no: str | None = None

    @classmethod
    def from_external_dict(cls, data: dict[str, Any] | StockOrderRequest) -> StockOrderRequest:
        """Parse a new caller request without weakening historical decoding."""
        if isinstance(data, StockOrderRequest):
            request = data
        else:
            if not isinstance(data, dict):
                raise TypeError("stock order request must be an object")
            _validate_external_fields(data)
            request = cls.from_dict(data)
            raw_ap_code = data.get("ap_code", data.get("APCode", request.ap_code))
            request.ap_code = ApCode.from_value(raw_ap_code)
        if not isinstance(request.ap_code, ApCode):
            request.ap_code = ApCode.from_value(request.ap_code)
        _validate_external_request(request)
        return request

    @classmethod
    def from_dict(cls, data: dict[str, Any] | Any) -> StockOrderRequest:
        if isinstance(data, StockOrderRequest):
            return data
        if not isinstance(data, dict):
            raise TypeError("StockOrderRequest.from_dict expects a mapping")
        get = _getter(data)
        return cls(
            client_order_id=str(get("client_order_id", default=get("ClientOrderID", default=""))),
            action=_coerce_enum(OrderAction, get("action", default="new"), OrderAction.NEW),
            account=str(get("account", default=get("Account", default="")) or ""),
            order_no=get("order_no", default=get("OrderNo")),
            trade_date=get("trade_date", default=get("TradeDate")),
            stk_code=str(get("stk_code", default=get("StkCode", default="")) or ""),
            side=_coerce_enum(
                OrderSide,
                get("side", default=get("buy_sell", default=get("BuySell", default="B"))),
                OrderSide.BUY,
            ),
            price=float(
                get("price", default=get("new_price", default=get("Price", default=0))) or 0
            )
            if get("price", default=get("new_price", default=get("Price"))) is not None
            else None,
            quantity=int(
                get(
                    "quantity",
                    default=get(
                        "new_quantity", default=get("qty", default=get("OrderQty", default=0))
                    ),
                )
                or 0
            ),
            time_in_force=_coerce_enum(
                TimeInForce,
                _normalize_time_in_force(
                    get("time_in_force", default=get("Time_in_force", default="ROD"))
                ),
                TimeInForce.ROD,
            ),
            price_flag=_coerce_enum(
                PriceFlag,
                _normalize_price_flag(
                    get("price_flag", default=get("PriceFlag", default="LIMIT"))
                ),
                PriceFlag.LIMIT,
            ),
            ap_code=_coerce_ap_code(get("ap_code", default=get("APCode", default=0))),
            order_type=get("order_type", default=get("OrderType", default="0")),
            identify=int(get("identify", default=get("Identify", default=1)) or 1),
            mock=_coerce_bool(get("mock", default=get("Mock", default=False))),
            broker_basket_no=get("broker_basket_no", default=get("BrokerBasketNo")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_order_id": self.client_order_id,
            "action": self.action.value if isinstance(self.action, OrderAction) else str(self.action),
            "account": self.account,
            "order_no": self.order_no,
            "trade_date": self.trade_date,
            "stk_code": self.stk_code,
            "side": self.side.value if isinstance(self.side, OrderSide) else str(self.side),
            "price": self.price,
            "quantity": self.quantity,
            "time_in_force": self.time_in_force.value if isinstance(self.time_in_force, TimeInForce) else str(self.time_in_force),
            "price_flag": self.price_flag.value if isinstance(self.price_flag, PriceFlag) else str(self.price_flag),
            "ap_code": self.ap_code.name if isinstance(self.ap_code, ApCode) else self.ap_code,
            "order_type": self.order_type,
            "identify": self.identify,
            "mock": self.mock,
            "broker_basket_no": self.broker_basket_no,
        }


    @property
    def qty(self) -> int:
        """Alias for :attr:`quantity` (broker/UI shorthand)."""
        return self.quantity

    @property
    def buy_sell(self) -> str:
        """Alias for :attr:`side` using the Yuanta field name."""
        return self.side.value if isinstance(self.side, OrderSide) else str(self.side)


@dataclass
class StockOrderState:
    """Persisted state for a client order."""

    client_order_id: str
    status: OrderStatus | str = OrderStatus.PENDING
    request: StockOrderRequest | None = None
    order_no: str | None = None
    trade_date: str | None = None
    account: str = ""
    filled_qty: int = 0
    avg_price: float | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    last_error: str | None = None
    need_manual_review: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StockOrderState:
        request_data = data.get("request")
        request = StockOrderRequest.from_dict(request_data) if request_data else None
        status = _coerce_enum(OrderStatus, data.get("status", "PENDING"), OrderStatus.PENDING)
        return cls(
            client_order_id=str(data.get("client_order_id", "")),
            status=status,
            request=request,
            order_no=data.get("order_no"),
            trade_date=data.get("trade_date"),
            account=str(data.get("account", request.account if request else "")),
            filled_qty=int(data.get("filled_qty", 0) or 0),
            avg_price=float(data["avg_price"]) if data.get("avg_price") is not None else None,
            created_at=str(data.get("created_at", _now())),
            updated_at=str(data.get("updated_at", _now())),
            transitions=list(data.get("transitions") or []),
            last_error=data.get("last_error"),
            need_manual_review=bool(data.get("need_manual_review", False)),
            raw=dict(data.get("raw") or {}),
        )

    @property
    def history(self) -> list[dict[str, Any]]:
        """Alias for :attr:`transitions`."""
        return self.transitions

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_order_id": self.client_order_id,
            "status": self.status.value if isinstance(self.status, OrderStatus) else str(self.status),
            "request": self.request.to_dict() if self.request else None,
            "order_no": self.order_no,
            "trade_date": self.trade_date,
            "account": self.account,
            "filled_qty": self.filled_qty,
            "avg_price": self.avg_price,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "transitions": self.transitions,
            "last_error": self.last_error,
            "need_manual_review": self.need_manual_review,
            "raw": self.raw,
        }


class InvalidOrderStateTransition(Exception):
    """Raised when an order tries to move to an illegal status."""


_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {
        OrderStatus.SUBMITTED,
        OrderStatus.ACCEPTED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
        OrderStatus.NEED_MANUAL_REVIEW,
    },
    OrderStatus.SUBMITTED: {
        OrderStatus.ACCEPTED,
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
        OrderStatus.NEED_MANUAL_REVIEW,
    },
    OrderStatus.ACCEPTED: {
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
        OrderStatus.NEED_MANUAL_REVIEW,
    },
    OrderStatus.PARTIALLY_FILLED: {
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
        OrderStatus.NEED_MANUAL_REVIEW,
    },
    OrderStatus.FILLED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REJECTED: set(),
    OrderStatus.FAILED: {OrderStatus.PENDING, OrderStatus.NEED_MANUAL_REVIEW},
    OrderStatus.NEED_MANUAL_REVIEW: {
        OrderStatus.PENDING,
        OrderStatus.SUBMITTED,
        OrderStatus.ACCEPTED,
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.FAILED,
        OrderStatus.NEED_MANUAL_REVIEW,
    },
}


class OrderStateMachine:
    """Validate and record order lifecycle transitions."""

    def can_transition(
        self,
        current: OrderStatus | str,
        target: OrderStatus | str,
    ) -> bool:
        current_enum = _coerce_enum(OrderStatus, current, None)
        target_enum = _coerce_enum(OrderStatus, target, None)
        if current_enum is None or target_enum is None:
            return False
        if current_enum == target_enum:
            return True
        return target_enum in _TRANSITIONS.get(current_enum, set())

    def transition(
        self,
        state: StockOrderState,
        new_status: OrderStatus | str,
        reason: str | None = None,
    ) -> StockOrderState:
        current = state.status
        if isinstance(current, str):
            current = _coerce_enum(OrderStatus, current, OrderStatus.PENDING)
        target = _coerce_enum(OrderStatus, new_status, None)
        if target is None:
            raise InvalidOrderStateTransition(f"unknown target status: {new_status}")
        if current == target:
            return state
        allowed = _TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidOrderStateTransition(
                f"illegal order transition: {current.value if isinstance(current, OrderStatus) else current} -> {target.value}"
            )
        state.status = target
        state.updated_at = _now()
        state.transitions.append(
            {
                "from": current.value if isinstance(current, OrderStatus) else str(current),
                "to": target.value,
                "reason": reason,
                "at": state.updated_at,
                "timestamp": state.updated_at,
            }
        )
        if target == OrderStatus.NEED_MANUAL_REVIEW:
            state.need_manual_review = True
        return state




def _validate_external_fields(data: dict[str, Any]) -> None:
    """Reject caller values that would otherwise silently become defaults."""
    values = {
        "action": (OrderAction, {member.value for member in OrderAction}),
        "side": (OrderSide, {member.value for member in OrderSide}),
        "time_in_force": (TimeInForce, {member.value for member in TimeInForce} | {"0", "3", "4"}),
        "price_flag": (PriceFlag, {member.value for member in PriceFlag} | {""}),
    }
    for field_name, (enum_type, allowed) in values.items():
        if field_name not in data or data[field_name] is None:
            continue
        value = data[field_name]
        raw = str(value.value if isinstance(value, enum_type) else value).strip().upper()
        if raw not in allowed and not any(str(member.value).upper() == raw for member in enum_type):
            raise ValueError(f"{field_name} has an unsupported value: {data[field_name]!r}")

    if "ap_code" in data and data["ap_code"] is not None:
        ApCode.from_value(data["ap_code"])


def _validate_external_request(request: StockOrderRequest) -> None:
    """Validate a normalized request before it can reach an adapter."""
    side = request.side.value if isinstance(request.side, OrderSide) else str(request.side).upper()
    if side not in {member.value for member in OrderSide}:
        raise ValueError("side must be B or S")

    tif = request.time_in_force.value if isinstance(request.time_in_force, TimeInForce) else str(request.time_in_force).upper()
    if tif not in {member.value for member in TimeInForce}:
        raise ValueError("time_in_force must be ROD, IOC, or FOK")

    price_flag = request.price_flag.value if isinstance(request.price_flag, PriceFlag) else str(request.price_flag).upper()
    if price_flag == "":
        price_flag = PriceFlag.LIMIT.value
    if price_flag not in {member.value for member in PriceFlag}:
        raise ValueError("price_flag has an unsupported value")

    ApCode.from_value(request.ap_code)

    action = request.action.value if isinstance(request.action, OrderAction) else str(request.action).lower()
    if action not in {member.value for member in OrderAction}:
        raise ValueError("action must be new, cancel, or replace")
    if action == OrderAction.REPLACE.value and request.quantity <= 0 and request.price is None:
        raise ValueError("replace quantity must be positive")


def _coerce_ap_code(value: Any) -> ApCode | int:
    if isinstance(value, ApCode):
        return value
    if isinstance(value, str) and not value.strip().lstrip("+-").isdigit():
        try:
            return ApCode.from_value(value)
        except ValueError:
            return ApCode.REGULAR
    return _coerce_int(value)


def _coerce_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_time_in_force(value: Any) -> Any:
    if value in {0, 3, 4, "0", "3", "4"}:
        return {0: "ROD", 3: "IOC", 4: "FOK", "0": "ROD", "3": "IOC", "4": "FOK"}[value]
    return value


def _normalize_price_flag(value: Any) -> Any:
    if value == "":
        return "LIMIT"
    return value


def _getter(data: dict[str, Any]) -> Any:
    """Return a helper that reads snake_case first and falls back to aliases."""

    def get(*keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in data:
                return data[key]
        return default

    return get


__all__ = [
    "FINAL_STATUSES",
    "ApCode",
    "InvalidOrderStateTransition",
    "OrderAction",
    "OrderSide",
    "OrderStateMachine",
    "OrderStatus",
    "PriceFlag",
    "StockOrderRequest",
    "StockOrderState",
    "TimeInForce",
]
