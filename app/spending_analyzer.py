"""
Spending Analyzer (Phase 3).

Turns raw transaction history into structured, explainable numbers about
a candidate purchase. Every function here does one calculation and
returns a plain number/DataFrame - no verdicts, no judgment calls. The
Decision Engine (Phase 4) is what turns these numbers into BUY / WAIT /
DON'T BUY. Keeping the split means every figure the AI later talks about
traces back to a specific, inspectable calculation here.
"""

import calendar
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


def expected_recent_purchases(history_df: pd.DataFrame, category: str, window_days: int, reference_date) -> float:
    """How many category purchases the pre-burst baseline pace would predict for the window.

    Deliberately excludes the window itself from the rate calculation -
    otherwise a burst inflates its own baseline and ends up looking
    "normal" simply because it's included in the average it's compared
    against. Returns 0.0 when there's no pre-window history to establish
    a pace from (e.g. a brand-new category).
    """
    window_start = reference_date - timedelta(days=window_days)
    prior = history_df[(history_df["category"] == category) & (history_df["date"] <= window_start)]
    if prior.empty:
        return 0.0
    span_days = (window_start - history_df["date"].min()).days
    span_weeks = max(span_days / 7, 1)
    rate_per_week = len(prior) / span_weeks
    return float(rate_per_week * (window_days / 7))


def purchase_frequency_per_week(history_df: pd.DataFrame, category: str) -> float:
    """Average number of purchases per week in this category, over history up to now.

    `history_df` must already be trimmed to transactions on or before the
    reference date - otherwise this would be judging today's purchase
    using a "normal pace" computed partly from the future.
    """
    history = history_df[history_df["category"] == category]
    if history.empty:
        return 0.0
    span_days = (history_df["date"].max() - history_df["date"].min()).days
    span_weeks = max(span_days / 7, 1)
    return float(len(history) / span_weeks)


def average_purchase_amount(history_df: pd.DataFrame, category: str) -> float | None:
    """Mean historical transaction amount in this category, for sizing a new purchase against.

    `history_df` must already be trimmed to on-or-before the reference date.
    """
    history = history_df[history_df["category"] == category]
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


def discretionary_spend_this_month(
    df: pd.DataFrame, essential_categories: set, reference_date
) -> float:
    """Non-essential spend from the start of reference_date's month through reference_date."""
    this_month = df[
        (df["date"].dt.year == reference_date.year)
        & (df["date"].dt.month == reference_date.month)
        & (df["date"] <= reference_date)
    ]
    return float(this_month.loc[~this_month["category"].isin(essential_categories), "amount"].sum())


def month_progress_pct(reference_date) -> float:
    """How far through the calendar month reference_date is, as a percentage.

    The budget is a monthly allowance, so "how much have you used" only means
    something next to "how much of the month has gone". Being 90% through the
    budget is unremarkable on the 28th and alarming on the 3rd.
    """
    days_in_month = calendar.monthrange(reference_date.year, reference_date.month)[1]
    return float(reference_date.day / days_in_month * 100)


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
    # Everything historical must stop at reference_date - a purchase check "today"
    # can never be informed by transactions that haven't happened yet.
    history_df = df[df["date"] <= reference_date]

    category_spend_this_month = category_monthly_spend(df, category, reference_date)
    normal_category_spend = average_monthly_category_spend(df, category, reference_date)
    similar = recent_similar_purchases(df, category, recent_window_days, reference_date)
    expected_recent = expected_recent_purchases(history_df, category, recent_window_days, reference_date)
    avg_purchase_amount = average_purchase_amount(history_df, category)
    remaining_budget = remaining_discretionary_budget(
        df, discretionary_budget, essential_categories, reference_date
    )

    budget_percentage = round(purchase_price / remaining_budget * 100, 1) if remaining_budget > 0 else None

    # Budget consumption measured against how far through the month we are.
    # Raw "budget remaining" can't tell 90% spent on the 3rd from 90% spent on
    # the 28th, even though only one of those is a problem.
    spent_so_far = discretionary_spend_this_month(df, essential_categories, reference_date)
    progress_pct = month_progress_pct(reference_date)
    used_after_pct = (spent_so_far + purchase_price) / discretionary_budget * 100
    overshoot_pct = used_after_pct - progress_pct
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
        "is_essential_category": category in essential_categories,
        "current_month_total_spend": current_month_spend(df, reference_date),
        "remaining_discretionary_budget": round(remaining_budget, 2),
        "budget_already_exhausted": remaining_budget <= 0,
        "budget_percentage": budget_percentage,
        "discretionary_spend_this_month": round(spent_so_far, 2),
        "month_progress_pct": round(progress_pct, 1),
        "budget_used_after_purchase_pct": round(used_after_pct, 1),
        "budget_overshoot_pct": round(overshoot_pct, 1),
        "category_spend_this_month": round(category_spend_this_month, 2),
        "normal_category_spend": round(normal_category_spend, 2) if normal_category_spend else None,
        "category_deviation_pct": spending_deviation_pct(category_spend_this_month, normal_category_spend),
        "recent_similar_purchases_count": int(len(similar)),
        "expected_recent_purchases": round(expected_recent, 2),
        "recent_similar_purchases": similar.assign(
            date=similar["date"].dt.strftime("%Y-%m-%d %H:%M")
        ).to_dict(orient="records"),
        "recent_window_days": recent_window_days,
        "purchase_frequency_per_week": round(purchase_frequency_per_week(history_df, category), 2),
        "average_category_purchase_amount": round(avg_purchase_amount, 2) if avg_purchase_amount else None,
        "purchase_size_ratio": purchase_size_ratio,
        "is_unusually_large": bool(purchase_size_ratio and purchase_size_ratio >= 1.75),
        "spend_by_category_all_time": spend_by_category(history_df).round(2).to_dict(),
    }
