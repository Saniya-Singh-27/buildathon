"""
SQLite persistence (Phase 7).

Four small tables: users, transactions, purchase_checks, payments.

Everything is CREATE TABLE IF NOT EXISTS and seeding only happens when a
table is actually empty, so restarting the app never wipes anything.
The synthetic CSV is treated as a one-time seed source - once it's in
the database, the database is the source of truth, and purchase checks
and payments accumulate across restarts.

Connections are opened per-operation and closed immediately. That's
deliberate: Streamlit re-runs the whole script on every interaction, and
a long-lived connection held in module state would be shared across
reruns in ways sqlite3 isn't happy about. For a single-user local demo
the cost of reconnecting is irrelevant.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "should_i_buy.db"
CSV_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"

DEFAULT_USER_ID = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    monthly_budget REAL NOT NULL,
    discretionary_budget REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,
    merchant TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    verdict TEXT NOT NULL,
    reasons TEXT NOT NULL,
    user_decision TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_check_id INTEGER NOT NULL REFERENCES purchase_checks(id),
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    reference TEXT,
    timestamp TEXT NOT NULL
);
"""


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(user_name: str, monthly_budget: float, discretionary_budget: float) -> None:
    """Create tables if missing and seed the demo user + transaction history once."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.executescript(_SCHEMA)

        existing_user = connection.execute(
            "SELECT id FROM users WHERE id = ?", (DEFAULT_USER_ID,)
        ).fetchone()
        if existing_user is None:
            connection.execute(
                "INSERT INTO users (id, name, monthly_budget, discretionary_budget) VALUES (?, ?, ?, ?)",
                (DEFAULT_USER_ID, user_name, monthly_budget, discretionary_budget),
            )

        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if transaction_count == 0 and CSV_SEED_PATH.exists():
            seed = pd.read_csv(CSV_SEED_PATH)
            seed.insert(0, "user_id", DEFAULT_USER_ID)
            seed.to_sql("transactions", connection, if_exists="append", index=False)


def load_transactions(user_id: int = DEFAULT_USER_ID) -> pd.DataFrame:
    """Transaction history for a user, in the same shape the analyzer expects."""
    with get_connection() as connection:
        df = pd.read_sql_query(
            "SELECT date, merchant, category, amount, payment_method "
            "FROM transactions WHERE user_id = ? ORDER BY date",
            connection,
            params=(user_id,),
        )
    df["date"] = pd.to_datetime(df["date"])
    return df.reset_index(drop=True)


def save_purchase_check(decision: dict, user_id: int = DEFAULT_USER_ID) -> int:
    """Record a verdict the app produced. Returns the new row's id."""
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO purchase_checks "
            "(user_id, product, price, category, verdict, reasons, user_decision, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL, ?)",
            (
                user_id,
                decision["product_name"],
                decision["purchase_price"],
                decision["category"],
                decision["verdict"],
                json.dumps(decision["reasons"]),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return int(cursor.lastrowid)


def record_user_decision(purchase_check_id: int, user_decision: str) -> None:
    """Record what the user actually did about the verdict ('waited' or 'bought_anyway')."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE purchase_checks SET user_decision = ? WHERE id = ?",
            (user_decision, purchase_check_id),
        )


def save_payment(purchase_check_id: int, amount: float, status: str, reference: str | None = None) -> int:
    """Record a (test-mode only) payment attempt against a purchase check."""
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO payments (purchase_check_id, amount, status, reference, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                purchase_check_id,
                amount,
                status,
                reference,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return int(cursor.lastrowid)


def get_purchase_checks(user_id: int = DEFAULT_USER_ID) -> pd.DataFrame:
    """Every verdict this user has been given, newest first. Used by the dashboard."""
    with get_connection() as connection:
        df = pd.read_sql_query(
            "SELECT id, product, price, category, verdict, reasons, user_decision, timestamp "
            "FROM purchase_checks WHERE user_id = ? ORDER BY id DESC",
            connection,
            params=(user_id,),
        )
    if not df.empty:
        df["reasons"] = df["reasons"].apply(json.loads)
    return df


def get_payments() -> pd.DataFrame:
    """Every recorded test payment, newest first."""
    with get_connection() as connection:
        return pd.read_sql_query(
            "SELECT id, purchase_check_id, amount, status, reference, timestamp "
            "FROM payments ORDER BY id DESC",
            connection,
        )
