"""High-level Python wrapper around ``YuantaSparkAPITrader``.

The adapter owns the .NET trader object, registers ``OnResponse`` once, and
forwards every raw event to a thread-safe :class:`EventQueue`.  Business code
should use this class instead of touching pythonnet directly.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Self

from stock_broker_tw.yuanta import loader
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent
from stock_broker_tw.yuanta.serializer import login_result_to_dict, to_dict


class YuantaAdapterError(RuntimeError):
    """Raised when the adapter is used in an invalid lifecycle state."""


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
        self._query_responses: dict[str, list[Any]] = {}
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

        if pfx_path:
            result = self._trader.Login(pfx_path, pfx_pass, account, password)
        else:
            result = self._trader.Login(account, password)
        self._logged_in = bool(result)
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
        event = YuantaEvent(
            int_mark=int_mark,
            dw_index=dw_index,
            str_index=str_index,
            obj_handle=obj_handle,
            obj_value=obj_value,
        )
        self._event_queue.put(event)

        if str_index == "Login":
            try:
                data = login_result_to_dict(obj_value)
                self._last_login_result = data
                if data.get("login_list"):
                    self._logged_in = True
                else:
                    self._logged_in = False
            except Exception:
                pass

        # Query/trade responses are stored separately so ``query()`` and
        # ``send_stock_order()`` do not steal unrelated events from the shared
        # WebSocket/event queue.
        if (int_mark == 1 or str_index == "SendStockOrder") and str_index != "Login":
            try:
                data = to_dict(obj_value)
            except Exception:
                data = None
            if data is not None:
                with self._query_cond:
                    self._query_responses.setdefault(str_index, []).append(data)
                    self._query_cond.notify_all()

    def send_stock_order(
        self,
        account: str,
        orders: Any,
        timeout: float = 10.0,
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
                responses = self._query_responses.get("SendStockOrder")
                if responses:
                    return responses.pop(0)

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"timed out after {timeout:.1f}s waiting for SendStockOrder response")
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
                responses = self._query_responses.get(function_name)
                if responses:
                    return responses.pop(0)

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
