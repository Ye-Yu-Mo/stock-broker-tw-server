"""Convert Yuanta .NET response objects into plain Python dict/list.

Business code should never depend on pythonnet / .NET types directly.  This
module is the single place where ``OnResponse`` payloads are translated into
JSON-friendly structures.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any


def _snake(name: str) -> str:
    """Convert a C#/PascalCase name to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower().replace("__", "_")


def _is_list_like(obj: Any) -> bool:
    if obj is None or isinstance(obj, (str, bytes, dict)):
        return False
    if isinstance(obj, (list, tuple)):
        return True
    # .NET List<T>/arrays look like a sequence with Count and indexer access.
    if hasattr(obj, "Count") and hasattr(obj, "__getitem__"):
        return True
    # Some pythonnet collections are iterable without exposing __getitem__.
    return bool(hasattr(obj, "Count") and hasattr(obj, "__iter__") and not hasattr(obj, "MsgCode"))


def status_to_dict(status: Any) -> dict[str, Any]:
    """Serialize a ``Status``-like object (MsgCode/MsgContent/Count)."""
    return {
        "msg_code": getattr(status, "MsgCode", None),
        "msg_content": getattr(status, "MsgContent", None),
        "count": getattr(status, "Count", None),
    }


def login_data_to_dict(data: Any) -> dict[str, Any]:
    """Serialize a ``LoginData`` object."""
    return {
        "account": getattr(data, "Account", None),
        "name": getattr(data, "Name", None),
        "investor_id": getattr(data, "InvestorID", None),
        "seller_no": getattr(data, "SellerNo", None),
    }


def login_result_to_dict(result: Any) -> dict[str, Any]:
    """Serialize a ``LoginResult`` object."""
    return {
        "login_status": status_to_dict(getattr(result, "LoginStatus", None)),
        "login_list": to_list(getattr(result, "LoginList", None)),
    }


def yuanta_date_to_dict(value: Any) -> dict[str, Any]:
    """Serialize a ``TYuantaDate``-like object."""
    return {
        "year": getattr(value, "Year", getattr(value, "ushtYear", None)),
        "month": getattr(value, "Month", getattr(value, "bytMon", None)),
        "day": getattr(value, "Day", getattr(value, "bytDay", None)),
    }


def yuanta_time_to_dict(value: Any) -> dict[str, Any]:
    """Serialize a ``TYuantaTime``-like object."""
    return {
        "hour": getattr(value, "Hour", getattr(value, "bytHour", None)),
        "minute": getattr(value, "Minute", getattr(value, "bytMin", None)),
        "second": getattr(value, "Second", getattr(value, "bytSec", None)),
        "millisecond": getattr(
            value, "Millisecond", getattr(value, "ushtMSec", None)
        ),
    }


def to_list(obj: Any) -> list[Any]:
    """Convert a .NET list/array or Python sequence to a list of dicts."""
    if obj is None:
        return []
    if isinstance(obj, (list, tuple)):
        return [to_dict(item) for item in obj]

    items: list[Any] = []
    if hasattr(obj, "Count") and hasattr(obj, "__getitem__"):
        try:
            items = [obj[i] for i in range(int(obj.Count))]
        except Exception:
            items = list(obj)
    else:
        try:
            items = list(obj)
        except TypeError:
            items = [obj]
    return [to_dict(item) for item in items]


def to_dict(obj: Any) -> Any:
    """Convert a Yuanta .NET object (or Python stand-in) to plain Python data."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    name = type(obj).__name__.lower()

    # Explicit known types.
    if "loginresult" in name:
        return login_result_to_dict(obj)
    if name in {"status", "orderstatus"} or (
        hasattr(obj, "MsgCode") and hasattr(obj, "MsgContent")
    ):
        return status_to_dict(obj)
    if "logindata" in name or (
        hasattr(obj, "Account") and hasattr(obj, "InvestorID")
    ):
        return login_data_to_dict(obj)

    # Date/time helpers used by the official examples.
    if hasattr(obj, "ushtYear") or (
        hasattr(obj, "Year") and hasattr(obj, "Month") and hasattr(obj, "Day")
    ):
        return yuanta_date_to_dict(obj)
    if hasattr(obj, "bytHour") or (
        hasattr(obj, "Hour") and hasattr(obj, "Minute") and hasattr(obj, "Second")
    ):
        return yuanta_time_to_dict(obj)

    if _is_list_like(obj):
        return to_list(obj)

    # .NET objects: use reflection if available.
    get_type = getattr(obj, "GetType", None)
    if callable(get_type):
        try:
            props = obj.GetType().GetProperties()
            result: dict[str, Any] = {}
            for prop in props:
                prop_name = getattr(prop, "Name", "")
                if not prop_name:
                    continue
                try:
                    value = prop.GetValue(obj, None)
                except Exception:
                    continue
                result[_snake(prop_name)] = to_dict(value)
            if result:
                return result
        except Exception:
            pass

    # Generic Python fallback: expose public non-callable attributes.
    result = {}
    for attr in dir(obj):
        if attr.startswith("_"):
            continue
        try:
            value = getattr(obj, attr)
        except Exception:
            continue
        if callable(value):
            continue
        result[_snake(attr)] = to_dict(value)
    return result


def serialize(obj: Any) -> Any:
    """Alias for :func:`to_dict`."""
    return to_dict(obj)


# Friendly aliases matching common naming expectations.
serialize_login_result = login_result_to_dict
serialize_status = status_to_dict
serialize_login_data = login_data_to_dict
serialize_object = to_dict
object_to_dict = to_dict
