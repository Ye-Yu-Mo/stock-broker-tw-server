"""M5 quote serializer tests."""

from __future__ import annotations

from typing import ClassVar

from stock_broker_tw.yuanta.serializer import (
    five_tick_a_result_to_dict,
    k_line_result_to_dict,
    market_info_result_to_dict,
    stick_detail_result_to_dict,
    stk_classify_price_result_to_dict,
    stk_information_result_to_dict,
    stock_other_info_result_to_dict,
    stock_tick_result_to_dict,
    to_dict,
    watch_list_all_result_to_dict,
    watch_list_result_to_dict,
)


class FakeTime:
    bytHour = 10
    bytMin = 30
    bytSec = 15
    ushtMSec = 123


class FakeWatchListResult:
    Key = "TWSE2330"
    MarketType = "TWSE"
    StkCode = "2330"
    IndexFlag = 7
    Value = 500.0


class FakeWatchListAllResult:
    Key = "TWSE2330"
    MarketType = "TWSE"
    StkCode = "2330"
    SeqNo = 100
    IndexFlag = 22
    Value = None
    IndexFlag_22 = None
    IndexFlag_28 = None
    IndexFlag_29 = None


class FakeFlag22:
    BuyVol = 10
    SellVol = 20


class FakeFiveTickAResult:
    Key = "TWSE2330"
    MarketType = "TWSE"
    StkCode = "2330"
    IndexFlag = 50
    Value = None
    IndexFlag_20 = None
    IndexFlag_21 = None
    IndexFlag_42 = None
    IndexFlag_43 = None
    IndexFlag_50 = None
    IndexFlag_51 = None


class FakeFlag50:
    BuyPrice1 = 100.0
    BuyPrice2 = 99.0
    BuyPrice3 = 98.0
    BuyPrice4 = 97.0
    BuyPrice5 = 96.0
    BuyVol1 = 1
    BuyVol2 = 2
    BuyVol3 = 3
    BuyVol4 = 4
    BuyVol5 = 5
    SellPrice1 = 101.0
    SellPrice2 = 102.0
    SellPrice3 = 103.0
    SellPrice4 = 104.0
    SellPrice5 = 105.0
    SellVol1 = 6
    SellVol2 = 7
    SellVol3 = 8
    SellVol4 = 9
    SellVol5 = 10


class FakeStockTickResult:
    Key = "TWSE2330"
    MarketType = "TWSE"
    StkCode = "2330"
    SerialNo = 1
    Time = FakeTime()
    BuyPrice = 100.0
    SellPrice = 101.0
    DealPrice = 100.5
    DealVol = 10
    InOutFlag = 1
    Type = 0


class FakeMarketInfoResult:
    Key = "TWSE2330"
    MarketType = "TWSE"
    StkCode = "2330"
    DealPrice = 500.0
    TickVol = 100
    Time = FakeTime()
    TradeStatus = 1


class FakeStockOtherInfoResult:
    Key = "TWSE2330"
    MarketType = "TWSE"
    StkCode = "2330"
    IndexFlag = 1
    TradeTime = FakeTime()


class FakeStkInformation:
    MarketNo = "TWSE"
    StockCode = "2330"
    Dayoffmark = "Y"
    Creditpercent = 60
    Lendpercent = 90
    Creditremnants = 999999
    Lendremnants = -1
    LendSellMark = "Y"
    RecallDate = "1150101"
    LendQty = 1000
    StockWarning: ClassVar[list[str]] = []
    UpdateDate = "1150101"


class FakeStkInformationResult:
    StockInformationList: ClassVar[list[FakeStkInformation]] = [FakeStkInformation()]


class FakeStickDetail:
    TimeStamp = "2026/08/27 09:30:00"
    DealPrice = 500.0
    DealVol = 100
    BuyPrice = 499.0
    SellPrice = 501.0
    SeqNo = 1
    InOutFlag = 0


class FakeStickDetailResult:
    MarketNo = "TWSE"
    StockCode = "2330"
    StickDetailList: ClassVar[list[FakeStickDetail]] = [FakeStickDetail()]


class FakeClassifyPrice:
    Price = 500.0
    InDealVol = 100
    OutDealVol = 200
    TotalDealVol = 300


class FakeStkClassifyPriceResult:
    Date = "2026/08/27"
    MarketNo = "TWSE"
    StockCode = "2330"
    ClassifyPriceList: ClassVar[list[FakeClassifyPrice]] = [FakeClassifyPrice()]


class FakeKLine:
    TimeStamp = "2026/08/27"
    OpenPrice = 500.0
    HighPrice = 510.0
    LowPrice = 490.0
    ClosePrice = 505.0
    DealVol = 1000


class FakeKLineResult:
    MarketNo = "TWSE"
    StockCode = "2330"
    KLineList: ClassVar[list[FakeKLine]] = [FakeKLine()]


def test_watch_list_result_to_dict() -> None:
    data = watch_list_result_to_dict(FakeWatchListResult())
    assert data["stk_code"] == "2330"
    assert data["index_flag"] == 7
    assert data["value"] == 500.0


def test_watch_list_all_result_to_dict() -> None:
    result = FakeWatchListAllResult()
    result.IndexFlag_22 = FakeFlag22()
    data = watch_list_all_result_to_dict(result)
    assert data["index_flag_22"] == {"buy_vol": 10, "sell_vol": 20}


def test_five_tick_a_result_to_dict() -> None:
    result = FakeFiveTickAResult()
    result.IndexFlag_50 = FakeFlag50()
    data = five_tick_a_result_to_dict(result)
    assert data["index_flag_50"]["buy_price1"] == 100.0
    assert data["index_flag_50"]["sell_vol5"] == 10


def test_stock_tick_result_to_dict() -> None:
    data = stock_tick_result_to_dict(FakeStockTickResult())
    assert data["stk_code"] == "2330"
    assert data["time"]["hour"] == 10


def test_market_info_result_to_dict() -> None:
    data = market_info_result_to_dict(FakeMarketInfoResult())
    assert data["trade_status"] == 1


def test_stock_other_info_result_to_dict() -> None:
    data = stock_other_info_result_to_dict(FakeStockOtherInfoResult())
    assert data["trade_time"]["minute"] == 30


def test_stk_information_result_to_dict() -> None:
    data = stk_information_result_to_dict(FakeStkInformationResult())
    assert data["stock_information_list"][0]["stock_code"] == "2330"


def test_stick_detail_result_to_dict() -> None:
    data = stick_detail_result_to_dict(FakeStickDetailResult())
    assert data["stock_code"] == "2330"
    assert data["stick_detail_list"][0]["deal_price"] == 500.0


def test_stk_classify_price_result_to_dict() -> None:
    data = stk_classify_price_result_to_dict(FakeStkClassifyPriceResult())
    assert data["classify_price_list"][0]["total_deal_vol"] == 300


def test_k_line_result_to_dict() -> None:
    data = k_line_result_to_dict(FakeKLineResult())
    assert data["k_line_list"][0]["close_price"] == 505.0


def test_to_dict_dispatches_m5_types() -> None:
    assert to_dict(FakeWatchListResult()) == watch_list_result_to_dict(FakeWatchListResult())
    assert to_dict(FakeStockTickResult()) == stock_tick_result_to_dict(FakeStockTickResult())
    assert to_dict(FakeKLineResult()) == k_line_result_to_dict(FakeKLineResult())
