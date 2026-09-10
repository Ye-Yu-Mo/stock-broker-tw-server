"""Local SQLite state store for M3 snapshots, orders, trades, and reports."""

from __future__ import annotations

import json
import logging
import math
import re
import sqlite3
import uuid
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MockAccountError(Exception):
    """Raised when a simulated account cannot complete an operation."""

    def __init__(self, message: str, code: str = "MOCK_ACCOUNT_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


_FINAL_ORDER_STATUSES = {"10", "20", "24", "25", "30"}
_VALID_STOCK_ORDER_STATUSES = {
    "PENDING",
    "SUBMITTED",
    "ACCEPTED",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
    "FAILED",
    "NEED_MANUAL_REVIEW",
}
_MOCK_ACCOUNT_RE = re.compile(r"^MOCK-[A-Za-z0-9][A-Za-z0-9_.-]*$")


def is_mock_account(account: Any) -> bool:
    """Return whether ``account`` belongs to the isolated mock namespace."""
    return bool(_MOCK_ACCOUNT_RE.fullmatch(str(account or "")))


def _finite_number(
    value: Any,
    field: str,
    *,
    positive: bool = False,
    code: str = "INVALID_MOCK_VALUE",
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MockAccountError(f"{field} must be numeric", code) from exc
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        requirement = "positive" if positive else "finite and non-negative"
        raise MockAccountError(f"{field} must be {requirement}", code)
    return number


def _integer_quantity(
    value: Any,
    field: str,
    *,
    positive: bool = False,
    code: str = "INVALID_MOCK_VALUE",
) -> int:
    if isinstance(value, bool):
        raise MockAccountError(f"{field} must be an integer", code)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MockAccountError(f"{field} must be an integer", code) from exc
    if not math.isfinite(number) or number != int(number):
        raise MockAccountError(f"{field} must be an integer", code)
    quantity = int(number)
    if (quantity <= 0 if positive else quantity < 0):
        requirement = "positive" if positive else "non-negative"
        raise MockAccountError(f"{field} must be {requirement}", code)
    return quantity


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _mock_claim_expired(execution: Any) -> bool:
    if not isinstance(execution, dict):
        return False
    expires_at = execution.get("expires_at")
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(str(expires_at))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return expiry <= datetime.now(UTC)
    except (TypeError, ValueError):
        return False


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _json_loads(value: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def _merge_order_data(current: Any, incoming: Any) -> dict[str, Any] | None:
    """Merge an order update without discarding fields from a newer writer."""
    if incoming is None:
        return None
    current_data = dict(current) if isinstance(current, dict) else {}
    incoming_data = dict(incoming) if isinstance(incoming, dict) else {}
    merged = {**current_data, **incoming_data}

    current_transitions = current_data.get("transitions")
    incoming_transitions = incoming_data.get("transitions")
    if isinstance(current_transitions, list) or isinstance(incoming_transitions, list):
        transitions: list[Any] = []
        seen: set[str] = set()
        for item in [
            *(current_transitions if isinstance(current_transitions, list) else []),
            *(incoming_transitions if isinstance(incoming_transitions, list) else []),
        ]:
            marker = _json_dumps(item)
            if marker in seen:
                continue
            seen.add(marker)
            transitions.append(item)
        transitions.sort(key=lambda item: str(item.get("at", item.get("timestamp", ""))) if isinstance(item, dict) else "")
        merged["transitions"] = transitions
    return merged


def _validate_order_transition(
    client_order_id: str,
    current_status: str | None,
    new_status: str | None,
) -> None:
    """Reject status changes that violate the order state machine."""
    if new_status is None or current_status == new_status:
        return
    # Imported lazily to avoid a package-init cycle:
    # engine/__init__ -> report_handler -> state.store.
    from stock_broker_tw.engine.state import (
        InvalidOrderStateTransition,
        OrderStateMachine,
    )

    if not OrderStateMachine().can_transition(current_status, new_status):
        logger.error(
            "rejected illegal order status transition: client_order_id=%s %s -> %s",
            client_order_id,
            current_status,
            new_status,
        )
        raise InvalidOrderStateTransition(
            f"illegal order transition for {client_order_id}: "
            f"{current_status} -> {new_status}"
        )


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
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
        elif self.db_path.parent and str(self.db_path.parent) != ".":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
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
                    created_at TEXT NOT NULL
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

                CREATE TABLE IF NOT EXISTS quote_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT NOT NULL,
                    quote_type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    market_type TEXT NOT NULL DEFAULT 'TWSE',
                    index_flag INTEGER,
                    created_at TEXT NOT NULL,
                    UNIQUE(account, quote_type, symbol, market_type, index_flag)
                );

                CREATE TABLE IF NOT EXISTS mock_accounts (
                    account TEXT PRIMARY KEY,
                    cash REAL NOT NULL,
                    positions TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_orders_order_no ON orders(order_no);
                CREATE INDEX IF NOT EXISTS idx_stock_orders_order_no ON stock_orders(order_no);
                CREATE INDEX IF NOT EXISTS idx_stock_orders_status ON stock_orders(status);
                CREATE INDEX IF NOT EXISTS idx_trades_order_no ON trades(order_no);
                CREATE INDEX IF NOT EXISTS idx_reports_order_no ON reports(order_no);
                CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
                CREATE INDEX IF NOT EXISTS idx_quote_subscriptions_account ON quote_subscriptions(account);
                """
            )
            self._migrate_trades_table()
            self._migrate_quote_subscriptions_table()
            self._migrate_mock_accounts_table()
            self._ensure_quote_subscription_unique()

    def _migrate_trades_table(self) -> None:
        """Rebuild ``trades`` without the old unique(order_no, trade_date)."""
        with self._connect() as conn:
            indexes = conn.execute("PRAGMA index_list('trades')").fetchall()
            has_unique = any(
                row["origin"] == "u" if "origin" in row else row[3] == "u"
                for row in indexes
            )
            if not has_unique:
                return
            conn.execute(
                """
                CREATE TABLE trades_migrated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT NOT NULL,
                    account TEXT,
                    trade_date TEXT,
                    company_no TEXT,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO trades_migrated (id, order_no, account, trade_date, company_no, data, created_at)
                SELECT id, order_no, account, trade_date, company_no, data, created_at FROM trades
                """
            )
            conn.execute("DROP TABLE trades")
            conn.execute("ALTER TABLE trades_migrated RENAME TO trades")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_order_no ON trades(order_no)")

    def _migrate_quote_subscriptions_table(self) -> None:
        """Rebuild ``quote_subscriptions`` to include ``index_flag`` in the key."""
        with self._connect() as conn:
            columns = [row["name"] for row in conn.execute("PRAGMA table_info('quote_subscriptions')").fetchall()]
            has_index_flag = "index_flag" in columns
            has_index_in_unique = any(
                "index_flag" in (row["name"] or "")
                for row in conn.execute("PRAGMA index_info('sqlite_autoindex_quote_subscriptions_1')").fetchall()
            )
            if has_index_flag and has_index_in_unique:
                return
            conn.execute(
                """
                CREATE TABLE quote_subscriptions_migrated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT NOT NULL,
                    quote_type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    market_type TEXT NOT NULL DEFAULT 'TWSE',
                    index_flag INTEGER,
                    created_at TEXT NOT NULL,
                    UNIQUE(account, quote_type, symbol, market_type, index_flag)
                )
                """
            )
            if has_index_flag:
                conn.execute(
                    """
                    INSERT INTO quote_subscriptions_migrated
                        (id, account, quote_type, symbol, market_type, index_flag, created_at)
                    SELECT id, account, quote_type, symbol, market_type, index_flag, created_at
                    FROM quote_subscriptions
                    """
                )
            else:
                conn.execute(
                    """
                    INSERT INTO quote_subscriptions_migrated
                        (id, account, quote_type, symbol, market_type, index_flag, created_at)
                    SELECT id, account, quote_type, symbol, market_type, NULL, created_at
                    FROM quote_subscriptions
                    """
                )
            conn.execute("DROP TABLE quote_subscriptions")
            conn.execute("ALTER TABLE quote_subscriptions_migrated RENAME TO quote_subscriptions")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_quote_subscriptions_account ON quote_subscriptions(account)")

    def _migrate_mock_accounts_table(self) -> None:
        """Add the active flag to databases created before mock lifecycle support."""
        with self._connect() as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info('mock_accounts')").fetchall()
            }
            if "active" not in columns:
                conn.execute(
                    "ALTER TABLE mock_accounts ADD COLUMN active INTEGER NOT NULL DEFAULT 1"
                )

    def _ensure_quote_subscription_unique(self) -> None:
        """Make nullable index_flag participate in subscription uniqueness."""
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM quote_subscriptions
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM quote_subscriptions
                    GROUP BY account, quote_type, symbol, market_type,
                             COALESCE(index_flag, -1)
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_quote_subscriptions_natural
                ON quote_subscriptions(
                    account, quote_type, symbol, market_type, COALESCE(index_flag, -1)
                )
                """
            )


    @staticmethod
    def _normalize_mock_positions(positions: Any) -> dict[str, dict[str, Any]]:
        if positions is None:
            return {}
        if isinstance(positions, dict):
            entries = []
            for stk_code, value in positions.items():
                if isinstance(value, dict):
                    entries.append({"stk_code": stk_code, **value})
                else:
                    entries.append({"stk_code": stk_code, "quantity": value})
        elif isinstance(positions, list):
            entries = positions
        else:
            raise MockAccountError("positions must be a list or mapping", "INVALID_MOCK_POSITIONS")

        normalized: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise MockAccountError("each position must be an object", "INVALID_MOCK_POSITION")
            stk_code = str(entry.get("stk_code") or entry.get("symbol") or "").strip()
            if not stk_code:
                raise MockAccountError("position stk_code is required", "INVALID_MOCK_POSITION")
            quantity = _integer_quantity(
                entry.get("quantity", entry.get("qty", 0)),
                f"position quantity for {stk_code}",
                code="INVALID_MOCK_POSITION",
            )
            avg_price = entry.get("avg_price")
            if avg_price is not None:
                avg_price = _finite_number(
                    avg_price,
                    f"average price for {stk_code}",
                    code="INVALID_MOCK_POSITION",
                )
            normalized[stk_code] = {"quantity": quantity, "avg_price": avg_price}
        return normalized

    @staticmethod
    def _mock_account_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "account": row["account"],
            "cash": float(row["cash"]),
            "positions": _json_loads(row["positions"]) or {},
            "active": bool(row["active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def init_mock_account(
        self,
        account: str,
        cash: float,
        positions: Any = None,
    ) -> dict[str, Any]:
        account = str(account or "").strip()
        if not is_mock_account(account):
            raise MockAccountError(
                "mock account must use the MOCK- namespace", "INVALID_MOCK_ACCOUNT"
            )
        cash = _finite_number(cash, "cash", code="INVALID_MOCK_ACCOUNT")
        normalized = self._normalize_mock_positions(positions)
        existing = self.get_mock_account(account)
        if existing:
            current_positions = self._normalize_mock_positions(existing.get("positions"))
            if existing["cash"] != cash or current_positions != normalized:
                with self._connect() as conn:
                    history = conn.execute(
                        """
                        SELECT 1 FROM stock_orders WHERE account = ?
                        UNION ALL SELECT 1 FROM orders WHERE account = ?
                        UNION ALL SELECT 1 FROM trades WHERE account = ?
                        LIMIT 1
                        """,
                        (account, account, account),
                    ).fetchone()
                if history is not None:
                    raise MockAccountError(
                        "cannot reinitialize mock account with existing history",
                        "MOCK_ACCOUNT_REINITIALIZE_REQUIRES_RESET",
                    )
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO mock_accounts (account, cash, positions, active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(account) DO UPDATE SET
                    cash = excluded.cash,
                    positions = excluded.positions,
                    active = 1,
                    updated_at = excluded.updated_at
                """,
                (account, cash, _json_dumps(normalized), now, now),
            )
        return self.get_mock_account(account) or {}

    def get_mock_account(self, account: str) -> dict[str, Any] | None:
        account = str(account or "").strip()
        if not is_mock_account(account):
            return None
        row = self._fetchone(
            "SELECT * FROM mock_accounts WHERE account = ?",
            (account,),
        )
        return self._mock_account_row_to_dict(row) if row is not None else None

    def deactivate_mock_account(self, account: str) -> bool:
        """Deactivate a mock account without deleting its historical ledger."""
        account = str(account or "").strip()
        if not is_mock_account(account):
            raise MockAccountError(
                "mock account must use the MOCK- namespace", "INVALID_MOCK_ACCOUNT"
            )
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE mock_accounts SET active = 0, updated_at = ? WHERE account = ?",
                (_now(), account),
            )
        if cursor.rowcount == 0:
            raise MockAccountError(
                f"mock account not found: {account}", "MOCK_ACCOUNT_NOT_FOUND"
            )
        return True

    def apply_mock_fill(
        self,
        account: str,
        side: str,
        stk_code: str,
        quantity: int,
        price: float,
    ) -> dict[str, Any]:
        account = str(account or "").strip()
        if not is_mock_account(account):
            raise MockAccountError(
                "mock account must use the MOCK- namespace", "INVALID_MOCK_ACCOUNT"
            )
        stk_code = str(stk_code or "").strip()
        if not stk_code:
            raise MockAccountError("stk_code is required", "INVALID_MOCK_FILL")
        quantity = _integer_quantity(quantity, "quantity", positive=True, code="INVALID_MOCK_FILL")
        price = _finite_number(price, "price", positive=True, code="INVALID_MOCK_FILL")

        side = str(side).upper()
        if side not in {"B", "S"}:
            raise MockAccountError("side must be B or S", "INVALID_MOCK_FILL")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM mock_accounts WHERE account = ?",
                (account,),
            ).fetchone()
            if row is None:
                raise MockAccountError(
                    f"mock account not found: {account}", "MOCK_ACCOUNT_NOT_FOUND"
                )
            if not row["active"]:
                raise MockAccountError(
                    f"mock account is inactive: {account}", "MOCK_ACCOUNT_INACTIVE"
                )

            cash = float(row["cash"])
            positions = self._normalize_mock_positions(_json_loads(row["positions"]))
            position = positions.get(stk_code, {"quantity": 0, "avg_price": None})
            current_quantity = int(position.get("quantity", 0) or 0)
            notional = price * quantity
            if side == "B":
                if cash < notional:
                    raise MockAccountError(
                        "mock account has insufficient cash", "INSUFFICIENT_CASH"
                    )
                new_quantity = current_quantity + quantity
                old_avg = position.get("avg_price")
                if old_avg is None:
                    avg_price = price
                else:
                    avg_price = (
                        current_quantity * float(old_avg) + notional
                    ) / new_quantity
                cash -= notional
            else:
                if current_quantity < quantity:
                    raise MockAccountError(
                        "mock account has insufficient position", "INSUFFICIENT_POSITION"
                    )
                new_quantity = current_quantity - quantity
                avg_price = position.get("avg_price")
                cash += notional

            if new_quantity:
                positions[stk_code] = {
                    "quantity": new_quantity,
                    "avg_price": avg_price,
                }
            else:
                positions.pop(stk_code, None)
            updated_at = _now()
            conn.execute(
                """
                UPDATE mock_accounts
                SET cash = ?, positions = ?, updated_at = ?
                WHERE account = ?
                """,
                (cash, _json_dumps(positions), updated_at, account),
            )
            return {
                "account": account,
                "cash": cash,
                "positions": positions,
                "created_at": row["created_at"],
                "updated_at": updated_at,
            }


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
        """Insert a new stock order keyed by ``client_order_id``.

        If the key already exists this method refuses to overwrite the row with
        a status that is not reachable from the current state.  Idempotent
        writes with the same status are still allowed.
        """
        request = request or {"client_order_id": client_order_id}
        request_json = _json_dumps(request)
        data_json = _json_dumps(data or {})
        trade_date = _stringify_date(trade_date) or trade_date
        now = _now()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            current = conn.execute(
                "SELECT status FROM stock_orders WHERE client_order_id = ?",
                (client_order_id,),
            ).fetchone()
            if current is not None:
                _validate_order_transition(
                    client_order_id,
                    current["status"],
                    status,
                )
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

    def claim_stock_order(
        self,
        client_order_id: str,
        request: dict[str, Any],
        account: str,
        action: str,
        mock: bool = False,
        execution_id: str | None = None,
        lease_seconds: float = 30.0,
    ) -> tuple[bool, dict[str, Any]]:
        """Atomically claim a client order id before external execution.

        A successful insert (or retry claim) grants execution ownership.  A
        conflict is read-only: callers must return the existing state and never
        invoke a broker or mock fill themselves.
        """
        account = str(account or "").strip()
        if mock and not is_mock_account(account):
            raise MockAccountError(
                "mock orders require a MOCK- account", "INVALID_MOCK_ACCOUNT"
            )
        if not mock and is_mock_account(account):
            raise MockAccountError(
                "mock account requires mock=true", "MOCK_ACCOUNT_REQUIRES_MOCK"
            )
        request = dict(request)
        request["mock"] = bool(mock)
        execution_id = execution_id or str(uuid.uuid4())
        lease_seconds = _finite_number(
            lease_seconds,
            "lease_seconds",
            positive=True,
            code="INVALID_MOCK_CLAIM",
        )
        now = _now()
        expires_at = (datetime.now(UTC) + timedelta(seconds=lease_seconds)).isoformat()
        execution = {
            "id": execution_id,
            "attempt": 1,
            "status": "running",
            "started_at": now,
            "expires_at": expires_at,
        }
        data = {"request": request, "mock": bool(mock), "execution": execution}
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO stock_orders (
                    client_order_id, account, action, status, order_no, trade_date,
                    request, data, created_at, updated_at
                ) VALUES (?, ?, ?, 'PENDING', NULL, NULL, ?, ?, ?, ?)
                ON CONFLICT(client_order_id) DO NOTHING
                """,
                (
                    client_order_id,
                    account,
                    action,
                    _json_dumps(request),
                    _json_dumps(data),
                    now,
                    now,
                ),
            )
            claimed = cursor.rowcount == 1
            if not claimed and mock:
                existing = conn.execute(
                    "SELECT status, account, action, request, data FROM stock_orders WHERE client_order_id = ?",
                    (client_order_id,),
                ).fetchone()
                if existing is not None:
                    existing_data = _json_loads(existing["data"]) or {}
                    if not isinstance(existing_data, dict):
                        existing_data = {}
                    retryable = (
                        existing["status"] == "FAILED"
                        and bool(existing_data.get("retryable"))
                        and existing["account"] == account
                        and existing["action"] == action
                    )
                    previous_execution = existing_data.get("execution") or {}
                    stale = (
                        existing["status"] == "PENDING"
                        and existing["account"] == account
                        and existing["action"] == action
                        and _mock_claim_expired(previous_execution)
                    )
                    if retryable or stale:
                        attempt = int(previous_execution.get("attempt", 0) or 0) + 1
                        execution["attempt"] = attempt
                        existing_data["execution"] = execution
                        existing_data["retryable"] = False
                        if stale:
                            existing_data.setdefault("transitions", []).append(
                                {
                                    "from": "PENDING",
                                    "to": "PENDING",
                                    "reason": "reclaim expired mock execution",
                                    "at": now,
                                    "timestamp": now,
                                }
                            )
                        else:
                            transitions = list(existing_data.get("transitions") or [])
                            transitions.append(
                                {
                                    "from": "FAILED",
                                    "to": "PENDING",
                                    "reason": "retry mock execution",
                                    "at": now,
                                    "timestamp": now,
                                }
                            )
                            existing_data["transitions"] = transitions
                        previous_status = "PENDING" if stale else "FAILED"
                        cursor = conn.execute(
                            """
                            UPDATE stock_orders
                            SET status = 'PENDING', request = ?, data = ?, updated_at = ?
                            WHERE client_order_id = ? AND status = ?
                            """,
                            (
                                _json_dumps(request),
                                _json_dumps(existing_data),
                                now,
                                client_order_id,
                                previous_status,
                            ),
                        )
                        claimed = cursor.rowcount == 1
        row = self.get_stock_order(client_order_id)
        if row is None:
            raise KeyError(f"stock order claim disappeared: {client_order_id}")
        return claimed, row

    def settle_mock_fill(
        self,
        client_order_id: str,
        account: str,
        side: str,
        stk_code: str,
        quantity: int,
        price: float,
        order_no: str,
        trade_date: str,
        data: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically settle a Mock fill and its order/trade ledger rows."""
        account = str(account or "").strip()
        if not is_mock_account(account):
            raise MockAccountError(
                "mock account must use the MOCK- namespace", "INVALID_MOCK_ACCOUNT"
            )
        stk_code = str(stk_code or "").strip()
        if not stk_code:
            raise MockAccountError("stk_code is required", "INVALID_MOCK_FILL")
        quantity = _integer_quantity(quantity, "quantity", positive=True, code="INVALID_MOCK_FILL")
        price = _finite_number(price, "price", positive=True, code="INVALID_MOCK_FILL")
        side = str(side).upper()
        if side not in {"B", "S"}:
            raise MockAccountError("side must be B or S", "INVALID_MOCK_FILL")

        now = _now()
        trade_date = _stringify_date(trade_date) or ""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM stock_orders WHERE client_order_id = ?",
                (client_order_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"stock order not found: {client_order_id}")
            request = _json_loads(row["request"]) or {}
            persisted_data = _json_loads(row["data"]) or {}
            if not request.get("mock") and not persisted_data.get("mock"):
                raise MockAccountError(
                    "cannot settle a real order as mock",
                    "MOCK_ORDER_MODE_MISMATCH",
                )
            if execution_id is not None:
                current_execution = persisted_data.get("execution") or {}
                if current_execution.get("id") != execution_id:
                    raise MockAccountError(
                        "mock execution claim is no longer owned",
                        "MOCK_EXECUTION_CLAIM_LOST",
                    )
            current_status = str(row["status"] or "")
            if current_status == "FILLED":
                return self._stock_order_row_to_dict(row)
            if current_status != "PENDING":
                raise MockAccountError(
                    f"mock order cannot be settled from {current_status}",
                    "MOCK_ORDER_NOT_PENDING",
                )
            if row["account"] != account:
                raise MockAccountError("mock order account mismatch", "MOCK_ACCOUNT_MISMATCH")

            account_row = conn.execute(
                "SELECT * FROM mock_accounts WHERE account = ?",
                (account,),
            ).fetchone()
            if account_row is None:
                raise MockAccountError(
                    f"mock account not found: {account}", "MOCK_ACCOUNT_NOT_FOUND"
                )
            if not account_row["active"]:
                raise MockAccountError(
                    f"mock account is inactive: {account}", "MOCK_ACCOUNT_INACTIVE"
                )
            cash = float(account_row["cash"])
            positions = self._normalize_mock_positions(_json_loads(account_row["positions"]))
            position = positions.get(stk_code, {"quantity": 0, "avg_price": None})
            current_quantity = int(position.get("quantity", 0) or 0)
            notional = price * quantity
            if side == "B":
                if cash < notional:
                    raise MockAccountError(
                        "mock account has insufficient cash", "INSUFFICIENT_CASH"
                    )
                new_quantity = current_quantity + quantity
                old_avg = position.get("avg_price")
                avg_price = price if old_avg is None else (
                    current_quantity * float(old_avg) + notional
                ) / new_quantity
                cash -= notional
            else:
                if current_quantity < quantity:
                    raise MockAccountError(
                        "mock account has insufficient position", "INSUFFICIENT_POSITION"
                    )
                new_quantity = current_quantity - quantity
                avg_price = position.get("avg_price")
                cash += notional

            if new_quantity:
                positions[stk_code] = {"quantity": new_quantity, "avg_price": avg_price}
            else:
                positions.pop(stk_code, None)
            conn.execute(
                "UPDATE mock_accounts SET cash = ?, positions = ?, updated_at = ? WHERE account = ?",
                (cash, _json_dumps(positions), now, account),
            )

            persisted_data.update(data or {})
            execution = persisted_data.get("execution")
            if not isinstance(execution, dict):
                execution = {}
            execution.update({"status": "completed", "completed_at": now})
            persisted_data.update(
                {
                    "mock": True,
                    "execution": execution,
                    "filled_qty": quantity,
                    "avg_price": price,
                    "fill_price": price,
                }
            )
            transitions = list(persisted_data.get("transitions") or [])
            transitions.extend(
                [
                    {"from": "PENDING", "to": "ACCEPTED", "reason": "mock order accepted", "at": now, "timestamp": now},
                    {"from": "ACCEPTED", "to": "FILLED", "reason": "mock order filled", "at": now, "timestamp": now},
                ]
            )
            persisted_data["transitions"] = transitions
            request["mock"] = True
            conn.execute(
                """
                UPDATE stock_orders
                SET status = 'FILLED', order_no = ?, trade_date = ?, request = ?, data = ?, updated_at = ?
                WHERE client_order_id = ? AND status = 'PENDING'
                """,
                (
                    str(order_no),
                    trade_date,
                    _json_dumps(request),
                    _json_dumps(persisted_data),
                    now,
                    client_order_id,
                ),
            )
            trade = {
                "order_no": str(order_no),
                "account": account,
                "trade_date": trade_date,
                "company_no": stk_code,
                "client_order_id": client_order_id,
                "bs": side,
                "price": price,
                "ok_qty": quantity,
                "order_qty": quantity,
                "mock": True,
            }
            conn.execute(
                """
                INSERT INTO trades (order_no, account, trade_date, company_no, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(order_no), account, trade_date, stk_code, _json_dumps(trade), now),
            )
            conn.execute(
                """
                INSERT INTO orders (order_no, account, trade_date, company_no, status, data, created_at)
                VALUES (?, ?, ?, ?, '20', ?, ?)
                ON CONFLICT(order_no, trade_date) DO UPDATE SET
                    account = excluded.account,
                    company_no = excluded.company_no,
                    status = excluded.status,
                    data = excluded.data,
                    created_at = excluded.created_at
                """,
                (str(order_no), account, trade_date, stk_code, _json_dumps(trade), now),
            )

        return self.get_stock_order(client_order_id) or {}

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
        """Update mutable fields of an existing stock order row.

        A status change is validated against the order state machine before it
        is persisted; illegal transitions raise
        :class:`InvalidOrderStateTransition`.
        """
        trade_date = _stringify_date(trade_date) if trade_date is not None else None
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            current = conn.execute(
                "SELECT status, data FROM stock_orders WHERE client_order_id = ?",
                (client_order_id,),
            ).fetchone()
            if current is None:
                raise KeyError(f"stock order not found: {client_order_id}")
            _validate_order_transition(
                client_order_id,
                current["status"],
                status,
            )
            merged_data = _merge_order_data(_json_loads(current["data"]), data)
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
                    _json_dumps(merged_data) if merged_data is not None else None,
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

    def get_stock_order_by_basket_no(self, basket_no: str) -> dict[str, Any] | None:
        """Find an M4 order using the broker-facing BasketNo mapping."""
        basket_no = str(basket_no or "")
        if not basket_no:
            return None
        for row in self.list_stock_orders():
            request = row.get("request") or {}
            data = row.get("data") or {}
            if request.get("broker_basket_no") == basket_no or data.get("broker_basket_no") == basket_no:
                return row
        return None

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
        """Insert trade records; multiple fills for the same order/date are kept."""
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

    # -- quote subscriptions ----------------------------------------------

    def save_quote_subscriptions(
        self,
        account: str,
        quote_type: str,
        symbols: Iterable[str] | str,
        market_type: str = "TWSE",
        index_flag: int | None = None,
    ) -> None:
        """Insert quote subscription rows, ignoring duplicates by full key."""
        if isinstance(symbols, str):
            symbols = [symbols]
        quote_type = str(quote_type)
        for symbol in symbols:
            if not symbol:
                continue
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO quote_subscriptions
                        (account, quote_type, symbol, market_type, index_flag, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (account, quote_type, str(symbol), market_type, index_flag, _now()),
                )

    def save_quote_subscription(
        self,
        account: str,
        quote_type: str,
        symbol: str,
        market_type: str = "TWSE",
        index_flag: int | None = None,
    ) -> None:
        """Insert one quote subscription row."""
        self.save_quote_subscriptions(account, quote_type, [symbol], market_type, index_flag=index_flag)

    def delete_quote_subscriptions(
        self,
        account: str,
        quote_type: str,
        symbols: Iterable[str] | str,
        market_type: str = "TWSE",
        index_flag: int | None = None,
    ) -> None:
        """Delete quote subscription rows for the given full key."""
        quote_type = str(quote_type)
        if isinstance(symbols, str):
            symbols = [symbols]
        for symbol in symbols:
            if not symbol:
                continue
            with self._connect() as conn:
                conn.execute(
                    """
                    DELETE FROM quote_subscriptions
                    WHERE account = ? AND quote_type = ? AND symbol = ? AND market_type = ?
                        AND index_flag IS ?
                    """,
                    (account, quote_type, str(symbol), market_type, index_flag),
                )

    def delete_quote_subscription(
        self,
        account: str,
        quote_type: str,
        symbol: str,
        market_type: str = "TWSE",
        index_flag: int | None = None,
    ) -> None:
        """Delete one quote subscription row."""
        self.delete_quote_subscriptions(account, quote_type, [symbol], market_type, index_flag=index_flag)

    def list_quote_subscriptions(
        self,
        account: str | None = None,
        quote_type: str | None = None,
        index_flag: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return quote subscriptions, optionally filtered by account/type."""
        sql = "SELECT account, quote_type, symbol, market_type, index_flag, created_at FROM quote_subscriptions"
        conditions: list[str] = []
        params: list[Any] = []
        if account:
            conditions.append("account = ?")
            params.append(account)
        if quote_type:
            conditions.append("quote_type = ?")
            params.append(str(quote_type))
        if index_flag is not None:
            conditions.append("index_flag = ?")
            params.append(index_flag)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY id"
        rows = self._fetchall(sql, tuple(params))
        return [
            {
                "account": row["account"],
                "type": row["quote_type"],
                "symbol": row["symbol"],
                "market_type": row["market_type"],
                "index_flag": row["index_flag"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_quote_subscriptions(
        self,
        account: str | None = None,
        quote_type: str | None = None,
        index_flag: int | None = None,
    ) -> list[dict[str, Any]]:
        """Alias for :meth:`list_quote_subscriptions`."""
        return self.list_quote_subscriptions(account=account, quote_type=quote_type, index_flag=index_flag)

    def count_quote_subscriptions(self, account: str | None = None) -> int:
        """Return the number of stored quote subscription rows."""
        return len(self.list_quote_subscriptions(account=account))

    # -- M6 recovery helpers ----------------------------------------------

    def get_unfinished_stock_orders(self) -> list[dict[str, Any]]:
        """Return M4 orders requiring reconciliation, including uncertain timeouts."""
        rows = self._fetchall("SELECT * FROM stock_orders ORDER BY created_at, client_order_id")
        result = []
        for row in rows:
            item = self._stock_order_row_to_dict(row)
            if item["status"] not in {"FILLED", "CANCELLED", "REJECTED", "FAILED"} or _is_uncertain_timeout(item):
                result.append(item)
        return result

    def list_unresolved_recovery(self) -> list[dict[str, Any]]:
        """Return unresolved/unknown orders from both legacy and M4 tables."""
        items: list[dict[str, Any]] = []
        for row in self._fetchall(
            "SELECT * FROM orders WHERE status = 'NEED_MANUAL_REVIEW' ORDER BY id"
        ):
            item = self._row_to_dict(row)
            items.append({"source": "orders", **item})
        for row in self._fetchall(
            "SELECT * FROM stock_orders WHERE status = 'NEED_MANUAL_REVIEW' ORDER BY created_at, client_order_id"
        ):
            item = self._stock_order_row_to_dict(row)
            items.append({"source": "stock_orders", **item})
        return items

    def resolve_stock_order(
        self,
        client_order_id: str,
        status: str,
        order_no: str | None = None,
        trade_date: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        """Manually resolve an unknown M4 stock order."""
        status = _validate_recovery_status(status)
        row = self.get_stock_order(client_order_id)
        if row is None:
            return None
        if _is_mock_order_row(row) and str(status).upper() == "FILLED":
            raise MockAccountError(
                "mock FILLED resolution must use settle_mock_fill",
                "MOCK_SETTLEMENT_REQUIRED",
            )
        data = dict(row.get("data") or {})
        data["need_manual_review"] = False
        if note:
            data["resolve_note"] = note
        self.update_stock_order(
            client_order_id,
            status=status,
            order_no=order_no,
            trade_date=trade_date,
            data=data,
        )
        return self.get_stock_order(client_order_id)

    def resolve_legacy_order(
        self,
        order_no: str,
        status: str,
        trade_date: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        """Manually resolve an unknown M3 legacy order by order_no."""
        status = _validate_recovery_status(status, legacy=True)
        rows = self.get_orders(order_no=order_no, trade_date=trade_date)
        if not rows:
            return None
        row = rows[0]
        data = dict(row.get("data") or {})
        data["need_manual_review"] = False
        if note:
            data["resolve_note"] = note
        with self._connect() as conn:
            conn.execute(
                "UPDATE orders SET status = ?, data = ?, created_at = ? WHERE id = ?",
                (status, _json_dumps(data), _now(), row["id"]),
            )
        resolved = self.get_orders(order_no=order_no, trade_date=trade_date)
        return resolved[0] if resolved else None

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


def _validate_recovery_status(status: Any, legacy: bool = False) -> str:
    value = str(status or "").strip().upper()
    if legacy:
        allowed = _FINAL_ORDER_STATUSES | {"0"}
        if value not in allowed:
            raise ValueError(f"invalid recovery status: {status!r}")
        return value
    if value not in _VALID_STOCK_ORDER_STATUSES:
        raise ValueError(f"invalid recovery status: {status!r}")
    return value


def _is_uncertain_timeout(row: dict[str, Any]) -> bool:
    data = row.get("data") or {}
    if not isinstance(data, dict):
        return False
    if data.get("execution_uncertain") is True:
        return True
    return row.get("status") == "FAILED" and "timed out" in str(data.get("error") or "").lower()


def _is_mock_order_row(row: dict[str, Any]) -> bool:
    request = row.get("request") or {}
    data = row.get("data") or {}
    return bool(request.get("mock") or data.get("mock"))


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


__all__ = ["StateStore", "is_mock_account"]
