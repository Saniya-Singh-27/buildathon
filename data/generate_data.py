"""
Generates a synthetic transaction history for one demo user.

Not real financial data. Run this file directly to (re)create
data/transactions.csv:

    python3 data/generate_data.py

It builds three kinds of transactions and merges them:
  1. Recurring subscriptions (Netflix, Spotify, etc.) - same merchant,
     same amount, roughly the same day every month.
  2. Day-to-day random purchases - frequency and category mix shift on
     weekends, food delivery skews late at night.
  3. Category "bursts" - a handful of short windows where the user buys
     several similar things close together (e.g. three tops in a week),
     which later phases use to detect duplicate-purchase behavior.
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DAYS_OF_HISTORY = 90
OUTPUT_PATH = Path(__file__).resolve().parent / "transactions.csv"

CATEGORIES = {
    "food_delivery": {
        "merchants": ["Zomato", "Swiggy", "Domino's", "Box8", "Behrouz Biryani"],
        "amount_range": (50, 160),
        "weight": 5.0,
        "weekend_boost": 1.4,
        "late_night_share": 0.35,
    },
    "clothing": {
        "merchants": ["Myntra", "Zara", "H&M", "Ajio", "Urban Outfitters"],
        "amount_range": (249, 1049),
        "weight": 1.0,
        "weekend_boost": 1.2,
    },
    "beauty": {
        "merchants": ["Nykaa", "Sephora", "The Body Shop", "Mamaearth", "Purplle"],
        "amount_range": (109, 699),
        "weight": 0.9,
        "weekend_boost": 1.1,
    },
    "entertainment": {
        "merchants": ["BookMyShow", "PVR Cinemas", "INOX", "Steam", "PlayStation Store"],
        "amount_range": (69, 420),
        "weight": 1.0,
        "weekend_boost": 1.6,
    },
    "transportation": {
        "merchants": ["Uber", "Ola", "Rapido", "Namma Metro", "Indian Oil Petrol Pump"],
        "amount_range": (25, 175),
        "weight": 3.0,
        "weekend_boost": 1.0,
    },
    "electronics": {
        "merchants": ["Amazon", "Croma", "Reliance Digital", "Apple Store"],
        "amount_range": (219, 2099),
        "weight": 0.25,
        "weekend_boost": 1.1,
    },
    "groceries": {
        "merchants": ["BigBasket", "Blinkit", "Zepto", "DMart", "Instamart"],
        "amount_range": (49, 490),
        "weight": 2.3,
        "weekend_boost": 1.1,
    },
    "fitness": {
        "merchants": ["Cult.fit", "Gold's Gym", "Decathlon", "HealthifyMe"],
        "amount_range": (109, 840),
        "weight": 0.6,
        "weekend_boost": 1.0,
    },
    "travel": {
        "merchants": ["MakeMyTrip", "IRCTC", "RedBus", "Airbnb", "IndiGo"],
        "amount_range": (109, 1750),
        "weight": 0.3,
        "weekend_boost": 1.0,
    },
}

# Rare, genuinely expensive one-offs (a new phone, a weekend trip) layered on
# top of the regular category draws so the dataset has real high-ticket
# outliers without dragging up the everyday average.
BIG_TICKET_ITEMS = [
    {"category": "electronics", "merchants": ["Amazon", "Croma", "Apple Store"], "amount_range": (4000, 14000)},
    {"category": "travel", "merchants": ["MakeMyTrip", "Airbnb", "IndiGo"], "amount_range": (3000, 11000)},
]
NUM_BIG_TICKET_EVENTS = 3

RECURRING_SUBSCRIPTIONS = [
    {"merchant": "Netflix", "amount": 649, "day_of_month": 3},
    {"merchant": "Spotify Premium", "amount": 119, "day_of_month": 5},
    {"merchant": "Amazon Prime", "amount": 299, "day_of_month": 12},
    {"merchant": "iCloud+", "amount": 75, "day_of_month": 8},
    {"merchant": "YouTube Premium", "amount": 149, "day_of_month": 18},
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking"]
PAYMENT_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

BURST_CATEGORIES = ["clothing", "beauty", "food_delivery", "entertainment"]


def _sample_amount(rng, low, high):
    mode = low + (high - low) * 0.25
    return round(float(rng.triangular(low, mode, high)))


def _sample_hour(rng, category):
    if category == "food_delivery" and rng.random() < CATEGORIES[category]["late_night_share"]:
        return int(rng.choice([22, 23, 0, 1]))
    return int(rng.integers(8, 23))


def build_recurring_transactions(rng, start_date, end_date):
    rows = []
    month_cursor = start_date.replace(day=1)
    while month_cursor <= end_date:
        for sub in RECURRING_SUBSCRIPTIONS:
            try:
                charge_date = month_cursor.replace(day=sub["day_of_month"])
            except ValueError:
                continue
            if start_date <= charge_date <= end_date:
                hour = int(rng.integers(9, 21))
                rows.append(
                    {
                        "date": charge_date.replace(hour=hour, minute=int(rng.integers(0, 59))),
                        "merchant": sub["merchant"],
                        "category": "subscriptions",
                        "amount": sub["amount"],
                        "payment_method": "Credit Card",
                    }
                )
        if month_cursor.month == 12:
            month_cursor = month_cursor.replace(year=month_cursor.year + 1, month=1)
        else:
            month_cursor = month_cursor.replace(month=month_cursor.month + 1)
    return rows


def build_daily_transactions(rng, start_date, end_date):
    rows = []
    categories = list(CATEGORIES.keys())
    base_weights = np.array([CATEGORIES[c]["weight"] for c in categories])

    day = start_date
    while day <= end_date:
        is_weekend = day.weekday() >= 5
        daily_lambda = 7.5 if is_weekend else 5.5
        num_transactions = rng.poisson(daily_lambda)

        weights = base_weights.copy()
        if is_weekend:
            boosts = np.array([CATEGORIES[c]["weekend_boost"] for c in categories])
            weights = weights * boosts
        weights = weights / weights.sum()

        for _ in range(num_transactions):
            category = rng.choice(categories, p=weights)
            spec = CATEGORIES[category]
            merchant = rng.choice(spec["merchants"])
            amount = _sample_amount(rng, *spec["amount_range"])
            hour = _sample_hour(rng, category)
            minute = int(rng.integers(0, 59))
            payment = rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
            rows.append(
                {
                    "date": day.replace(hour=hour, minute=minute),
                    "merchant": merchant,
                    "category": category,
                    "amount": amount,
                    "payment_method": payment,
                }
            )
        day += timedelta(days=1)
    return rows


def build_burst_transactions(rng, start_date, end_date):
    rows = []
    num_bursts = 6
    for _ in range(num_bursts):
        category = rng.choice(BURST_CATEGORIES)
        spec = CATEGORIES[category]
        window_start_offset = int(rng.integers(0, (end_date - start_date).days - 14))
        window_start = start_date + timedelta(days=window_start_offset)
        burst_size = int(rng.integers(3, 6))
        for _ in range(burst_size):
            offset = int(rng.integers(0, 12))
            purchase_day = window_start + timedelta(days=offset)
            if purchase_day > end_date:
                continue
            merchant = rng.choice(spec["merchants"])
            amount = _sample_amount(rng, *spec["amount_range"])
            hour = _sample_hour(rng, category)
            minute = int(rng.integers(0, 59))
            payment = rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
            rows.append(
                {
                    "date": purchase_day.replace(hour=hour, minute=minute),
                    "merchant": merchant,
                    "category": category,
                    "amount": amount,
                    "payment_method": payment,
                }
            )
    return rows


def build_big_ticket_transactions(rng, start_date, end_date):
    rows = []
    for _ in range(NUM_BIG_TICKET_EVENTS):
        item = BIG_TICKET_ITEMS[rng.integers(0, len(BIG_TICKET_ITEMS))]
        offset = int(rng.integers(0, (end_date - start_date).days))
        purchase_day = start_date + timedelta(days=offset)
        merchant = rng.choice(item["merchants"])
        amount = _sample_amount(rng, *item["amount_range"])
        hour = int(rng.integers(10, 21))
        minute = int(rng.integers(0, 59))
        payment = rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
        rows.append(
            {
                "date": purchase_day.replace(hour=hour, minute=minute),
                "merchant": merchant,
                "category": item["category"],
                "amount": amount,
                "payment_method": payment,
            }
        )
    return rows


def generate(seed=SEED, days=DAYS_OF_HISTORY, end_date=None):
    rng = np.random.default_rng(seed)
    end_date = (end_date or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)

    rows = []
    rows += build_recurring_transactions(rng, start_date, end_date)
    rows += build_daily_transactions(rng, start_date, end_date)
    rows += build_burst_transactions(rng, start_date, end_date)
    rows += build_big_ticket_transactions(rng, start_date, end_date)

    df = pd.DataFrame(rows)
    df = df.sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def main():
    df = generate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} transactions to {OUTPUT_PATH}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total spend: Rs {df['amount'].sum():,.0f}")

    parsed = df.copy()
    parsed["date"] = pd.to_datetime(parsed["date"])
    parsed["month"] = parsed["date"].dt.to_period("M")
    print("\nSpend by month:")
    print(parsed.groupby("month")["amount"].sum().round(0))
    print("\nSpend by category (full range):")
    print(parsed.groupby("category")["amount"].sum().sort_values(ascending=False).round(0))


if __name__ == "__main__":
    main()
