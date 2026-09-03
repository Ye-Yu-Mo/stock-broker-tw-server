"""M3 serializer tests for read-only Yuanta response objects."""

from __future__ import annotations

import json
from typing import ClassVar

from stock_broker_tw.yuanta.serializer import (
    bank_balance_result_to_dict,
    order_trade_report_result_to_dict,
    real_report_merge_result_to_dict,
    real_report_result_to_dict,
    realized_gain_loss_result_to_dict,
    reversal_report_result_to_dict,
    store_summary_result_to_dict,
    to_dict,
    transaction_outlay_result_to_dict,
    unrealized_gain_loss_result_to_dict,
)


class FakeYuantaDate:
    ushtYear = 2026
    bytMon = 8
    bytDay = 27


class FakeYuantaTime:
    bytHour = 10
    bytMin = 30
    bytSec = 15
    ushtMSec = 123


class FakeStkStore:
    Account = "S98875005091"
    TradeKind = 0
    MarketNo = "TWSE"
    MarketName = "上市"
    StkCode = "2330"
    StkName = "台積電"
    StockQty = 1000
    Price = 100.0
    Cost = 90.0
    Interest = 0
    BuyNotInNos = 0
    SellNotInNos = 0
    TradingQty = 1000
    Loan = 0
    TaxRate = 3
    LotSize = 1000
    MarketPrice = 105.0
    Decimal = 0
    StkType1 = 0
    StkType2 = 0
    BuyPrice = 104.0
    SellPrice = 106.0
    UpStopPrice = 115.0
    DownStopPrice = 95.0
    PriceMultiplier = 1
    CurrencyType = "TWD"
    CDQTY = 0
    OddTradingQty = 0
    ReturnAmt = 15000.0
    MarketAmt = 105000.0


class FakeOVStkStore:
    Account = "S98875005091"
    CurrencyType = "USD"
    MarketNo = "NYSE"
    MarketName = "NYSE"
    StkCode = "AAPL"
    StkName = "APPLE"
    StkFullName = "Apple Inc."
    StockQty = 10
    TradingQty = 10
    Price = 200.0
    Cost = 180.0
    CloseRate = 31.0
    RateKind = 1
    LotSize = 1
    MarketPrice = 0.0
    Decimal = 2
    BuyPrice = 199.0
    SellPrice = 201.0


class FakeStoreSummaryResult:
    StkStoreList: ClassVar[list[FakeStkStore]] = [FakeStkStore()]
    OVStkStoreList: ClassVar[list[FakeOVStkStore]] = [FakeOVStkStore()]


class FakeMarketType:
    def __str__(self) -> str:
        return "TWSE"


class FakeStkStoreWithEnum(FakeStkStore):
    MarketNo = FakeMarketType()


class FakeStoreSummaryResultWithEnum:
    StkStoreList: ClassVar[list[FakeStkStore]] = [FakeStkStoreWithEnum()]
    OVStkStoreList: ClassVar[list[FakeOVStkStore]] = []


class FakeBankBalance:
    Account = "S98875005091"
    ResponseTime = "10:30:15"
    BankAccount = "0123456789"
    AvailableBalance = 123456.78
    Message = ""


class FakeBankBalanceResult:
    BankBalanceList: ClassVar[list[FakeBankBalance]] = [FakeBankBalance()]


class FakeTransactionOutlay:
    Account = "S98875005091"
    SettlementDay = "2026/08/28"
    SettlementAmt = 12345.0


class FakeTransactionOutlayResult:
    TransactionOutlayList: ClassVar[list[FakeTransactionOutlay]] = [FakeTransactionOutlay()]


class FakeUnGainLossDetail:
    Account = "S98875005091"
    TradeKind = 0
    MarketNo = "TWSE"
    StkCode = "2330"
    StockQty = 1000
    Price = 100.0
    TradeDate = "2026/08/01"
    Cost = 90.0
    Interest = 0
    ReturnAmt = 15000.0
    MarketAmt = 105000.0


class FakeUnGainLossDetailResult:
    UnGainLossDetailList: ClassVar[list[FakeUnGainLossDetail]] = [FakeUnGainLossDetail()]


class FakeRealizedGainLoss:
    Account = "S98875005091"
    MarketNo = "TWSE"
    StkCode = "2330"
    TradeDate = "2026/08/01"
    TradeKind = 0
    Price = 105.0
    Qty = 1000
    ProfitLoss = 15000
    OrderNo = "H00001"
    TermSplit = 0
    TermExt = ""
    Charge = 100
    Cost = 90000
    Tax = 300
    TotalAMT = 105000


class FakeRealizedGainLossResult:
    RealizedGainLossList: ClassVar[list[FakeRealizedGainLoss]] = [FakeRealizedGainLoss()]


class FakeRealizedGainLossWithEnum(FakeRealizedGainLoss):
    MarketNo = FakeMarketType()


class FakeRealizedGainLossResultWithEnum:
    RealizedGainLossList: ClassVar[list[FakeRealizedGainLoss]] = [FakeRealizedGainLossWithEnum()]


class FakeReversalReport:
    Account = "S98875005091"
    ReversalDate = "2026/08/01"
    ReversalPrice = 105.0
    ReversalQty = 1000
    GlAmt = 15000.0


class FakeReversalReportResult:
    ReversalReportList: ClassVar[list[FakeReversalReport]] = [FakeReversalReport()]


class FakeRealReport:
    Account = "S98875005091"
    RptType = 50
    OrderNo = "H00001"
    MarketNo = "TWSE"
    CompanyNo = "2330"
    StkCName = "台積電"
    OrderDate = FakeYuantaDate()
    OrderTime = FakeYuantaTime()
    OrderType = "0"
    BS = "B"
    Price = 100.0
    TouchPrice = 0.0
    BeforeQty = 0
    OrderQty = 1000
    OpenOffsetKind = "0"
    DayTrade = " "
    OrderCond = "0"
    OrderErrorNo = ""
    TradeKind = 1
    APCode = 0
    BasketNo = ""
    OrderStatus = 20
    StkType1 = 0
    StkType2 = 0
    BelongMarketNo = 0
    BelongStkCode = ""
    SeqNo = 0
    PriceType = "2"
    StkErrorNo = ""


class FakeRealReportResult:
    RealReportList: ClassVar[list[FakeRealReport]] = [FakeRealReport()]


class FakeRealReportMerge:
    Account = "S98875005091"
    RptType = 1
    OrderNo = "H00001"
    MarketNo = "TWSE"
    CompanyNo = "2330"
    OrderDate = FakeYuantaDate()
    OrderTime = FakeYuantaTime()
    OrderType = "0"
    BS = "B"
    Price = 100.0
    TouchPrice = 0.0
    LastDealPrice = 105.0
    AvgDealPrice = 104.0
    BeforeQty = 0
    OrderQty = 1000
    OkQty = 1000
    OpenOffsetKind = "0"
    DayTrade = " "
    OrderCond = "0"
    OrderErrorNo = ""
    APCode = 0
    OrderStatus = 20
    LastOrderStatus = 8
    StkCName = "台積電"
    TradeCode = "2330"
    StrikePrice = 0.0
    BasketNo = ""
    StkType1 = 0
    StkType2 = 0
    BelongMarketNo = 0
    BelongStkCode = ""
    StkType = "2"
    StkErrorNo = ""


class FakeRealReportMergeResult:
    RealReportMergeList: ClassVar[list[FakeRealReportMerge]] = [FakeRealReportMerge()]


class FakeStkOrder:
    Account = "S98875005091"
    TradeDate = FakeYuantaDate()
    MarketNo = "TWSE"
    MarketName = "上市"
    CompanyNo = "2330"
    StkName = "台積電"
    OrderType = 0
    BS = "B"
    Price = 100.0
    PriceFlag = "2"
    BeforeQty = 0
    AfterQty = 1000
    OkQty = 1000
    OrderStatus = 20
    AcceptDate = FakeYuantaDate()
    AcceptTime = FakeYuantaTime()
    OrderNo = "H00001"
    ErrorNo = ""
    ErrorMessage = ""
    Seller = 0
    Channel = ""
    APCode = 0
    OTax = 0
    OCharge = 0
    ODueAmt = 0
    CancelFlag = "Y"
    ReduceFlag = "Y"
    TraditionFlag = "N"
    BasketNo = ""
    TradeCurrency = "TWD"
    Time_in_Force = "0"
    Order_Success = ""
    Reduce_Flag = ""
    Chg_Prz_Flag = ""
    TSE_Cancel = ""
    CancelQty = 0
    OR_QTY = 1000
    UpdateDate = FakeYuantaDate()
    UpdateTime = FakeYuantaTime()


class FakeStkTrade:
    Account = "S98875005091"
    MarketNo = "TWSE"
    MarketName = "上市"
    CompanyNo = "2330"
    StkName = "台積電"
    OrderType = 0
    BS = "B"
    OkQty = 1000
    OPrice = 100.0
    SPrice = 105.0
    DateTime = "2026/08/27 10:30:15"
    OrderNo = "H00001"
    TradeCurrency = "TWD"
    Price_Flag = "2"
    Exchange_Code = 0


class FakeOrderTradeReportResult:
    StkOrderList: ClassVar[list[FakeStkOrder]] = [FakeStkOrder()]
    StkTradeList: ClassVar[list[FakeStkTrade]] = [FakeStkTrade()]
    FutOrderList: ClassVar[list] = []
    FutTradeList: ClassVar[list] = []
    OVStkOrderList: ClassVar[list] = []
    OVStkTradeList: ClassVar[list] = []
    OVFutOrderList: ClassVar[list] = []
    OVFutTradeList: ClassVar[list] = []


def test_store_summary_result_to_dict() -> None:
    data = store_summary_result_to_dict(FakeStoreSummaryResult())
    assert data["stk_store_list"][0]["stk_code"] == "2330"
    assert data["stk_store_list"][0]["return_amt"] == 15000.0
    assert data["ov_stk_store_list"][0]["stk_full_name"] == "Apple Inc."


def test_bank_balance_result_to_dict() -> None:
    data = bank_balance_result_to_dict(FakeBankBalanceResult())
    assert data["bank_balance_list"][0]["available_balance"] == 123456.78


def test_transaction_outlay_result_to_dict() -> None:
    data = transaction_outlay_result_to_dict(FakeTransactionOutlayResult())
    assert data["transaction_outlay_list"][0]["settlement_amt"] == 12345.0


def test_unrealized_gain_loss_result_to_dict() -> None:
    data = unrealized_gain_loss_result_to_dict(FakeUnGainLossDetailResult())
    assert data["un_gain_loss_detail_list"][0]["stock_qty"] == 1000


def test_realized_gain_loss_result_to_dict() -> None:
    data = realized_gain_loss_result_to_dict(FakeRealizedGainLossResult())
    assert data["realized_gain_loss_list"][0]["order_no"] == "H00001"


def test_reversal_report_result_to_dict() -> None:
    data = reversal_report_result_to_dict(FakeReversalReportResult())
    assert data["reversal_report_list"][0]["gl_amt"] == 15000.0


def test_real_report_result_to_dict() -> None:
    data = real_report_result_to_dict(FakeRealReportResult())
    row = data["real_report_list"][0]
    assert row["order_no"] == "H00001"
    assert row["order_date"]["year"] == 2026


def test_real_report_merge_result_to_dict() -> None:
    data = real_report_merge_result_to_dict(FakeRealReportMergeResult())
    row = data["real_report_merge_list"][0]
    assert row["order_no"] == "H00001"
    assert row["ok_qty"] == 1000


def test_order_trade_report_result_to_dict() -> None:
    data = order_trade_report_result_to_dict(FakeOrderTradeReportResult())
    assert data["stk_order_list"][0]["order_no"] == "H00001"
    assert data["stk_trade_list"][0]["s_price"] == 105.0
    assert data["fut_order_list"] == []


def test_to_dict_dispatches_m3_result_types() -> None:
    assert to_dict(FakeStoreSummaryResult()) == store_summary_result_to_dict(FakeStoreSummaryResult())
    assert to_dict(FakeBankBalanceResult()) == bank_balance_result_to_dict(FakeBankBalanceResult())
    assert to_dict(FakeOrderTradeReportResult()) == order_trade_report_result_to_dict(
        FakeOrderTradeReportResult()
    )


class FakeYuantaDateTime:
    ushtYear = 2026
    bytMon = 8
    bytDay = 27
    bytHour = 10
    bytMin = 30
    bytSec = 15
    ushtMSec = 123


def test_yuanta_datetime_to_dict() -> None:
    from stock_broker_tw.yuanta.serializer import to_dict

    assert to_dict(FakeYuantaDateTime()) == {
        "year": 2026,
        "month": 8,
        "day": 27,
        "hour": 10,
        "minute": 30,
        "second": 15,
        "millisecond": 123,
    }


def test_to_dict_reflection_failure_includes_placeholder(caplog) -> None:
    import logging

    class BrokenProp:
        Name = "CriticalField"

        def GetValue(self, obj, none):
            raise RuntimeError("boom")

    class BrokenType:
        def GetProperties(self):
            return [BrokenProp()]

    class BrokenObject:
        def GetType(self):
            return BrokenType()

    with caplog.at_level(logging.WARNING):
        result = to_dict(BrokenObject())
    assert result == {"critical_field": None}
    assert any("CriticalField" in record.message for record in caplog.records)


def test_to_dict_python_fallback_failure_includes_placeholder(caplog) -> None:
    import logging

    class BrokenAttribute:
        @property
        def critical_field(self):
            raise RuntimeError("boom")

    with caplog.at_level(logging.WARNING):
        result = to_dict(BrokenAttribute())
    assert result.get("critical_field") is None
    assert any("critical_field" in record.message for record in caplog.records)


def test_m3_market_no_enum_values_are_json_safe() -> None:
    cases = [
        (
            store_summary_result_to_dict(FakeStoreSummaryResultWithEnum()),
            lambda data: data["stk_store_list"][0]["market_no"],
        ),
        (
            realized_gain_loss_result_to_dict(FakeRealizedGainLossResultWithEnum()),
            lambda data: data["realized_gain_loss_list"][0]["market_no"],
        ),
    ]

    for data, get_market_no in cases:
        assert get_market_no(data) == "TWSE"
        json.dumps(data)
