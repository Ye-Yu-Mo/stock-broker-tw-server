"""Convert Yuanta .NET response objects into plain Python dict/list.

Business code should never depend on pythonnet / .NET types directly.  This
module is the single place where ``OnResponse`` payloads are translated into
JSON-friendly structures.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


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
    if isinstance(status, dict):
        return {
            "msg_code": status.get("MsgCode"),
            "msg_content": status.get("MsgContent"),
            "count": status.get("Count"),
        }
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


def yuanta_datetime_to_dict(value: Any) -> dict[str, Any]:
    """Serialize a ``TYuantaDateTime``-like object (date + time)."""
    return {
        **yuanta_date_to_dict(value),
        **yuanta_time_to_dict(value),
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
    if isinstance(obj, dict):
        return {str(key): to_dict(value) for key, value in obj.items()}
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

    # M3 read-only query result wrappers.
    if "storesummaryresult" in name or (
        hasattr(obj, "StkStoreList") and hasattr(obj, "OVStkStoreList")
    ):
        return store_summary_result_to_dict(obj)
    if "bankbalanceresult" in name or hasattr(obj, "BankBalanceList"):
        return bank_balance_result_to_dict(obj)
    if "transactionoutlayresult" in name or (
        hasattr(obj, "TransactionOutlayList") and not hasattr(obj, "ReversalReportList")
    ):
        return transaction_outlay_result_to_dict(obj)
    if "ungainlossdetailresult" in name or hasattr(obj, "UnGainLossDetailList"):
        return unrealized_gain_loss_result_to_dict(obj)
    if "realizedgainlossresult" in name or hasattr(obj, "RealizedGainLossList"):
        return realized_gain_loss_result_to_dict(obj)
    if "reversalreportresult" in name or hasattr(obj, "ReversalReportList"):
        return reversal_report_result_to_dict(obj)
    if "realreportresult" in name or hasattr(obj, "RealReportList"):
        return real_report_result_to_dict(obj)
    if "realreportmergeresult" in name or hasattr(obj, "RealReportMergeList"):
        return real_report_merge_result_to_dict(obj)
    if (
        hasattr(obj, "StkOrderList")
        or hasattr(obj, "StkTradeList")
        or hasattr(obj, "FutOrderList")
        or hasattr(obj, "FutTradeList")
        or hasattr(obj, "OVStkOrderList")
        or hasattr(obj, "OVFutOrderList")
    ):
        return order_trade_report_result_to_dict(obj)

    # M5 quote subscription/query result wrappers.
    if "watchlistresult" in name or (
        hasattr(obj, "Key") and hasattr(obj, "IndexFlag") and hasattr(obj, "StkCode") and hasattr(obj, "Value")
    ):
        return watch_list_result_to_dict(obj)
    if "watchlistallresult" in name or (
        hasattr(obj, "Key") and hasattr(obj, "SeqNo") and hasattr(obj, "IndexFlag") and hasattr(obj, "StkCode")
    ):
        return watch_list_all_result_to_dict(obj)
    if "fivetickaresult" in name or (
        hasattr(obj, "Key") and hasattr(obj, "IndexFlag") and hasattr(obj, "StkCode") and hasattr(obj, "IndexFlag_50")
    ):
        return five_tick_a_result_to_dict(obj)
    if "stocktickresult" in name or (
        hasattr(obj, "SerialNo") and hasattr(obj, "DealVol") and hasattr(obj, "InOutFlag")
    ):
        return stock_tick_result_to_dict(obj)
    if "marketinforesult" in name or (
        hasattr(obj, "TickVol") and hasattr(obj, "TradeStatus") and hasattr(obj, "DealPrice")
    ):
        return market_info_result_to_dict(obj)
    if "stockotherinforesult" in name or (
        hasattr(obj, "IndexFlag") and hasattr(obj, "TradeTime") and hasattr(obj, "Key")
    ):
        return stock_other_info_result_to_dict(obj)
    if "stkinformationresult" in name or hasattr(obj, "StockInformationList"):
        return stk_information_result_to_dict(obj)
    if "stickdetailresult" in name or hasattr(obj, "StickDetailList"):
        return stick_detail_result_to_dict(obj)
    if "stkclassifypriceresult" in name or hasattr(obj, "ClassifyPriceList"):
        return stk_classify_price_result_to_dict(obj)
    if "klineresult" in name or hasattr(obj, "KLineList"):
        return k_line_result_to_dict(obj)
    if "querywatchlistresult" in name or hasattr(obj, "QueryWatchList"):
        return query_watch_list_result_to_dict(obj)
    if "subquotelistresult" in name or (
        hasattr(obj, "QuoteList") and hasattr(obj, "Account")
    ):
        return sub_quote_list_result_to_dict(obj)

    # M5 quote row objects.
    if "fivetick" in name or (
        hasattr(obj, "BuyPrice1")
        and hasattr(obj, "BuyVol1")
        and hasattr(obj, "SellPrice1")
    ):
        return five_tick_a_flag_to_dict(obj)
    if "stkinformation" in name or (
        hasattr(obj, "Dayoffmark") and hasattr(obj, "Creditpercent")
    ):
        return stk_information_to_dict(obj)
    if "stickdetail" in name or (
        hasattr(obj, "TimeStamp") and hasattr(obj, "DealPrice") and hasattr(obj, "DealVol")
    ):
        return stick_detail_to_dict(obj)
    if "classifyprice" in name or (
        hasattr(obj, "InDealVol") and hasattr(obj, "OutDealVol")
    ):
        return classify_price_to_dict(obj)
    if "kline" in name or (
        hasattr(obj, "OpenPrice") and hasattr(obj, "ClosePrice") and hasattr(obj, "DealVol")
    ):
        return k_line_to_dict(obj)
    if "querywatchlist" in name or (
        hasattr(obj, "StkName") and hasattr(obj, "YstPrice") and hasattr(obj, "DealPrice")
    ):
        return query_watch_list_to_dict(obj)

    # M3 read-only query row objects.
    if "ovstkstore" in name or (hasattr(obj, "StkFullName") and hasattr(obj, "RateKind")):
        return ov_stk_store_to_dict(obj)
    if "stkstore" in name or (
        hasattr(obj, "TradingQty")
        and hasattr(obj, "MarketAmt")
        and hasattr(obj, "ReturnAmt")
        and hasattr(obj, "OddTradingQty")
    ):
        return stk_store_to_dict(obj)
    if "bankbalance" in name or (
        hasattr(obj, "BankAccount") and hasattr(obj, "AvailableBalance")
    ):
        return bank_balance_to_dict(obj)
    if "transactionoutlay" in name or (
        hasattr(obj, "SettlementDay") and hasattr(obj, "SettlementAmt")
    ):
        return transaction_outlay_to_dict(obj)
    if "ungainlossdetail" in name or (
        not hasattr(obj, "UnGainLossDetailList")
        and hasattr(obj, "StockQty")
        and hasattr(obj, "ReturnAmt")
        and hasattr(obj, "MarketAmt")
        and hasattr(obj, "TradeDate")
        and not hasattr(obj, "ProfitLoss")
    ):
        return unrealized_gain_loss_detail_to_dict(obj)
    if "realizedgainloss" in name or (
        hasattr(obj, "ProfitLoss")
        and hasattr(obj, "OrderNo")
        and hasattr(obj, "TermSplit")
    ):
        return realized_gain_loss_to_dict(obj)
    if "reversalreport" in name or (
        hasattr(obj, "ReversalDate") and hasattr(obj, "GlAmt")
    ):
        return reversal_report_to_dict(obj)
    if "realreportmerge" in name or (
        hasattr(obj, "OkQty") and hasattr(obj, "AvgDealPrice")
    ):
        return real_report_merge_to_dict(obj)
    if "stkorderresult" in name or (
        hasattr(obj, "ResultCount") and hasattr(obj, "ResultList")
    ):
        return stk_order_result_to_dict(obj)
    if "stkorderdata" in name or (
        hasattr(obj, "Identify") and hasattr(obj, "ReplyCode") and hasattr(obj, "OrderNO")
    ):
        return stk_order_data_to_dict(obj)
    if "realreport" in name or (
        hasattr(obj, "RptType")
        and hasattr(obj, "CompanyNo")
        and hasattr(obj, "OrderDate")
        and hasattr(obj, "OrderTime")
        and hasattr(obj, "OrderQty")
        and hasattr(obj, "SeqNo")
    ):
        return real_report_to_dict(obj)
    if ("stkorder" in name and "ovstkorder" not in name) or (
        "ovstkorder" not in name
        and hasattr(obj, "OrderNo")
        and hasattr(obj, "CompanyNo")
        and hasattr(obj, "StkName")
        and hasattr(obj, "AcceptDate")
        and hasattr(obj, "AfterQty")
        and not hasattr(obj, "SPrice")
    ):
        return stk_order_to_dict(obj)
    if ("stktrade" in name and "ovstktrade" not in name) or (
        "ovstktrade" not in name
        and hasattr(obj, "OrderNo")
        and hasattr(obj, "SPrice")
        and hasattr(obj, "OPrice")
        and hasattr(obj, "OkQty")
    ):
        return stk_trade_to_dict(obj)

    # Date/time helpers used by the official examples.
    has_date = hasattr(obj, "ushtYear") or (
        hasattr(obj, "Year") and hasattr(obj, "Month") and hasattr(obj, "Day")
    )
    has_time = hasattr(obj, "bytHour") or (
        hasattr(obj, "Hour") and hasattr(obj, "Minute") and hasattr(obj, "Second")
    )
    if has_date and has_time:
        return yuanta_datetime_to_dict(obj)
    if has_date:
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
                except Exception as exc:
                    logger.warning(
                        "Failed to serialize property %s on %s: %s",
                        prop_name,
                        name,
                        exc,
                    )
                    result[_snake(prop_name)] = None
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
        except Exception as exc:
            logger.warning(
                "Failed to serialize attribute %s on %s: %s",
                attr,
                name,
                exc,
            )
            result[_snake(attr)] = None
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


# ---------------------------------------------------------------------------
# M3 read-only query serializers
# ---------------------------------------------------------------------------


def _json_scalar(value: Any) -> Any:
    """Keep JSON primitives and stringify SDK scalar values such as enums."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Get an attribute while allowing pythonnet to raise on missing props."""
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def stk_store_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkStore`` (domestic stock inventory) object."""
    return {
        "account": _get_attr(obj, "Account"),
        "trade_kind": _get_attr(obj, "TradeKind"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "market_name": _get_attr(obj, "MarketName"),
        "stk_code": _get_attr(obj, "StkCode"),
        "stk_name": _get_attr(obj, "StkName"),
        "stock_qty": _get_attr(obj, "StockQty"),
        "price": _get_attr(obj, "Price"),
        "cost": _get_attr(obj, "Cost"),
        "interest": _get_attr(obj, "Interest"),
        "buy_not_in_nos": _get_attr(obj, "BuyNotInNos"),
        "sell_not_in_nos": _get_attr(obj, "SellNotInNos"),
        "trading_qty": _get_attr(obj, "TradingQty"),
        "loan": _get_attr(obj, "Loan"),
        "tax_rate": _get_attr(obj, "TaxRate"),
        "lot_size": _get_attr(obj, "LotSize"),
        "market_price": _get_attr(obj, "MarketPrice"),
        "decimal": _get_attr(obj, "Decimal"),
        "stk_type1": _get_attr(obj, "StkType1"),
        "stk_type2": _get_attr(obj, "StkType2"),
        "buy_price": _get_attr(obj, "BuyPrice"),
        "sell_price": _get_attr(obj, "SellPrice"),
        "up_stop_price": _get_attr(obj, "UpStopPrice"),
        "down_stop_price": _get_attr(obj, "DownStopPrice"),
        "price_multiplier": _get_attr(obj, "PriceMultiplier"),
        "currency_type": _get_attr(obj, "CurrencyType"),
        "cdqty": _get_attr(obj, "CDQTY"),
        "odd_trading_qty": _get_attr(obj, "OddTradingQty"),
        "return_amt": _get_attr(obj, "ReturnAmt"),
        "market_amt": _get_attr(obj, "MarketAmt"),
    }


def ov_stk_store_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize an ``OVStkStore`` (overseas stock inventory) object."""
    return {
        "account": _get_attr(obj, "Account"),
        "currency_type": _get_attr(obj, "CurrencyType"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "market_name": _get_attr(obj, "MarketName"),
        "stk_code": _get_attr(obj, "StkCode"),
        "stk_name": _get_attr(obj, "StkName"),
        "stk_full_name": _get_attr(obj, "StkFullName"),
        "stock_qty": _get_attr(obj, "StockQty"),
        "trading_qty": _get_attr(obj, "TradingQty"),
        "price": _get_attr(obj, "Price"),
        "cost": _get_attr(obj, "Cost"),
        "close_rate": _get_attr(obj, "CloseRate"),
        "rate_kind": _get_attr(obj, "RateKind"),
        "lot_size": _get_attr(obj, "LotSize"),
        "market_price": _get_attr(obj, "MarketPrice"),
        "decimal": _get_attr(obj, "Decimal"),
        "buy_price": _get_attr(obj, "BuyPrice"),
        "sell_price": _get_attr(obj, "SellPrice"),
    }


def store_summary_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StoreSummaryResult`` object."""
    return {
        "stk_store_list": to_list(_get_attr(obj, "StkStoreList")),
        "ov_stk_store_list": to_list(_get_attr(obj, "OVStkStoreList")),
    }


def bank_balance_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``BankBalance`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "response_time": _get_attr(obj, "ResponseTime"),
        "bank_account": _get_attr(obj, "BankAccount"),
        "available_balance": _get_attr(obj, "AvailableBalance"),
        "message": _get_attr(obj, "Message"),
    }


def bank_balance_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``BankBalanceResult`` object."""
    return {"bank_balance_list": to_list(_get_attr(obj, "BankBalanceList"))}


def transaction_outlay_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``TransactionOutlay`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "settlement_day": _get_attr(obj, "SettlementDay"),
        "settlement_amt": _get_attr(obj, "SettlementAmt"),
    }


def transaction_outlay_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``TransactionOutlayResult`` object."""
    return {"transaction_outlay_list": to_list(_get_attr(obj, "TransactionOutlayList"))}


def unrealized_gain_loss_detail_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize an ``UnGainLossDetail`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "trade_kind": _get_attr(obj, "TradeKind"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "stk_code": _get_attr(obj, "StkCode"),
        "stock_qty": _get_attr(obj, "StockQty"),
        "price": _get_attr(obj, "Price"),
        "trade_date": _get_attr(obj, "TradeDate"),
        "cost": _get_attr(obj, "Cost"),
        "interest": _get_attr(obj, "Interest"),
        "return_amt": _get_attr(obj, "ReturnAmt"),
        "market_amt": _get_attr(obj, "MarketAmt"),
    }


def unrealized_gain_loss_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize an ``UnGainLossDetailResult`` object."""
    return {"un_gain_loss_detail_list": to_list(_get_attr(obj, "UnGainLossDetailList"))}


def realized_gain_loss_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``RealizedGainLoss`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "stk_code": _get_attr(obj, "StkCode"),
        "trade_date": _get_attr(obj, "TradeDate"),
        "trade_kind": _get_attr(obj, "TradeKind"),
        "price": _get_attr(obj, "Price"),
        "qty": _get_attr(obj, "Qty"),
        "profit_loss": _get_attr(obj, "ProfitLoss"),
        "order_no": _get_attr(obj, "OrderNo"),
        "term_split": _get_attr(obj, "TermSplit"),
        "term_ext": _get_attr(obj, "TermExt"),
        "charge": _get_attr(obj, "Charge"),
        "cost": _get_attr(obj, "Cost"),
        "tax": _get_attr(obj, "Tax"),
        "total_amt": _get_attr(obj, "TotalAMT"),
    }


def realized_gain_loss_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``RealizedGainLossResult`` object."""
    return {"realized_gain_loss_list": to_list(_get_attr(obj, "RealizedGainLossList"))}


def reversal_report_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``ReversalReport`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "reversal_date": _get_attr(obj, "ReversalDate"),
        "reversal_price": _get_attr(obj, "ReversalPrice"),
        "reversal_qty": _get_attr(obj, "ReversalQty"),
        "gl_amt": _get_attr(obj, "GlAmt"),
    }


def reversal_report_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``ReversalReportResult`` object."""
    return {"reversal_report_list": to_list(_get_attr(obj, "ReversalReportList"))}


def real_report_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``RealReport`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "rpt_type": _get_attr(obj, "RptType"),
        "order_no": _get_attr(obj, "OrderNo"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "company_no": _get_attr(obj, "CompanyNo"),
        "stk_c_name": _get_attr(obj, "StkCName"),
        "order_date": to_dict(_get_attr(obj, "OrderDate")),
        "order_time": to_dict(_get_attr(obj, "OrderTime")),
        "order_type": _get_attr(obj, "OrderType"),
        "bs": _get_attr(obj, "BS"),
        "price": _get_attr(obj, "Price"),
        "touch_price": _get_attr(obj, "TouchPrice"),
        "before_qty": _get_attr(obj, "BeforeQty"),
        "order_qty": _get_attr(obj, "OrderQty"),
        "open_offset_kind": _get_attr(obj, "OpenOffsetKind"),
        "day_trade": _get_attr(obj, "DayTrade"),
        "order_cond": _get_attr(obj, "OrderCond"),
        "order_error_no": _get_attr(obj, "OrderErrorNo"),
        "trade_kind": _get_attr(obj, "TradeKind"),
        "ap_code": _get_attr(obj, "APCode"),
        "basket_no": _get_attr(obj, "BasketNo"),
        "order_status": _get_attr(obj, "OrderStatus"),
        "stk_type1": _get_attr(obj, "StkType1"),
        "stk_type2": _get_attr(obj, "StkType2"),
        "belong_market_no": _get_attr(obj, "BelongMarketNo"),
        "belong_stk_code": _get_attr(obj, "BelongStkCode"),
        "seq_no": _get_attr(obj, "SeqNo"),
        "price_type": _get_attr(obj, "PriceType"),
        "stk_error_no": _get_attr(obj, "StkErrorNo"),
    }


def real_report_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``RealReportResult`` object."""
    return {"real_report_list": to_list(_get_attr(obj, "RealReportList"))}


def real_report_merge_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``RealReportMerge`` object."""
    return {
        "account": _get_attr(obj, "Account"),
        "rpt_type": _get_attr(obj, "RptType"),
        "order_no": _get_attr(obj, "OrderNo"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "company_no": _get_attr(obj, "CompanyNo"),
        "order_date": to_dict(_get_attr(obj, "OrderDate")),
        "order_time": to_dict(_get_attr(obj, "OrderTime")),
        "order_type": _get_attr(obj, "OrderType"),
        "bs": _get_attr(obj, "BS"),
        "price": _get_attr(obj, "Price"),
        "touch_price": _get_attr(obj, "TouchPrice"),
        "last_deal_price": _get_attr(obj, "LastDealPrice"),
        "avg_deal_price": _get_attr(obj, "AvgDealPrice"),
        "before_qty": _get_attr(obj, "BeforeQty"),
        "order_qty": _get_attr(obj, "OrderQty"),
        "ok_qty": _get_attr(obj, "OkQty"),
        "open_offset_kind": _get_attr(obj, "OpenOffsetKind"),
        "day_trade": _get_attr(obj, "DayTrade"),
        "order_cond": _get_attr(obj, "OrderCond"),
        "order_error_no": _get_attr(obj, "OrderErrorNo"),
        "ap_code": _get_attr(obj, "APCode"),
        "order_status": _get_attr(obj, "OrderStatus"),
        "last_order_status": _get_attr(obj, "LastOrderStatus"),
        "stk_c_name": _get_attr(obj, "StkCName"),
        "trade_code": _get_attr(obj, "TradeCode"),
        "strike_price": _get_attr(obj, "StrikePrice"),
        "basket_no": _get_attr(obj, "BasketNo"),
        "stk_type1": _get_attr(obj, "StkType1"),
        "stk_type2": _get_attr(obj, "StkType2"),
        "belong_market_no": _get_attr(obj, "BelongMarketNo"),
        "belong_stk_code": _get_attr(obj, "BelongStkCode"),
        "stk_type": _get_attr(obj, "StkType"),
        "stk_error_no": _get_attr(obj, "StkErrorNo"),
    }


def real_report_merge_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``RealReportMergeResult`` object."""
    return {"real_report_merge_list": to_list(_get_attr(obj, "RealReportMergeList"))}


def stk_order_data_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkOrderData`` (SendStockOrder response row) object."""
    return {
        "identify": _get_attr(obj, "Identify"),
        "reply_code": _get_attr(obj, "ReplyCode"),
        "order_no": _get_attr(obj, "OrderNO"),
        "trade_date": to_dict(_get_attr(obj, "TradeDate")),
        "err_type": _get_attr(obj, "ErrType"),
        "err_no": _get_attr(obj, "ErrNO"),
        "advisory": _get_attr(obj, "Advisory"),
    }


def stk_order_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkOrderResult`` (SendStockOrder response) object."""
    return {
        "result_count": status_to_dict(_get_attr(obj, "ResultCount")),
        "result_list": to_list(_get_attr(obj, "ResultList")),
    }


def stk_order_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkOrder`` (domestic stock order) object."""
    return {
        "account": _get_attr(obj, "Account"),
        "trade_date": to_dict(_get_attr(obj, "TradeDate")),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "market_name": _get_attr(obj, "MarketName"),
        "company_no": _get_attr(obj, "CompanyNo"),
        "stk_name": _get_attr(obj, "StkName"),
        "order_type": _get_attr(obj, "OrderType"),
        "bs": _get_attr(obj, "BS"),
        "price": _get_attr(obj, "Price"),
        "price_flag": _get_attr(obj, "PriceFlag"),
        "before_qty": _get_attr(obj, "BeforeQty"),
        "after_qty": _get_attr(obj, "AfterQty"),
        "ok_qty": _get_attr(obj, "OkQty"),
        "order_status": _get_attr(obj, "OrderStatus"),
        "accept_date": to_dict(_get_attr(obj, "AcceptDate")),
        "accept_time": to_dict(_get_attr(obj, "AcceptTime")),
        "order_no": _get_attr(obj, "OrderNo"),
        "error_no": _get_attr(obj, "ErrorNo"),
        "error_message": _get_attr(obj, "ErrorMessage"),
        "seller": _get_attr(obj, "Seller"),
        "channel": _get_attr(obj, "Channel"),
        "ap_code": _get_attr(obj, "APCode"),
        "otax": _get_attr(obj, "OTax"),
        "ocharge": _get_attr(obj, "OCharge"),
        "odue_amt": _get_attr(obj, "ODueAmt"),
        "cancel_flag": _get_attr(obj, "CancelFlag"),
        "reduce_flag": _get_attr(obj, "ReduceFlag"),
        "tradition_flag": _get_attr(obj, "TraditionFlag"),
        "basket_no": _get_attr(obj, "BasketNo"),
        "trade_currency": _get_attr(obj, "TradeCurrency"),
        "time_in_force": _get_attr(obj, "Time_in_Force"),
        "order_success": _get_attr(obj, "Order_Success"),
        "reduce_flag2": _get_attr(obj, "Reduce_Flag"),
        "chg_prz_flag": _get_attr(obj, "Chg_Prz_Flag"),
        "tse_cancel": _get_attr(obj, "TSE_Cancel"),
        "cancel_qty": _get_attr(obj, "CancelQty"),
        "or_qty": _get_attr(obj, "OR_QTY"),
        "update_date": to_dict(_get_attr(obj, "UpdateDate")),
        "update_time": to_dict(_get_attr(obj, "UpdateTime")),
    }


def stk_trade_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkTrade`` (domestic stock trade) object."""
    return {
        "account": _get_attr(obj, "Account"),
        "market_no": to_dict(_get_attr(obj, "MarketNo")),
        "market_name": _get_attr(obj, "MarketName"),
        "company_no": _get_attr(obj, "CompanyNo"),
        "stk_name": _get_attr(obj, "StkName"),
        "order_type": _get_attr(obj, "OrderType"),
        "bs": _get_attr(obj, "BS"),
        "ok_qty": _get_attr(obj, "OkQty"),
        "o_price": _get_attr(obj, "OPrice"),
        "s_price": _get_attr(obj, "SPrice"),
        "date_time": to_dict(_get_attr(obj, "DateTime")),
        "order_no": _get_attr(obj, "OrderNo"),
        "trade_currency": _get_attr(obj, "TradeCurrency"),
        "price_flag": _get_attr(obj, "Price_Flag"),
        "exchange_code": _get_attr(obj, "Exchange_Code"),
    }


def order_trade_report_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize an ``OrderTradeReportResult`` object."""
    return {
        "stk_order_list": to_list(_get_attr(obj, "StkOrderList")),
        "stk_trade_list": to_list(_get_attr(obj, "StkTradeList")),
        "fut_order_list": to_list(_get_attr(obj, "FutOrderList")),
        "fut_trade_list": to_list(_get_attr(obj, "FutTradeList")),
        "ov_stk_order_list": to_list(_get_attr(obj, "OVStkOrderList")),
        "ov_stk_trade_list": to_list(_get_attr(obj, "OVStkTradeList")),
        "ov_fut_order_list": to_list(_get_attr(obj, "OVFutOrderList")),
        "ov_fut_trade_list": to_list(_get_attr(obj, "OVFutTradeList")),
    }


# Friendly aliases used in service/tests.
serialize_store_summary = store_summary_result_to_dict
serialize_bank_balance = bank_balance_result_to_dict
serialize_transaction_outlay = transaction_outlay_result_to_dict
serialize_unrealized_gain_loss = unrealized_gain_loss_result_to_dict
serialize_realized_gain_loss = realized_gain_loss_result_to_dict
serialize_reversal_report = reversal_report_result_to_dict
serialize_real_report = real_report_result_to_dict
serialize_real_report_merge = real_report_merge_result_to_dict
serialize_stk_order_result = stk_order_result_to_dict
serialize_stk_order_data = stk_order_data_to_dict
serialize_order_trade_report = order_trade_report_result_to_dict


# Common short aliases.
store_summary_to_dict = store_summary_result_to_dict
unrealized_gain_loss_to_dict = unrealized_gain_loss_result_to_dict
order_trade_report_to_dict = order_trade_report_result_to_dict

# ---------------------------------------------------------------------------
# M5 quote subscription / query serializers
# ---------------------------------------------------------------------------


def watch_list_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``WatchListResult`` subscription event."""
    return {
        "key": _get_attr(obj, "Key"),
        "market_type": _get_attr(obj, "MarketType"),
        "stk_code": _get_attr(obj, "StkCode"),
        "index_flag": _get_attr(obj, "IndexFlag"),
        "value": _get_attr(obj, "Value"),
    }


def watch_list_all_flag_22_to_dict(obj: Any) -> dict[str, Any]:
    return {"buy_vol": _get_attr(obj, "BuyVol"), "sell_vol": _get_attr(obj, "SellVol")}


def watch_list_all_flag_28_to_dict(obj: Any) -> dict[str, Any]:
    return {"buy_price": _get_attr(obj, "BuyPrice"), "sell_price": _get_attr(obj, "SellPrice")}


def watch_list_all_flag_29_to_dict(obj: Any) -> dict[str, Any]:
    return {
        "time": to_dict(_get_attr(obj, "Time")),
        "total_out_vol": _get_attr(obj, "TotalOutVol"),
        "total_in_vol": _get_attr(obj, "TotalInVol"),
        "deal": _get_attr(obj, "Deal"),
        "vol": _get_attr(obj, "Vol"),
        "total_vol": _get_attr(obj, "TotalVol"),
        "total_amt": _get_attr(obj, "TotalAmt"),
    }


def watch_list_all_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``WatchListAllResult`` subscription event."""
    result = {
        "key": _get_attr(obj, "Key"),
        "market_type": _get_attr(obj, "MarketType"),
        "stk_code": _get_attr(obj, "StkCode"),
        "seq_no": _get_attr(obj, "SeqNo"),
        "index_flag": _get_attr(obj, "IndexFlag"),
        "value": _get_attr(obj, "Value"),
    }
    if _get_attr(obj, "IndexFlag_22") is not None:
        result["index_flag_22"] = watch_list_all_flag_22_to_dict(_get_attr(obj, "IndexFlag_22"))
    if _get_attr(obj, "IndexFlag_28") is not None:
        result["index_flag_28"] = watch_list_all_flag_28_to_dict(_get_attr(obj, "IndexFlag_28"))
    if _get_attr(obj, "IndexFlag_29") is not None:
        result["index_flag_29"] = watch_list_all_flag_29_to_dict(_get_attr(obj, "IndexFlag_29"))
    return result


def five_tick_a_flag_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a FiveTickA flag payload (20/21/42/43/50/51)."""
    candidates = {
        "price1": "Price1",
        "price2": "Price2",
        "price3": "Price3",
        "price4": "Price4",
        "price5": "Price5",
        "vol1": "Vol1",
        "vol2": "Vol2",
        "vol3": "Vol3",
        "vol4": "Vol4",
        "vol5": "Vol5",
        "buy_price1": "BuyPrice1",
        "buy_price2": "BuyPrice2",
        "buy_price3": "BuyPrice3",
        "buy_price4": "BuyPrice4",
        "buy_price5": "BuyPrice5",
        "buy_vol1": "BuyVol1",
        "buy_vol2": "BuyVol2",
        "buy_vol3": "BuyVol3",
        "buy_vol4": "BuyVol4",
        "buy_vol5": "BuyVol5",
        "sell_price1": "SellPrice1",
        "sell_price2": "SellPrice2",
        "sell_price3": "SellPrice3",
        "sell_price4": "SellPrice4",
        "sell_price5": "SellPrice5",
        "sell_vol1": "SellVol1",
        "sell_vol2": "SellVol2",
        "sell_vol3": "SellVol3",
        "sell_vol4": "SellVol4",
        "sell_vol5": "SellVol5",
    }
    return {
        key: _get_attr(obj, attr)
        for key, attr in candidates.items()
        if _get_attr(obj, attr) is not None
    }


def five_tick_a_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``FiveTickAResult`` subscription event."""
    result = {
        "key": _get_attr(obj, "Key"),
        "market_type": _get_attr(obj, "MarketType"),
        "stk_code": _get_attr(obj, "StkCode"),
        "index_flag": _get_attr(obj, "IndexFlag"),
        "value": _get_attr(obj, "Value"),
    }
    for flag_name in ("IndexFlag_20", "IndexFlag_21", "IndexFlag_42", "IndexFlag_43", "IndexFlag_50", "IndexFlag_51"):
        flag = _get_attr(obj, flag_name)
        if flag is not None:
            suffix = flag_name.split("_")[-1]
            result[f"index_flag_{suffix}"] = five_tick_a_flag_to_dict(flag)
    return result


def stock_tick_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StockTickResult`` subscription event."""
    return {
        "key": _get_attr(obj, "Key"),
        "market_type": _get_attr(obj, "MarketType"),
        "stk_code": _get_attr(obj, "StkCode"),
        "serial_no": _get_attr(obj, "SerialNo"),
        "time": to_dict(_get_attr(obj, "Time")),
        "buy_price": _get_attr(obj, "BuyPrice"),
        "sell_price": _get_attr(obj, "SellPrice"),
        "deal_price": _get_attr(obj, "DealPrice"),
        "deal_vol": _get_attr(obj, "DealVol"),
        "in_out_flag": _get_attr(obj, "InOutFlag"),
        "type": _get_attr(obj, "Type"),
    }


def market_info_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``MarketInfoResult`` subscription event."""
    return {
        "key": _get_attr(obj, "Key"),
        "market_type": _get_attr(obj, "MarketType"),
        "stk_code": _get_attr(obj, "StkCode"),
        "deal_price": _get_attr(obj, "DealPrice"),
        "tick_vol": _get_attr(obj, "TickVol"),
        "time": to_dict(_get_attr(obj, "Time")),
        "trade_status": _get_attr(obj, "TradeStatus"),
    }


def stock_other_info_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StockOtherInfoResult`` subscription event."""
    return {
        "key": _get_attr(obj, "Key"),
        "market_type": _get_attr(obj, "MarketType"),
        "stk_code": _get_attr(obj, "StkCode"),
        "index_flag": _get_attr(obj, "IndexFlag"),
        "trade_time": to_dict(_get_attr(obj, "TradeTime")),
    }


def stk_information_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkInformation`` stock info row."""
    return {
        "market_no": _json_scalar(_get_attr(obj, "MarketNo")),
        "stock_code": _get_attr(obj, "StockCode"),
        "dayoffmark": _get_attr(obj, "Dayoffmark"),
        "creditpercent": _get_attr(obj, "Creditpercent"),
        "lendpercent": _get_attr(obj, "Lendpercent"),
        "creditremnants": _get_attr(obj, "Creditremnants"),
        "lendremnants": _get_attr(obj, "Lendremnants"),
        "lend_sell_mark": _get_attr(obj, "LendSellMark"),
        "recall_date": _get_attr(obj, "RecallDate"),
        "lend_qty": _get_attr(obj, "LendQty"),
        "stock_warning": to_list(_get_attr(obj, "StockWarning")),
        "update_date": _get_attr(obj, "UpdateDate"),
    }


def stk_information_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkInformationResult`` query result."""
    return {"stock_information_list": to_list(_get_attr(obj, "StockInformationList"))}


def stick_detail_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StickDetail`` tick row."""
    return {
        "time_stamp": to_dict(_get_attr(obj, "TimeStamp")),
        "deal_price": _get_attr(obj, "DealPrice"),
        "deal_vol": _get_attr(obj, "DealVol"),
        "buy_price": _get_attr(obj, "BuyPrice"),
        "sell_price": _get_attr(obj, "SellPrice"),
        "seq_no": _get_attr(obj, "SeqNo"),
        "in_out_flag": _get_attr(obj, "InOutFlag"),
    }


def stick_detail_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StickDetailResult`` query result."""
    return {
        "market_no": _json_scalar(_get_attr(obj, "MarketNo")),
        "stock_code": _get_attr(obj, "StockCode"),
        "stick_detail_list": to_list(_get_attr(obj, "StickDetailList")),
    }


def classify_price_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``ClassifyPrice`` row."""
    return {
        "price": _get_attr(obj, "Price"),
        "in_deal_vol": _get_attr(obj, "InDealVol"),
        "out_deal_vol": _get_attr(obj, "OutDealVol"),
        "total_deal_vol": _get_attr(obj, "TotalDealVol"),
    }


def stk_classify_price_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``StkClassifyPriceResult`` query result."""
    return {
        "date": _get_attr(obj, "Date"),
        "market_no": _json_scalar(_get_attr(obj, "MarketNo")),
        "stock_code": _get_attr(obj, "StockCode"),
        "classify_price_list": to_list(_get_attr(obj, "ClassifyPriceList")),
    }


def k_line_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``KLine`` row."""
    return {
        "time_stamp": to_dict(_get_attr(obj, "TimeStamp")),
        "open_price": _get_attr(obj, "OpenPrice"),
        "high_price": _get_attr(obj, "HighPrice"),
        "low_price": _get_attr(obj, "LowPrice"),
        "close_price": _get_attr(obj, "ClosePrice"),
        "deal_vol": _get_attr(obj, "DealVol"),
    }


def k_line_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``KLineResult`` query result."""
    return {
        "market_no": _json_scalar(_get_attr(obj, "MarketNo")),
        "stock_code": _get_attr(obj, "StockCode"),
        "k_line_list": to_list(_get_attr(obj, "KLineList")),
    }


def query_watch_list_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``QueryWatchList`` snapshot row."""
    return {
        "market_no": _get_attr(obj, "MarketNo"),
        "stk_code": _get_attr(obj, "StkCode"),
        "stk_name": _get_attr(obj, "StkName"),
        "yst_price": _get_attr(obj, "YstPrice"),
        "open_ref_price": _get_attr(obj, "OpenRefPrice"),
        "up_stop_price": _get_attr(obj, "UpStopPrice"),
        "down_stop_price": _get_attr(obj, "DownStopPrice"),
        "yst_vol": _get_attr(obj, "YstVol"),
        "ext_name": _get_attr(obj, "ExtName"),
        "decimal": _get_attr(obj, "Decimal"),
        "credit_percent": _get_attr(obj, "CreditPercent"),
        "len_bond_percent": _get_attr(obj, "LenBondPercent"),
        "open_price": _get_attr(obj, "OpenPrice"),
        "high_price": _get_attr(obj, "HighPrice"),
        "low_price": _get_attr(obj, "LowPrice"),
        "buy_price": _get_attr(obj, "BuyPrice"),
        "total_out_vol": _get_attr(obj, "TotalOutVol"),
        "sell_price": _get_attr(obj, "SellPrice"),
        "total_in_vol": _get_attr(obj, "TotalInVol"),
        "deal_price": _get_attr(obj, "DealPrice"),
        "total_deal_amt": _get_attr(obj, "TotalDealAmt"),
        "vol_flag": _get_attr(obj, "VolFlag"),
        "vol": _get_attr(obj, "Vol"),
        "total_vol": _get_attr(obj, "TotalVol"),
        "fixed_price_vol": _get_attr(obj, "FixedPriceVol"),
        "reserve_vol": _get_attr(obj, "ReserveVol"),
        "settlement_price": _get_attr(obj, "SettlementPrice"),
        "hi_contract_price": _get_attr(obj, "HiContractPrice"),
        "lo_contract_price": _get_attr(obj, "LoContractPrice"),
        "order_buy_count": _get_attr(obj, "OrderBuyCount"),
        "order_buy_qty": _get_attr(obj, "OrderBuyQty"),
        "order_sell_count": _get_attr(obj, "OrderSellCount"),
        "order_sell_qty": _get_attr(obj, "OrderSellQty"),
        "deal_buy_count": _get_attr(obj, "DealBuyCount"),
        "deal_sell_count": _get_attr(obj, "DealSellCount"),
        "volatility": _get_attr(obj, "Volatility"),
        "time": to_dict(_get_attr(obj, "Time")),
        "time_diff": _get_attr(obj, "TimeDiff"),
        "stk_type2": _get_attr(obj, "StkType2"),
        "reserve_vol_diff": _get_attr(obj, "ReserveVolDiff"),
        "belong_code": _get_attr(obj, "BelongCode"),
        "industry_name": _get_attr(obj, "IndustryName"),
        "principal_percent": _get_attr(obj, "PrincipalPercent"),
        "up_down_day": _get_attr(obj, "UpDownDay"),
        "bid_qty": _get_attr(obj, "BidQty"),
        "ask_qty": _get_attr(obj, "AskQty"),
        "price_trends": _get_attr(obj, "PriceTrends"),
        "est_deal_price": _get_attr(obj, "EstDealPrice"),
        "est_deal_vol": _get_attr(obj, "EstDealVol"),
        "est_deal_vol_flag": _get_attr(obj, "EstDealVolFlag"),
    }


def query_watch_list_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``QueryWatchListResult`` query result."""
    return {"query_watch_list": to_list(_get_attr(obj, "QueryWatchList"))}


def sub_quote_list_result_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a ``SubQuoteListResult`` (GetQuoteList) result."""
    return {
        "account": _get_attr(obj, "Account"),
        "quote_list": to_list(_get_attr(obj, "QuoteList")),
    }


# Friendly aliases.
serialize_watch_list = watch_list_result_to_dict
serialize_watch_list_all = watch_list_all_result_to_dict
serialize_five_tick_a = five_tick_a_result_to_dict
serialize_stock_tick = stock_tick_result_to_dict
serialize_market_info = market_info_result_to_dict
serialize_stock_other_info = stock_other_info_result_to_dict
serialize_stk_information = stk_information_result_to_dict
serialize_stick_detail = stick_detail_result_to_dict
serialize_stk_classify_price = stk_classify_price_result_to_dict
serialize_k_line = k_line_result_to_dict

# Common short aliases used by callers/tests.
watchlist_result_to_dict = watch_list_result_to_dict
watchlist_all_result_to_dict = watch_list_all_result_to_dict
fivetick_a_result_to_dict = five_tick_a_result_to_dict
stocktick_result_to_dict = stock_tick_result_to_dict
marketinfo_result_to_dict = market_info_result_to_dict
stockotherinfo_result_to_dict = stock_other_info_result_to_dict
stkinformation_result_to_dict = stk_information_result_to_dict
stickdetail_result_to_dict = stick_detail_result_to_dict
stkclassifyprice_result_to_dict = stk_classify_price_result_to_dict
kline_result_to_dict = k_line_result_to_dict
querywatchlist_result_to_dict = query_watch_list_result_to_dict
