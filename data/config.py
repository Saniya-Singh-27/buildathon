"""Synthetic user profile used to generate and later analyze spending.

This is fictional demo data, not a real person's finances.
"""

USER_NAME = "Aria"
MONTHLY_INCOME = 60000
MONTHLY_BUDGET = 45000
DISCRETIONARY_BUDGET = 35000  # "fun money" allowance each month (monthly_budget minus essentials)

# Categories treated as non-negotiable essentials. Everything else counts
# against the discretionary ("fun money") budget.
ESSENTIAL_CATEGORIES = {"groceries", "transportation"}

RECENT_WINDOW_DAYS = 14  # lookback window for "similar recent purchases"
