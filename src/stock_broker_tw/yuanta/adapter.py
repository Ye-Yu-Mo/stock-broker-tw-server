"""High-level Python wrapper around ``YuantaSparkAPITrader``.

The adapter owns the .NET trader object, registers ``OnResponse`` once, and
forwards every raw event to a thread-safe :class:`EventQueue`.  Business code
should use this class instead of touching pythonnet directly.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Self

from stock_broker_tw.yuanta import loader
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent
from stock_broker_tw.yuanta.serializer import login_result_to_dict, to_dict

logger = logging.getLogger(__name__)


class YuantaAdapterError(RuntimeError):
    """Raised when the adapter is used in an invalid lifecycle state."""


_UNMATCHED_RESPONSE = ""


class YuantaAdapter:
    """Encapsulate Open / Login / LogOut / Close / Dispose.

    Parameters
    ----------
    spark_api_dir:
        Directory containing ``YuantaSparkAPI.dll``.  Only used when ``trader``
        is not injected.
    environment:
        ``"UAT"`` or ``"PROD"``.
    log_type:
        Yuanta log type, e.g. ``"COMMON"``.
    pmm_server_check:
        Passed to ``SetPMMServerCheck``.
    trader:
        Optional injected trader object.  Used by tests and advanced callers to
        avoid loading the native .NET assembly.
    event_queue:
        Optional :class:`EventQueue`.  A new one is created when omitted.
    """

    def __init__(
        self,
        spark_api_dir: str | None = None,
        environment: str = "UAT",
        log_type: str = "COMMON",
        pmm_server_check: bool = False,
        trader: Any = None,
        event_queue: EventQueue | None = None,
    ) -> None:
        self._spark_api_dir = spark_api_dir
        self._environment = environment
        self._log_type = log_type
        self._pmm_server_check = pmm_server_check
        self._trader = trader
        self._event_queue = event_queue or EventQueue()
        self._opened = False
        self._logged_in = False
        self._closed = False
        self._disposed = False
        self._last_login_result: dict[str, Any] | None = None
        self._query_responses: dict[str, dict[str, list[Any]]] = {}
        self._query_cond = threading.Condition()

    @property
    def trader(self) -> Any:
        return self._trader

    @property
    def event_queue(self) -> EventQueue:
        return self._event_queue

    @property
    def opened(self) -> bool:
        return self._opened

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def disposed(self) -> bool:
        return self._disposed

    @property
    def last_login_result(self) -> dict[str, Any] | None:
        return self._last_login_result

    def reset_login_result(self) -> None:
        """Clear the cached login result before a new login attempt."""
        self._last_login_result = None

    def open(self) -> None:
        """Open the Yuanta API connection.

        The method is idempotent; calling it twice only opens once.
        """
        if self._disposed:
            raise YuantaAdapterError("adapter has been disposed")
        if self._opened:
            return

        logger.debug(
            "Yuanta Open() request: environment=%s log_type=%s pmm_server_check=%s",
            self._environment,
            self._log_type,
            self._pmm_server_check,
        )
        if self._trader is None:
            self._trader = loader.create_trader(
                environment=self._environment,
                log_type=self._log_type,
                pmm_server_check=self._pmm_server_check,
                spark_api_dir=self._spark_api_dir,
            )

        self._configure_trader()
        self._register_event_handler()
        mode = self._resolve_environment_mode()
        self._trader.Open(mode)
        self._opened = True
        self._closed = False
        logger.debug("Yuanta Open() completed: opened=%s", self._opened)

    def login(
        self,
        account: str,
        password: str,
        pfx_path: str | None = None,
        pfx_pass: str | None = None,
    ) -> bool:
        """Submit a login request.

        Returns the boolean returned by the Yuanta ``Login`` method (usually
        whether the request was accepted).  The actual login result arrives
        through the ``OnResponse`` event queue.
        """
        if not self._opened:
            raise YuantaAdapterError("must call open() before login")
        if self._logged_in:
            raise YuantaAdapterError("already logged in, please logout first")
        if self._trader is None:
            raise YuantaAdapterError("trader is not available")

        method = "pfx" if pfx_path else "password"
        pfx_name = Path(pfx_path).name if pfx_path else None
        logger.debug(
            "Yuanta Login() request: environment=%s method=%s account_present=%s pfx_name=%s",
            self._environment,
            method,
            bool(account),
            pfx_name,
        )
        try:
            if pfx_path:
                result = self._trader.Login(pfx_path, pfx_pass, account, password)
            else:
                result = self._trader.Login(account, password)
        except Exception as exc:
            logger.error(
                "Yuanta Login() raised: exception_type=%s",
                type(exc).__name__,
            )
            raise
        self._logged_in = bool(result)
        logger.debug(
            "Yuanta Login() result: accepted=%s opened=%s logged_in=%s",
            bool(result),
            self._opened,
            self._logged_in,
        )
        return bool(result)

    def logout(self) -> bool:
        """Log out from the Yuanta API.

        Calling logout when not logged in is safe; calling it before
        :meth:`open` is an error.
        """
        if not self._opened:
            raise YuantaAdapterError("must call open() before logout")
        if self._trader is None:
            raise YuantaAdapterError("trader is not available")
        result = self._trader.LogOut()
        self._logged_in = False
        return bool(result)

    def close(self) -> None:
        """Close the Yuanta API connection. Safe to call multiple times."""
        if self._closed:
            return
        if self._trader is not None:
            if self._logged_in:
                try:
                    self._trader.LogOut()
                except Exception:
                    pass
            self._trader.Close()
        self._opened = False
        self._logged_in = False
        self._closed = True

    def dispose(self) -> None:
        """Dispose the underlying .NET trader. Safe to call multiple times."""
        if self._disposed:
            return
        if self._opened:
            self.close()
        if self._trader is not None:
            self._trader.Dispose()
        self._disposed = True

    def _configure_trader(self) -> None:
        if self._trader is None:
            return
        set_log_type = getattr(self._trader, "SetLogType", None)
        if callable(set_log_type):
            try:
                set_log_type(self._log_type)
            except Exception:
                pass
        set_pmm = getattr(self._trader, "SetPMMServerCheck", None)
        if callable(set_pmm):
            try:
                set_pmm(self._pmm_server_check)
            except Exception:
                pass

    def _register_event_handler(self) -> None:
        if self._trader is None:
            return
        try:
            from YuantaOneAPI import OnResponseEventHandler

            handler: Any = OnResponseEventHandler(self._on_response)
        except Exception:
            handler = self._on_response
        if hasattr(self._trader, "OnResponse"):
            # pythonnet exposes .NET events as objects that support +=.  For
            # test fakes (and plain Python stand-ins) we accept a list too.
            if isinstance(self._trader.OnResponse, list):
                self._trader.OnResponse.append(handler)
            else:
                self._trader.OnResponse += handler

    def _resolve_environment_mode(self) -> Any:
        try:
            return loader.get_environment_mode(self._environment)
        except Exception:
            return self._environment

    def _on_response(
        self,
        int_mark: int,
        dw_index: int,
        str_index: str,
        obj_handle: Any,
        obj_value: Any,
    ) -> None:
        # Serialize query/trade payloads before putting the event on the queue
        # so the event can carry the correlation id used by concurrent waiters.
        response_id: str | None = None
        data: Any = None
        if (int_mark == 1 or str_index == "SendStockOrder") and str_index != "Login":
            try:
                data = to_dict(obj_value)
            except Exception:
                logger.exception("failed to serialize %s response", str_index)
                data = None
            if data is not None:
                response_id = self._extract_response_request_id(data)

        if str_index == "Login":
            logger.debug(
                "Login response received: int_mark=%s dw_index=%s",
                int_mark,
                dw_index,
            )
            try:
                login_data = login_result_to_dict(obj_value)
                self._last_login_result = login_data
                login_status = login_data.get("login_status") or {}
                logger.debug(
                    "Login response parsed: msg_code=%s msg_content_present=%s login_entries=%s",
                    login_status.get("msg_code"),
                    bool(login_status.get("msg_content")),
                    len(login_data.get("login_list") or []),
                )
                if login_data.get("login_list"):
                    self._logged_in = True
                else:
                    self._logged_in = False
            except Exception as exc:
                logger.error(
                    "failed to parse Login response: exception_type=%s",
                    type(exc).__name__,
                )

        event = YuantaEvent(
            int_mark=int_mark,
            dw_index=dw_index,
            str_index=str_index,
            obj_handle=obj_handle,
            obj_value=obj_value,
            request_id=response_id,
        )
        self._event_queue.put(event)

        # Query/trade responses are stored separately so ``query()`` and
        # ``send_stock_order()`` do not steal unrelated events from the shared
        # WebSocket/event queue.
        if data is not None:
            with self._query_cond:
                bucket = self._query_responses.setdefault(str_index, {})
                key = str(response_id) if response_id is not None else _UNMATCHED_RESPONSE
                bucket.setdefault(key, []).append(data)
                self._query_cond.notify_all()

    @staticmethod
    def _extract_response_request_id(data: Any) -> str | None:
        """Return the correlation id embedded in a serialized response.

        ``SendStockOrder`` echoes ``Identify``; some test/query payloads use a
        ``request_id`` key directly.  If neither is present the response is
        treated as unmatched and kept in the per-function pending bucket.
        """
        def _first_id(mapping: dict[str, Any]) -> str | None:
            for key in ("request_id", "RequestID", "identify", "Identify"):
                value = mapping.get(key)
                if value is not None:
                    return str(value)
            return None

        if isinstance(data, dict):
            found = _first_id(data)
            if found is not None:
                return found
            for list_key in ("result_list", "ResultList"):
                items = data.get(list_key)
                if isinstance(items, (list, tuple)):
                    for item in items:
                        if isinstance(item, dict):
                            found = _first_id(item)
                            if found is not None:
                                return found
        elif isinstance(data, (list, tuple)):
            for item in data:
                if isinstance(item, dict):
                    found = _first_id(item)
                    if found is not None:
                        return found
        return None

    def _take_response_locked(
        self,
        function_name: str,
        request_id: str | None,
    ) -> Any | None:
        bucket = self._query_responses.get(function_name)
        if not bucket:
            return None
        if request_id is not None:
            key = str(request_id)
            responses = bucket.get(key)
            if responses:
                return responses.pop(0)
            # If the Yuanta API does not echo a correlation id, fall back to the
            # unmatched bucket.  QueryService serializes same-function queries,
            # so this fallback is safe for normal service usage.
            unmatched = bucket.get(_UNMATCHED_RESPONSE)
            if unmatched:
                return unmatched.pop(0)
            return None
        responses = bucket.get(_UNMATCHED_RESPONSE)
        if responses:
            return responses.pop(0)
        # A no-request_id caller should not steal request-specific responses.
        return None

    def send_stock_order(
        self,
        account: str,
        orders: Any,
        timeout: float = 10.0,
        request_id: str | None = None,
    ) -> Any:
        """Send one or more domestic stock orders and wait for the response.

        ``orders`` may be a dict or a list of dicts.  When the real .NET
        assembly is available the dicts are converted to ``StockOrder`` objects;
        test fakes may receive the plain dict/list.
        """
        if self._trader is None:
            raise YuantaAdapterError("trader is not available")
        method = getattr(self._trader, "SendStockOrder", None)
        if not callable(method):
            raise YuantaAdapterError("unknown Yuanta function: SendStockOrder")

        payload = self._build_stock_order_payload(orders)
        try:
            accepted = method(account, payload)
        except TypeError:
            # Some bindings/signatures expect a third lng argument.
            accepted = method(account, payload, 0)
        except Exception as exc:
            raise YuantaAdapterError(f"SendStockOrder call failed: {exc}") from exc
        if not accepted:
            raise YuantaAdapterError("SendStockOrder was rejected")

        deadline = time.monotonic() + timeout
        with self._query_cond:
            while True:
                response = self._take_response_locked(
                    "SendStockOrder", request_id
                )
                if response is not None:
                    return response

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    request_suffix = f" request_id={request_id}" if request_id else ""
                    raise TimeoutError(
                        f"timed out after {timeout:.1f}s waiting for "
                        f"SendStockOrder response{request_suffix}"
                    )
                self._query_cond.wait(remaining)

    @staticmethod
    def _build_stock_order_payload(orders: Any) -> Any:
        """Convert plain dicts to a .NET ``List[StockOrder]`` when possible."""
        if isinstance(orders, dict):
            orders = [orders]
        elif hasattr(orders, "to_dict") and callable(orders.to_dict):
            orders = [orders.to_dict()]
        if isinstance(orders, (list, tuple)):
            try:

                from System.Collections.Generic import List
                from YuantaOneAPI import StockOrder

                result = List[StockOrder]()
                for raw_item in orders:
                    item = raw_item.to_dict() if hasattr(raw_item, "to_dict") else raw_item
                    so = StockOrder()
                    for key, value in item.items():
                        attr = {
                            "order_no": "OrderNo",
                            "trade_date": "TradeDate",
                            "ap_code": "APCode",
                            "trade_kind": "TradeKind",
                            "order_type": "OrderType",
                            "stk_code": "StkCode",
                            "buy_sell": "BuySell",
                            "price_flag": "PriceFlag",
                            "price": "Price",
                            "basket_no": "BasketNo",
                            "order_qty": "OrderQty",
                            "time_in_force": "Time_in_force",
                            "identify": "Identify",
                            "account": "Account",
                        }.get(str(key), str(key))
                        if hasattr(so, attr):
                            setattr(so, attr, value)
                    result.Add(so)
                return result
            except Exception:
                return list(orders)
        return orders

    def subscribe(
        self,
        function_name: str,
        account: str,
        symbols: Any,
    ) -> bool:
        """Submit a Yuanta subscription request.

        The actual subscription events arrive through ``OnResponse``; this
        method only verifies that the call was accepted.
        """
        return self._call_subscription(function_name, account, symbols)

    def unsubscribe(
        self,
        function_name: str,
        account: str,
        symbols: Any,
    ) -> bool:
        """Submit a Yuanta unsubscription request."""
        return self._call_subscription(function_name, account, symbols)

    def _call_subscription(
        self,
        function_name: str,
        account: str,
        symbols: Any,
    ) -> bool:
        if self._trader is None:
            raise YuantaAdapterError("trader is not available")
        method = getattr(self._trader, function_name, None)
        if not callable(method):
            raise YuantaAdapterError(f"unknown Yuanta function: {function_name}")

        payload = self._build_subscription_payload(function_name, symbols)
        try:
            accepted = method(account, payload)
        except TypeError:
            accepted = method(account, payload, 0)
        except Exception as exc:
            raise YuantaAdapterError(f"{function_name} call failed: {exc}") from exc
        if not accepted:
            raise YuantaAdapterError(f"{function_name} was rejected")
        return True

    @staticmethod
    def _build_subscription_payload(function_name: str, symbols: Any) -> Any:
        """Convert plain dicts to Yuanta .NET subscription objects when possible."""
        if symbols is None:
            symbols = []
        if isinstance(symbols, dict):
            symbols = [symbols]
        elif hasattr(symbols, "to_dict") and callable(symbols.to_dict):
            symbols = [symbols.to_dict()]
        if not isinstance(symbols, (list, tuple)):
            return symbols

        stock_attr = {"market_type": "MarketType", "stk_code": "StockCode", "stock_code": "StockCode"}
        class_map = {
            "SubscribeWatchlist": ("Watchlist", {**stock_attr, "index_flag": "IndexFlag"}),
            "UnSubscribeWatchlist": ("Watchlist", {**stock_attr, "index_flag": "IndexFlag"}),
            "SubscribeWatchlistAll": ("WatchlistAll", stock_attr),
            "UnSubscribeWatchlistAll": ("WatchlistAll", stock_attr),
            "SubscribeFiveTickA": ("FiveTickA", stock_attr),
            "UnSubscribeFiveTickA": ("FiveTickA", stock_attr),
            "SubscribeStockTick": ("StockTick", stock_attr),
            "UnSubscribeStockTick": ("StockTick", stock_attr),
            "SubscribeMarketInformation": ("MarketInformation", stock_attr),
            "UnSubscribeMarketInformation": ("MarketInformation", stock_attr),
            "SubscribeStockInformation": ("StockOtherInformation", stock_attr),
            "UnSubscribeStockInformation": ("StockOtherInformation", stock_attr),
        }
        mapping = class_map.get(function_name)
        if mapping is None:
            return list(symbols)

        class_name, attr_map = mapping
        try:
            from System.Collections.Generic import List
            from YuantaOneAPI import enumMarketType

            module = __import__("YuantaOneAPI", fromlist=[class_name])
            cls = getattr(module, class_name)
            result = List[cls]()
            for raw_item in symbols:
                item = raw_item.to_dict() if hasattr(raw_item, "to_dict") else raw_item
                obj = cls()
                for key, value in item.items():
                    attr = attr_map.get(str(key), str(key))
                    if not hasattr(obj, attr):
                        continue
                    if attr == "MarketType" and isinstance(value, str):
                        value = getattr(enumMarketType, value, value)
                    if attr == "IndexFlag":
                        try:
                            from YuantaOneAPI import enumQuoteIndexType
                            value = enumQuoteIndexType(value)
                        except Exception:
                            pass
                    setattr(obj, attr, value)
                result.Add(obj)
            return result
        except Exception:
            return list(symbols)

    @staticmethod
    def _convert_query_object_params(function_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Convert object-list query params to .NET typed lists when possible.

        ``GetWatchListAll`` expects ``List[Quote]`` and ``GetStockInformation``
        expects ``List[StkInfo]``; plain dicts are not accepted by pythonnet.
        """
        result = dict(params)
        object_params = {
            "QuoteList": ("Quote", {"market_type": "MarketType", "stock_code": "StockCode"}),
            "StkList": ("StkInfo", {"market_type": "MarketType", "stock_code": "StockCode"}),
        }
        for param_name, (class_name, attr_map) in object_params.items():
            value = result.get(param_name)
            if not isinstance(value, (list, tuple)):
                continue
            result[param_name] = YuantaAdapter._build_typed_object_list(
                class_name, value, attr_map
            )

        re_gain_loss = result.get("ReGainLoss")
        if isinstance(re_gain_loss, dict):
            result["ReGainLoss"] = YuantaAdapter._build_typed_object(
                "RealizedGainLoss",
                re_gain_loss,
                {
                    "account": "Account",
                    "market_no": "MarketNo",
                    "stk_code": "StkCode",
                    "trade_date": "TradeDate",
                    "trade_kind": "TradeKind",
                    "price": "Price",
                    "qty": "Qty",
                    "profit_loss": "ProfitLoss",
                    "order_no": "OrderNo",
                    "term_split": "TermSplit",
                    "term_ext": "TermExt",
                    "charge": "Charge",
                    "cost": "Cost",
                    "tax": "Tax",
                    "total_amt": "TotalAMT",
                },
            )

        # Convert common string/int parameters to the .NET enum types expected
        # by the Yuanta API methods.
        try:
            from YuantaOneAPI import KLineType, enumMarketType, enumStkTickSelectType

            market_type = result.get("MarketType")
            if isinstance(market_type, str):
                result["MarketType"] = getattr(
                    enumMarketType, market_type, market_type
                )

            kline_type = result.get("KLineType")
            if isinstance(kline_type, int):
                result["KLineType"] = KLineType(kline_type)

            select_type = result.get("SelectType")
            if isinstance(select_type, int):
                result["SelectType"] = enumStkTickSelectType(select_type)
        except Exception:
            # If the assembly is not loaded (e.g. unit tests), leave values as-is.
            pass
        return result

    @staticmethod
    def _build_typed_object(
        class_name: str,
        item: dict[str, Any],
        attr_map: dict[str, str],
    ) -> Any:
        """Build one .NET object from a JSON-friendly mapping when possible."""
        try:
            from YuantaOneAPI import enumMarketType

            module = __import__("YuantaOneAPI", fromlist=[class_name])
            cls = getattr(module, class_name)
            result = cls()
            for key, value in item.items():
                attr = attr_map.get(str(key), str(key))
                if not hasattr(result, attr):
                    continue
                if attr == "MarketNo" and isinstance(value, str):
                    value = getattr(enumMarketType, value, value)
                setattr(result, attr, value)
            return result
        except Exception:
            # Test fakes and callers without the optional SDK still receive the
            # original mapping instead of failing during parameter normalization.
            return item

    @staticmethod
    def _build_typed_object_list(
        class_name: str,
        items: list[Any] | tuple[Any, ...],
        attr_map: dict[str, str],
    ) -> Any:
        """Build a .NET ``List[T]`` from plain dicts; falls back to plain list."""
        try:
            from System.Collections.Generic import List
            from YuantaOneAPI import enumMarketType

            module = __import__("YuantaOneAPI", fromlist=[class_name])
            cls = getattr(module, class_name)
            result = List[cls]()
            for raw_item in items:
                item = raw_item.to_dict() if hasattr(raw_item, "to_dict") else raw_item
                obj = cls()
                for key, value in item.items():
                    attr = attr_map.get(str(key), str(key))
                    if not hasattr(obj, attr):
                        continue
                    if attr == "MarketType" and isinstance(value, str):
                        value = getattr(enumMarketType, value, value)
                    setattr(obj, attr, value)
                result.Add(obj)
            return result
        except Exception:
            return list(items)

    def query(
        self,
        function_name: str,
        *args: Any,
        request_id: str | None = None,
        timeout: float = 10.0,
        **kwargs: Any,
    ) -> Any:
        """Call a Yuanta query function and wait for its ``OnResponse``.

        Parameters are forwarded to the .NET trader method.  The matching
        response is serialized to plain dict/list via :mod:`serializer`.
        """
        if self._trader is None:
            raise YuantaAdapterError("trader is not available")
        method = getattr(self._trader, function_name, None)
        if not callable(method):
            raise YuantaAdapterError(f"unknown Yuanta function: {function_name}")

        kwargs = self._convert_query_object_params(function_name, kwargs)
        try:
            accepted = method(*args, **kwargs) if args else method(**kwargs)
        except TypeError:
            # Some pythonnet bindings do not accept keyword arguments.  If the
            # caller supplied only kwargs, retry positionally in declaration
            # order (the service layer preserves the documented order).
            if not args and kwargs:
                accepted = method(*kwargs.values())
            else:
                raise
        except Exception as exc:
            raise YuantaAdapterError(
                f"query {function_name} call failed: {exc}"
            ) from exc
        if not accepted:
            raise YuantaAdapterError(f"query {function_name} was rejected")

        deadline = time.monotonic() + timeout
        with self._query_cond:
            while True:
                response = self._take_response_locked(function_name, request_id)
                if response is not None:
                    return response

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    request_suffix = f" request_id={request_id}" if request_id else ""
                    raise TimeoutError(
                        f"timed out after {timeout:.1f}s waiting for {function_name} "
                        f"response{request_suffix}"
                    )
                self._query_cond.wait(remaining)

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
        self.dispose()
