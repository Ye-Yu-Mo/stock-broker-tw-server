"""Unit tests for Yuanta .NET object serialization."""

from __future__ import annotations

from typing import ClassVar

from stock_broker_tw.yuanta.serializer import (
    login_data_to_dict,
    login_result_to_dict,
    serialize,
    status_to_dict,
    to_dict,
    to_list,
)


class FakeStatus:
    MsgCode = "0001"
    MsgContent = "成功"
    Count = 1


class FakeLoginData:
    Account = "S98875005091"
    Name = "測試用戶"
    InvestorID = "A123456789"
    SellerNo = "9527"


class FakeLoginResult:
    LoginStatus = FakeStatus()
    LoginList: ClassVar[list[FakeLoginData]] = [FakeLoginData(), FakeLoginData()]


class FakeYuantaDate:
    ushtYear = 2026
    bytMon = 8
    bytDay = 27


class FakeYuantaTime:
    bytHour = 10
    bytMin = 30
    bytSec = 15
    ushtMSec = 123


def test_status_to_dict() -> None:
    assert status_to_dict(FakeStatus()) == {
        "msg_code": "0001",
        "msg_content": "成功",
        "count": 1,
    }


def test_login_data_to_dict() -> None:
    assert login_data_to_dict(FakeLoginData()) == {
        "account": "S98875005091",
        "name": "測試用戶",
        "investor_id": "A123456789",
        "seller_no": "9527",
    }


def test_login_result_to_dict() -> None:
    result = login_result_to_dict(FakeLoginResult())
    assert result["login_status"] == status_to_dict(FakeStatus())
    assert len(result["login_list"]) == 2
    assert result["login_list"][0]["account"] == "S98875005091"


def test_serialize_dispatches_to_known_types() -> None:
    assert serialize(FakeLoginResult()) == login_result_to_dict(FakeLoginResult())


def test_to_dict_none() -> None:
    assert to_dict(None) is None


def test_to_list_converts_nested_objects() -> None:
    items = [FakeLoginData()]
    assert to_list(items) == [login_data_to_dict(FakeLoginData())]


def test_to_dict_handles_dates_and_times() -> None:
    assert to_dict(FakeYuantaDate()) == {"year": 2026, "month": 8, "day": 27}
    assert to_dict(FakeYuantaTime()) == {
        "hour": 10,
        "minute": 30,
        "second": 15,
        "millisecond": 123,
    }


def test_to_dict_reflection_fallback() -> None:
    class Arbitrary:
        Foo = "bar"
        Count = 3

    # Arbitrary objects are not lists; fallback should expose public attributes.
    assert to_dict(Arbitrary()) == {"foo": "bar", "count": 3}


def test_to_dict_primitive() -> None:
    assert to_dict("hello") == "hello"
    assert to_dict(123) == 123
    assert to_dict(1.5) == 1.5
    assert to_dict(True) is True
