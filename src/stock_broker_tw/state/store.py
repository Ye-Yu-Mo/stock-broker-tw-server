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
        year = value.get("year")
        month = value.get("month")
        day = value.get("day")
        if year is not None and month is not None and day is not None:
            return f"{int(year):04d}/{int(month):02d}/{int(day):02d}"
    return str(value)


__all__ = ["StateStore"]
