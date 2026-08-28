"""M6 leftover fixes: trades multi-fill and quote index_flag support."""

from __future__ import annotations

from pathlib import Path

from stock_broker_tw.state.store import StateStore


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
