"""
Spending Analyzer (Phase 3).

Turns raw transaction history into structured, explainable numbers about
a candidate purchase. Every function here does one calculation and
returns a plain number/DataFrame - no verdicts, no judgment calls. The
Decision Engine (Phase 4) is what turns these numbers into BUY / WAIT /
DON'T BUY. Keeping the split means every figure the AI later talks about
traces back to a specific, inspectable calculation here.
"""

from datetime import timedelta

import pandas as pd

from data_loader import current_month_spend, spend_by_category


def category_monthly_spend(df: pd.DataFrame, category: str, reference_date) -> float:
    """Category spend from the start of reference_date's month through reference_date."""
    mask = (
        (df["category"] == category)
        & (df["date"].dt.year == reference_date.year)
        & (df["date"].dt.month == reference_date.month)
        & (df["date"] <= reference_date)
    )
    return float(df.loc[mask, "amount"].sum())


def average_monthly_category_spend(df: pd.DataFrame, category: str, reference_date) -> float | None:
    """The category's 'normal' monthly spend, averaged over full prior months.

    The current (in-progress) month is excluded so a partial month doesn't
    get compared against itself. Returns None if there's no prior history
    for this category to establish a baseline.
    """
    current_period = pd.Period(reference_date, freq="M")
    history = df[df["category"] == category].copy()
    if history.empty:
        return None

    history["period"] = history["date"].dt.to_period("M")
    prior = history[history["period"] < current_period]
    if prior.empty:
        return None

    monthly_totals = prior.groupby("period")["amount"].sum()
    return float(monthly_totals.mean())


def recent_spending(df: pd.DataFrame, days: int, reference_date) -> float:
    """Total spend across all categories in the trailing `days` window."""
    window_start = reference_date - timedelta(days=days)
    mask = (df["date"] > window_start) & (df["date"] <= reference_date)
    return float(df.loc[mask, "amount"].sum())


def recent_similar_purchases(df: pd.DataFrame, category: str, days: int, reference_date) -> pd.DataFrame:
    """Purchases in the same category within the trailing `days` window."""
    window_start = reference_date - timedelta(days=days)
    mask = (
        (df["category"] == category)
        & (df["date"] > window_start)
        & (df["date"] <= reference_date)
    )
    return df.loc[mask, ["date", "merchant", "amount"]].sort_values("date", ascending=False)


def purchase_frequency_per_week(df: pd.DataFrame, category: str) -> float:
    """Average number of purchases per week in this category, over all observed history."""
    history = df[df["category"] == category]
    if history.empty:
        return 0.0
    span_days = (df["date"].max() - df["date"].min()).days
    span_weeks = max(span_days / 7, 1)
    return float(len(history) / span_weeks)


def average_purchase_amount(df: pd.DataFrame, category: str) -> float | None:
    """Mean historical transaction amount in this category, for sizing a new purchase against."""
    history = df[df["category"] == category]
    if history.empty:
        return None
    return float(history["amount"].mean())


def remaining_discretionary_budget(
    df: pd.DataFrame, discretionary_budget: float, essential_categories: set, reference_date
) -> float:
    """Discretionary budget left this month, after this month's non-essential spend so far."""
    this_month = df[
        (df["date"].dt.year == reference_date.year)
        & (df["date"].dt.month == reference_date.month)
        & (df["date"] <= reference_date)
    ]
    discretionary_spend = this_month.loc[~this_month["category"].isin(essential_categories), "amount"].sum()
    return float(discretionary_budget - discretionary_spend)


def spending_deviation_pct(current_spend: float, normal_spend: float | None) -> float | None:
    """How far current-month category spend is from the historical monthly average, as a %.

    Returns None when there's no baseline to compare against (new category).
    """
    if normal_spend is None or normal_spend == 0:
        return None
    return round((current_spend - normal_spend) / normal_spend * 100, 1)


def analyze_purchase(
    df: pd.DataFrame,
    category: str,
    purchase_price: float,
    monthly_budget: float,
    discretionary_budget: float,
    essential_categories: set,
    recent_window_days: int = 14,
    product_name: str | None = None,
    reference_date=None,
) -> dict:
    """Assemble every calculated feature the Decision Engine needs into one structured dict."""
    reference_date = reference_date or df["date"].max()

    category_spend_this_month = category_monthly_spend(df, category, reference_date)
    normal_category_spend = average_monthly_category_spend(df, category, reference_date)
    similar = recent_similar_purchases(df, category, recent_window_days, reference_date)
    avg_purchase_amount = average_purchase_amount(df, category)
    remaining_budget = remaining_discretionary_budget(
        df, discretionary_budget, essential_categories, reference_date
    )

    budget_percentage = round(purchase_price / remaining_budget * 100, 1) if remaining_budget > 0 else None
    purchase_size_ratio = (
        round(purchase_price / avg_purchase_amount, 2) if avg_purchase_amount else None
    )

    return {
        "product_name": product_name,
        "category": category,
        "purchase_price": purchase_price,
        "as_of": reference_date.strftime("%Y-%m-%d"),
        "monthly_budget": monthly_budget,
        "discretionary_budget": discretionary_budget,
        "current_month_total_spend": current_month_spend(df, reference_date),
        "remaining_discretionary_budget": round(remaining_budget, 2),
        "budget_already_exhausted": remaining_budget <= 0,
        "budget_percentage": budget_percentage,
        "category_spend_this_month": round(category_spend_this_month, 2),
        "normal_category_spend": round(normal_category_spend, 2) if normal_category_spend else None,
        "category_deviation_pct": spending_deviation_pct(category_spend_this_month, normal_category_spend),
        "recent_similar_purchases_count": int(len(similar)),
        "recent_similar_purchases": similar.assign(
            date=similar["date"].dt.strftime("%Y-%m-%d %H:%M")
        ).to_dict(orient="records"),
        "recent_window_days": recent_window_days,
        "purchase_frequency_per_week": round(purchase_frequency_per_week(df, category), 2),
        "average_category_purchase_amount": round(avg_purchase_amount, 2) if avg_purchase_amount else None,
        "purchase_size_ratio": purchase_size_ratio,
        "is_unusually_large": bool(purchase_size_ratio and purchase_size_ratio >= 1.75),
        "spend_by_category_all_time": spend_by_category(df).round(2).to_dict(),
    }
