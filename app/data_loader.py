"""
Loads the synthetic transaction history and exposes a few basic,
transparent calculations on top of it (totals, category breakdown,
current-month spend). This is intentionally simple - it is not the
spending analyzer (remaining budget, deviation, duplicate detection)
that comes in Phase 3.
"""

from pathlib import Path

import pandas as pd

TRANSACTIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"


def load_transactions(path: Path = TRANSACTIONS_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def total_spent(df: pd.DataFrame) -> float:
    return float(df["amount"].sum())


def transaction_count(df: pd.DataFrame) -> int:
    return int(len(df))


def average_transaction(df: pd.DataFrame) -> float:
    return float(df["amount"].mean())


def spend_by_category(df: pd.DataFrame) -> pd.Series:
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)


def date_range(df: pd.DataFrame):
    return df["date"].min(), df["date"].max()


def current_month_spend(df: pd.DataFrame, reference_date=None) -> float:
    """Spend from the start of reference_date's month through reference_date itself.

    Defaults to the most recent date in the dataset rather than the
    real wall-clock date, so this keeps working correctly even if the
    dataset isn't regenerated on the exact day the app is demoed.
    Deliberately excludes anything after reference_date - a "spent so
    far this month" figure should never include the rest of the month.
    """
    reference_date = reference_date or df["date"].max()
    mask = (
        (df["date"].dt.year == reference_date.year)
        & (df["date"].dt.month == reference_date.month)
        & (df["date"] <= reference_date)
    )
    return float(df.loc[mask, "amount"].sum())


def summary(df: pd.DataFrame) -> dict:
    start, end = date_range(df)
    return {
        "transaction_count": transaction_count(df),
        "total_spent": total_spent(df),
        "average_transaction": average_transaction(df),
        "current_month_spend": current_month_spend(df),
        "date_range": (start, end),
        "spend_by_category": spend_by_category(df),
    }
