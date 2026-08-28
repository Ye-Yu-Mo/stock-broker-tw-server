"""Local SQLite state store for M3 snapshots, orders, trades, and reports."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

_FINAL_ORDER_STATUSES = {"10", "20", "24", "25", "30"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _json_loads(value: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


class StateStore:
    """SQLite-backed persistence for read-only query results and M4 recovery.

    The database file and parent directories are created on demand.  Each
    public method opens a short-lived connection so the store is safe to share
    across threads in the FastAPI application.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        path: str | Path | None = None,
    ) -> None:
        if db_path is None:
            db_path = path or "state/yuanta.db"
        self.db_path = Path(db_path)
        self._memory_conn: sqlite3.Connection | None = None
        if str(self.db_path) == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
        elif self.db_path.parent and str(self.db_path.parent) != ".":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    account TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT NOT NULL,
                    account TEXT,
                    trade_date TEXT,
                    company_no TEXT,
                    status TEXT,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(order_no, trade_date)
                );

                CREATE TABLE IF NOT EXISTS stock_orders (
                    client_order_id TEXT PRIMARY KEY,
                    account TEXT,
                    action TEXT,
                    status TEXT,
                    order_no TEXT,
                    trade_date TEXT,
                    request TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT NOT NULL,
                    account TEXT,
                    trade_date TEXT,
                    company_no TEXT,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(order_no, trade_date)
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    order_no TEXT,
                    account TEXT,
                    trade_date TEXT,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(report_type, order_no, trade_date)
                );

                CREATE INDEX IF NOT EXISTS idx_orders_order_no ON orders(order_no);
                CREATE INDEX IF NOT EXISTS idx_stock_orders_order_no ON stock_orders(order_no);
                CREATE INDEX IF NOT EXISTS idx_stock_orders_status ON stock_orders(status);
                CREATE INDEX IF NOT EXISTS idx_trades_order_no ON trades(order_no);
                CREATE INDEX IF NOT EXISTS idx_reports_order_no ON reports(order_no);
                CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
                """
            )

    # -- snapshots ---------------------------------------------------------

    def save_snapshot(self, kind: str, payload: Any, account: str | None = None) -> None:
        """Persist the latest successful snapshot payload for ``kind``."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO snapshots (kind, account, payload, created_at) VALUES (?, ?, ?, ?)",
                (kind, account, _json_dumps(payload), _now()),
            )

    def get_latest_snapshot(
        self, kind: str, account: str | None = None
    ) -> dict[str, Any] | None:
        """Return the most recent snapshot row for ``kind``."""
        if account is None:
            row = self._fetchone(
                "SELECT * FROM snapshots WHERE kind = ? ORDER BY id DESC LIMIT 1",
                (kind,),
            )
        else:
            row = self._fetchone(
                "SELECT * FROM snapshots WHERE kind = ? AND account = ? ORDER BY id DESC LIMIT 1",
                (kind, account),
            )
        if row is None:
            return None
        return {
            "kind": row["kind"],
            "account": row["account"],
            "data": _json_loads(row["payload"]),
            "created_at": row["created_at"],
        }

    # -- orders ------------------------------------------------------------

    def save_orders(self, orders: Iterable[dict[str, Any]]) -> None:
        """Insert or replace order records keyed by order_no/trade_date."""
        for order in orders:
            order_no = order.get("order_no")
            if not order_no:
                continue
            account = order.get("account")
            trade_date = _stringify_date(order.get("trade_date")) or ""
            company_no = order.get("company_no")
            status = str(order.get("status") or order.get("order_status") or "")
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO orders (order_no, account, trade_date, company_no, status, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_no, trade_date) DO UPDATE SET
                        account = excluded.account,
                        company_no = excluded.company_no,
                        status = excluded.status,
                        data = excluded.data,
                        created_at = excluded.created_at
                    """,
                    (order_no, account, trade_date, company_no, status, _json_dumps(order), _now()),
                )

    def get_orders(
        self, order_no: str | None = None, trade_date: str | None = None
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM orders"
        conditions: list[str] = []
        params: list[Any] = []
        if order_no:
            conditions.append("order_no = ?")
            params.append(order_no)
        if trade_date:
            conditions.append("trade_date = ?")
            params.append(trade_date)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY id"
        return [self._row_to_dict(row) for row in self._fetchall(sql, tuple(params))]

    def get_unfinished_orders(self) -> list[dict[str, Any]]:
        """Return orders whose status is not a known final state."""
        rows = self._fetchall(
            "SELECT * FROM orders WHERE status NOT IN ('10','20','24','25','30') ORDER BY id"
        )
        return [self._row_to_dict(row) for row in rows]

    # -- M4 stock orders (client_order_id idempotency) ---------------------

    def save_stock_order(
        self,
        client_order_id: str,
        request: dict[str, Any] | None = None,
        status: str = "PENDING",
        account: str | None = None,
        action: str | None = None,
        order_no: str | None = None,
        trade_date: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Insert a new stock order keyed by ``client_order_id``."""
        request = request or {"client_order_id": client_order_id}
        request_json = _json_dumps(request)
        data_json = _json_dumps(data or {})
        trade_date = _stringify_date(trade_date) or trade_date
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO stock_orders (
                    client_order_id, account, action, status, order_no, trade_date,
                    request, data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(client_order_id) DO UPDATE SET
                    account = excluded.account,
                    action = excluded.action,
                    status = excluded.status,
                    order_no = excluded.order_no,
                    trade_date = excluded.trade_date,
                    request = excluded.request,
                    data = excluded.data,
                    updated_at = excluded.updated_at
                """,
                (
                    client_order_id,
                    account,
                    action or (request.get("action") if isinstance(request, dict) else None),
                    status,
                    order_no,
                    trade_date,
                    request_json,
                    data_json,
                    now,
                    now,
                ),
            )

    def save_stock_order_state(self, state: Any) -> None:
        """Persist a :class:`StockOrderState`-like object or its dict form."""
        data = state.to_dict() if hasattr(state, "to_dict") else state
        if not isinstance(data, dict) or "client_order_id" not in data:
            raise TypeError("state must be a StockOrderState or a mapping with client_order_id")
        request = data.get("request") or {}
        self.save_stock_order(
            client_order_id=str(data["client_order_id"]),
            request=request if isinstance(request, dict) else {"client_order_id": data["client_order_id"]},
            status=str(data.get("status", "PENDING")),
            account=data.get("account"),
            action=(request.get("action") if isinstance(request, dict) else None),
            order_no=data.get("order_no"),
            trade_date=data.get("trade_date"),
            data=data,
        )

    def update_stock_order(
        self,
        client_order_id: str,
        status: str | None = None,
        order_no: str | None = None,
        trade_date: str | None = None,
        data: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
        account: str | None = None,
        action: str | None = None,
    ) -> None:
        """Update mutable fields of an existing stock order row."""
        current = self.get_stock_order(client_order_id)
        if current is None:
            raise KeyError(f"stock order not found: {client_order_id}")
        trade_date = _stringify_date(trade_date) if trade_date is not None else None
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE stock_orders SET
                    account = COALESCE(?, account),
                    action = COALESCE(?, action),
                    status = COALESCE(?, status),
                    order_no = COALESCE(?, order_no),
                    trade_date = COALESCE(?, trade_date),
                    request = COALESCE(?, request),
                    data = COALESCE(?, data),
                    updated_at = ?
                WHERE client_order_id = ?
                """,
                (
                    account,
                    action,
                    status,
                    order_no,
                    trade_date,
                    _json_dumps(request) if request is not None else None,
                    _json_dumps(data) if data is not None else None,
                    _now(),
                    client_order_id,
                ),
            )

    def get_stock_order(self, client_order_id: str) -> dict[str, Any] | None:
        row = self._fetchone(
            "SELECT * FROM stock_orders WHERE client_order_id = ?",
            (client_order_id,),
        )
        return self._stock_order_row_to_dict(row) if row is not None else None

    def get_stock_order_by_order_no(
        self, order_no: str, trade_date: str | None = None
    ) -> dict[str, Any] | None:
        if trade_date:
            row = self._fetchone(
                "SELECT * FROM stock_orders WHERE order_no = ? AND trade_date = ? ORDER BY updated_at DESC LIMIT 1",
                (order_no, trade_date),
            )
        else:
            row = self._fetchone(
                "SELECT * FROM stock_orders WHERE order_no = ? ORDER BY updated_at DESC LIMIT 1",
                (order_no,),
            )
        return self._stock_order_row_to_dict(row) if row is not None else None

    def list_stock_orders(
        self,
        account: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM stock_orders"
        conditions: list[str] = []
        params: list[Any] = []
        if account:
            conditions.append("account = ?")
            params.append(account)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at, client_order_id"
        rows = self._fetchall(sql, tuple(params))
        return [self._stock_order_row_to_dict(row) for row in rows]

    def get_stock_orders(
        self,
        account: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Alias for :meth:`list_stock_orders`."""
        return self.list_stock_orders(account=account, status=status)

    @staticmethod
    def _stock_order_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        request = _json_loads(row["request"]) or {}
        data = _json_loads(row["data"]) or {}
        result = {
            "client_order_id": row["client_order_id"],
            "account": row["account"],
            "action": row["action"],
            "status": row["status"],
            "order_no": row["order_no"],
            "trade_date": row["trade_date"],
            "request": request,
            "data": data,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for key in ("filled_qty", "avg_price", "last_error", "need_manual_review", "transitions"):
            if key not in result and key in data:
                result[key] = data[key]
        return result

    # -- trades ------------------------------------------------------------

    def save_trades(self, trades: Iterable[dict[str, Any]]) -> None:
        """Insert or replace trade records keyed by order_no/trade_date."""
        for trade in trades:
            order_no = trade.get("order_no")
            if not order_no:
                continue
            account = trade.get("account")
            trade_date = _stringify_date(trade.get("trade_date")) or ""
            company_no = trade.get("company_no")
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO trades (order_no, account, trade_date, company_no, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_no, trade_date) DO UPDATE SET
                        account = excluded.account,
                        company_no = excluded.company_no,
                        data = excluded.data,
                        created_at = excluded.created_at
                    """,
                    (order_no, account, trade_date, company_no, _json_dumps(trade), _now()),
                )

    def get_trades(
        self, order_no: str | None = None, trade_date: str | None = None
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM trades"
        conditions: list[str] = []
        params: list[Any] = []
        if order_no:
            conditions.append("order_no = ?")
            params.append(order_no)
        if trade_date:
            conditions.append("trade_date = ?")
            params.append(trade_date)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY id"
        return [self._row_to_dict(row) for row in self._fetchall(sql, tuple(params))]

    # -- reports -----------------------------------------------------------

    def save_reports(self, report_type: str, reports: Iterable[dict[str, Any]]) -> None:
        """Insert or replace report rows for ``report_type`` keyed by order_no/date."""
        for report in reports:
            order_no = report.get("order_no") or ""
            trade_date = _stringify_date(report.get("order_date") or report.get("trade_date")) or ""
            account = report.get("account")
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO reports (report_type, order_no, account, trade_date, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(report_type, order_no, trade_date) DO UPDATE SET
                        account = excluded.account,
                        data = excluded.data,
                        created_at = excluded.created_at
                    """,
                    (report_type, order_no, account, trade_date, _json_dumps(report), _now()),
                )

    def get_reports(self, report_type: str | None = None) -> list[dict[str, Any]]:
        if report_type is None:
            rows = self._fetchall("SELECT * FROM reports ORDER BY id")
        else:
            rows = self._fetchall("SELECT * FROM reports WHERE report_type = ? ORDER BY id", (report_type,))
        return [self._row_to_dict(row) for row in rows]

    # -- helpers -----------------------------------------------------------

    def _fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(sql, params).fetchone()

    def _fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = _json_loads(row["data"])
        result = dict(row)
        result["data"] = data
        if isinstance(data, dict):
            for key, value in data.items():
                result.setdefault(key, value)
        return result


def _stringify_date(value: Any) -> str | None:
    """Convert a Yuanta date dict or ISO string to ``YYYY/MM/DD`` when possible."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y/%m/%d")
    if isinstance(value, dict):
        year = value.get("year") if value.get("year") is not None else value.get("Year")
        month = value.get("month") if value.get("month") is not None else value.get("Month")
        day = value.get("day") if value.get("day") is not None else value.get("Day")
        if year is not None and month is not None and day is not None:
            return f"{int(year):04d}/{int(month):02d}/{int(day):02d}"
    return str(value)


__all__ = ["StateStore"]
