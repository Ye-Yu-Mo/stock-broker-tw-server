"""M6 leftover fixes: trades multi-fill and quote index_flag support."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from stock_broker_tw.state.store import MockAccountError, StateStore


def test_trades_saves_multiple_fills_for_same_order_and_date(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_trades(
        [
            {"order_no": "H00001", "trade_date": "2026/08/27", "company_no": "2330", "match_seq": 1, "qty": 10},
            {"order_no": "H00001", "trade_date": "2026/08/27", "company_no": "2330", "match_seq": 2, "qty": 20},
        ]
    )
    trades = store.get_trades(order_no="H00001", trade_date="2026/08/27")
    assert len(trades) == 2
    assert {t["match_seq"] for t in trades} == {1, 2}


def test_claim_stock_order_is_atomic_and_idempotent(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    request = {
        "client_order_id": "C-CLAIM",
        "action": "new",
        "account": "MOCK-STORE",
        "stk_code": "2330",
        "quantity": 10,
        "mock": True,
    }

    claimed, first = store.claim_stock_order(
        client_order_id="C-CLAIM",
        request=request,
        account="MOCK-STORE",
        action="new",
        mock=True,
    )
    claimed_again, second = store.claim_stock_order(
        client_order_id="C-CLAIM",
        request=request,
        account="MOCK-STORE",
        action="new",
        mock=True,
    )

    assert claimed is True
    assert claimed_again is False
    assert first["status"] == "PENDING"
    assert second["client_order_id"] == "C-CLAIM"


def test_claim_stock_order_is_atomic_under_concurrency(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    store = StateStore(tmp_path / "state.db")
    request = {
        "client_order_id": "C-CONCURRENT",
        "action": "new",
        "account": "MOCK-STORE",
        "stk_code": "2330",
        "quantity": 1,
        "mock": True,
    }

    def claim():
        return store.claim_stock_order(
            client_order_id="C-CONCURRENT",
            request=request,
            account="MOCK-STORE",
            action="new",
            mock=True,
        )[0]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _index: claim(), range(8)))

    assert sum(results) == 1
    assert len(store.list_stock_orders()) == 1


def test_expired_mock_claim_can_be_reclaimed(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "lease.db")
    request = {
        "client_order_id": "MOCK-LEASE",
        "account": "MOCK-LEASE",
        "action": "new",
        "stk_code": "2330",
        "quantity": 1,
        "mock": True,
    }
    first_claimed, _ = store.claim_stock_order(
        "MOCK-LEASE",
        request,
        account="MOCK-LEASE",
        action="new",
        mock=True,
        execution_id="execution-1",
        lease_seconds=0.01,
    )
    time.sleep(0.02)

    second_claimed, row = store.claim_stock_order(
        "MOCK-LEASE",
        request,
        account="MOCK-LEASE",
        action="new",
        mock=True,
        execution_id="execution-2",
        lease_seconds=1.0,
    )

    assert first_claimed is True
    assert second_claimed is True
    assert row["data"]["execution"]["id"] == "execution-2"
    assert row["data"]["execution"]["attempt"] == 2


    store = StateStore(tmp_path / "state.db")
    store.init_mock_account("MOCK-STORE", cash=10_000, positions=[])
    request = {
        "client_order_id": "MOCK-SETTLE",
        "action": "new",
        "account": "MOCK-STORE",
        "stk_code": "2330",
        "side": "B",
        "price": 100,
        "quantity": 10,
        "mock": True,
    }
    store.claim_stock_order(
        client_order_id="MOCK-SETTLE",
        request=request,
        account="MOCK-STORE",
        action="new",
        mock=True,
    )

    result = store.settle_mock_fill(
        client_order_id="MOCK-SETTLE",
        account="MOCK-STORE",
        side="B",
        stk_code="2330",
        quantity=10,
        price=101,
        order_no="MOCK-ORDER-1",
        trade_date="2026/09/04",
        data={"mock": True, "fill_price": 101},
    )

    assert result["status"] == "FILLED"
    assert result["data"]["fill_price"] == 101
    assert len(store.get_trades(order_no="MOCK-ORDER-1")) == 1
    assert store.get_mock_account("MOCK-STORE")["cash"] == 8_990


def test_mock_settlement_rolls_back_when_trade_insert_fails(tmp_path: Path, monkeypatch) -> None:
    store = StateStore(tmp_path / "state.db")
    store.init_mock_account("MOCK-STORE", cash=10_000, positions=[])
    request = {
        "client_order_id": "MOCK-ROLLBACK",
        "action": "new",
        "account": "MOCK-STORE",
        "stk_code": "2330",
        "side": "B",
        "quantity": 10,
        "mock": True,
    }
    store.claim_stock_order(
        client_order_id="MOCK-ROLLBACK",
        request=request,
        account="MOCK-STORE",
        action="new",
        mock=True,
    )

    original_connect = store._connect

    class ConnectionProxy:
        def __init__(self, connection):
            self.connection = connection

        def __enter__(self):
            self.connection.__enter__()
            return self

        def __exit__(self, *args):
            return self.connection.__exit__(*args)

        def execute(self, sql, params=()):
            if "INSERT INTO trades" in sql:
                raise RuntimeError("trade write failed")
            return self.connection.execute(sql, params)

    monkeypatch.setattr(
        store,
        "_connect",
        lambda: ConnectionProxy(original_connect()),
    )
    with pytest.raises(RuntimeError, match="trade write failed"):
        store.settle_mock_fill(
            client_order_id="MOCK-ROLLBACK",
            account="MOCK-STORE",
            side="B",
            stk_code="2330",
            quantity=10,
            price=101,
            order_no="MOCK-ORDER-ROLLBACK",
            trade_date="2026/09/04",
            data={"mock": True},
        )

    assert store.get_mock_account("MOCK-STORE")["cash"] == 10_000
    assert store.get_stock_order("MOCK-ROLLBACK")["status"] == "PENDING"
    assert store.get_trades(order_no="MOCK-ORDER-ROLLBACK") == []


def test_quote_subscriptions_support_index_flag(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.save_quote_subscription(
        account="A",
        quote_type="watchlist",
        symbol="2330",
        market_type="TWSE",
        index_flag=7,
    )
    store.save_quote_subscription(
        account="A",
        quote_type="watchlist",
        symbol="2330",
        market_type="TWSE",
        index_flag=8,
    )
    rows = store.list_quote_subscriptions(account="A", quote_type="watchlist")
    assert len(rows) == 2
    assert {(r["symbol"], r["index_flag"]) for r in rows} == {("2330", 7), ("2330", 8)}

    store.delete_quote_subscription(
        account="A",
        quote_type="watchlist",
        symbol="2330",
        market_type="TWSE",
        index_flag=7,
    )
    rows = store.list_quote_subscriptions(account="A", quote_type="watchlist")
    assert len(rows) == 1
    assert rows[0]["index_flag"] == 8


def test_null_index_flag_subscription_is_idempotent(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "null-index.db")

    store.save_quote_subscription("A", "stock_tick", "2330", "TWSE")
    store.save_quote_subscription("A", "stock_tick", "2330", "TWSE")

    rows = store.list_quote_subscriptions(account="A", quote_type="stock_tick")
    assert len(rows) == 1


def test_mock_reinitialize_with_history_is_rejected(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "mock-reinit.db")
    store.init_mock_account("MOCK-REINIT", cash=10_000.0, positions=[])
    request = {
        "client_order_id": "MOCK-REINIT-001",
        "account": "MOCK-REINIT",
        "action": "new",
        "stk_code": "2330",
        "side": "B",
        "quantity": 1,
        "mock": True,
    }
    store.claim_stock_order("MOCK-REINIT-001", request, "MOCK-REINIT", "new", mock=True)
    store.settle_mock_fill(
        "MOCK-REINIT-001",
        "MOCK-REINIT",
        "B",
        "2330",
        1,
        101.0,
        "MOCK-ORDER-1",
        "2026/09/08",
    )

    with pytest.raises(MockAccountError, match="history"):
        store.init_mock_account("MOCK-REINIT", cash=1_000.0, positions=[])

    assert store.get_mock_account("MOCK-REINIT")["cash"] == 9_899.0


def test_invalid_recovery_status_is_rejected_without_writing(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "recovery-status.db")
    store.save_stock_order(
        client_order_id="RECOVERY001",
        request={"client_order_id": "RECOVERY001"},
        status="NEED_MANUAL_REVIEW",
        account="S98875005091",
        action="new",
    )

    with pytest.raises(ValueError, match="status"):
        store.resolve_stock_order("RECOVERY001", status="BOGUS")

    assert store.get_stock_order("RECOVERY001")["status"] == "NEED_MANUAL_REVIEW"


def test_mock_account_namespace_and_finite_values(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "mock.db")

    with pytest.raises(MockAccountError, match="MOCK-"):
        store.init_mock_account("REAL-ACCOUNT", cash=100.0, positions=[])
    for cash in (float("nan"), float("inf"), -1.0, "not-a-number"):
        with pytest.raises(MockAccountError):
            store.init_mock_account("MOCK-VALID", cash=cash, positions=[])
    with pytest.raises(MockAccountError):
        store.init_mock_account(
            "MOCK-VALID",
            cash=100.0,
            positions=[{"stk_code": "2330", "quantity": 1, "avg_price": float("inf")}],
        )


def test_mock_account_active_flag_migrates_and_deactivates(tmp_path: Path) -> None:
    import sqlite3

    db = tmp_path / "old_mock.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE mock_accounts (
            account TEXT PRIMARY KEY,
            cash REAL NOT NULL,
            positions TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO mock_accounts (account, cash, positions, created_at, updated_at)
        VALUES ('MOCK-OLD', 100.0, '{}', '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        """
    )
    conn.commit()
    conn.close()

    store = StateStore(db)
    assert store.get_mock_account("MOCK-OLD")["active"] is True
    assert store.deactivate_mock_account("MOCK-OLD") is True
    assert store.get_mock_account("MOCK-OLD")["active"] is False


def test_mock_fill_rejects_non_finite_values_before_writing(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "mock_fill.db")
    store.init_mock_account("MOCK-FILL", cash=100.0, positions=[])
    request = {
        "client_order_id": "MOCK-FILL-001",
        "account": "MOCK-FILL",
        "action": "new",
        "stk_code": "2330",
        "quantity": 1,
        "mock": True,
    }
    store.claim_stock_order("MOCK-FILL-001", request, "MOCK-FILL", "new", mock=True)

    with pytest.raises(MockAccountError):
        store.settle_mock_fill(
            client_order_id="MOCK-FILL-001",
            account="MOCK-FILL",
            side="B",
            stk_code="2330",
            quantity=1,
            price=float("nan"),
            order_no="MOCK-FILL-ORDER",
            trade_date="2026/09/07",
        )

    assert store.get_mock_account("MOCK-FILL")["cash"] == 100.0
    assert store.get_stock_order("MOCK-FILL-001")["status"] == "PENDING"
    assert store.get_trades(order_no="MOCK-FILL-ORDER") == []


def test_trades_old_unique_schema_is_migrated(tmp_path: Path) -> None:
    import sqlite3

    db = tmp_path / "old.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            account TEXT,
            trade_date TEXT,
            company_no TEXT,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(order_no, trade_date)
        );
        INSERT INTO trades (order_no, account, trade_date, company_no, data, created_at)
        VALUES ('H00001', 'A', '2026/08/27', '2330', '{}', '2026-01-01T00:00:00');
        """
    )
    conn.commit()
    conn.close()

    store = StateStore(db)
    store.save_trades(
        [
            {"order_no": "H00001", "trade_date": "2026/08/27", "match_seq": 2, "qty": 20},
        ]
    )
    assert len(store.get_trades(order_no="H00001")) == 2


def test_quote_subscriptions_old_schema_is_migrated(tmp_path: Path) -> None:
    import sqlite3

    db = tmp_path / "old_quote.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE quote_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            quote_type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            market_type TEXT NOT NULL DEFAULT 'TWSE',
            created_at TEXT NOT NULL,
            UNIQUE(account, quote_type, symbol, market_type)
        );
        INSERT INTO quote_subscriptions (account, quote_type, symbol, market_type, created_at)
        VALUES ('A', 'watchlist', '2330', 'TWSE', '2026-01-01T00:00:00');
        """
    )
    conn.commit()
    conn.close()

    store = StateStore(db)
    store.save_quote_subscription(
        account="A",
        quote_type="watchlist",
        symbol="2330",
        market_type="TWSE",
        index_flag=8,
    )
    rows = store.list_quote_subscriptions(account="A", quote_type="watchlist")
    assert len(rows) == 2
