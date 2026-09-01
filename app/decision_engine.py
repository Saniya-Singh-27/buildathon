"""
Decision Engine (Phase 4).

Turns the Spending Analyzer's structured numbers into one of three
verdicts: BUY, WAIT, or DONT_BUY. This is plain, deterministic Python -
a point score built from a handful of named checks, each of which
either fires or doesn't and says exactly why. No LLM involved. The AI
layer (Phase 6) only narrates what this module already decided; it
never gets to change the verdict or invent a reason.

Scoring is intentionally simple (concern points, not a trained model)
so every verdict can be explained in one sentence per check - matching
the brief's "prioritize interpretability over mathematical complexity."
"""

BUY_MAX = 1       # score <= this -> BUY
WAIT_MAX = 4       # score <= this -> WAIT, above it -> DONT_BUY

# Budget is scored on how far AHEAD OF THE MONTH this purchase would put you,
# not on the raw amount left. "Overshoot" is (budget used after this purchase)
# minus (how far through the month you are), both as percentages - so being 90%
# through the budget on the 28th scores nothing, while 90% on the 3rd scores
# heavily. See _check_budget.
BUDGET_OVERSHOOT_HIGH_POINTS = 3   # >= 50 points ahead of the month
BUDGET_OVERSHOOT_MED_POINTS = 2    # >= 25
BUDGET_OVERSHOOT_LOW_POINTS = 1    # >= 10

DEVIATION_HIGH_POINTS = 2        # category_deviation_pct >= 75
DEVIATION_MED_POINTS = 1         # category_deviation_pct >= 30

RECENT_HIGH_POINTS = 2           # recent purchases well above usual pace
RECENT_MED_POINTS = 1            # recent purchases somewhat above usual pace

SIZE_HIGH_POINTS = 2             # purchase_size_ratio >= 3
SIZE_MED_POINTS = 1              # purchase_size_ratio >= 1.75


def _pretty_category(category: str) -> str:
    return category.replace("_", " ")


def _check_budget(analysis: dict) -> tuple[int, str | None]:
    # Essentials (groceries, getting to work) are not discretionary spending,
    # so the fun-money budget is simply the wrong yardstick for them - without
    # this, the app told you not to buy groceries because you'd overspent on
    # clothes. They're still subject to every other check, so a wildly
    # oversized grocery run is still caught, just not by this one.
    if analysis.get("is_essential_category"):
        return 0, None

    # The budget is a monthly allowance, so the question isn't "how much is
    # left" but "would this put you ahead of the month". Overshoot is the gap
    # between the share of the budget you'd have used and the share of the
    # month that has passed. Judged on remaining alone, 90% spent on the 3rd
    # and 90% spent on the 28th look identical - only one of them is a problem.
    used = analysis["budget_used_after_purchase_pct"]
    elapsed = analysis["month_progress_pct"]
    overshoot = analysis["budget_overshoot_pct"]

    if overshoot >= 50:
        points = BUDGET_OVERSHOOT_HIGH_POINTS
    elif overshoot >= 25:
        points = BUDGET_OVERSHOOT_MED_POINTS
    elif overshoot >= 10:
        points = BUDGET_OVERSHOOT_LOW_POINTS
    else:
        return 0, None

    if used >= 100:
        reason = (
            f"this would put you at {used:.0f}% of your monthly fun budget - "
            f"over the whole month's allowance, and you're only {elapsed:.0f}% through it"
        )
    else:
        reason = (
            f"this would put you at {used:.0f}% of your monthly fun budget "
            f"when you're only {elapsed:.0f}% through the month"
        )
    return points, reason


def _check_deviation(analysis: dict) -> tuple[int, str | None]:
    dev = analysis["category_deviation_pct"]
    if dev is None or dev <= 0:
        return 0, None
    category = _pretty_category(analysis["category"])
    if dev >= 75:
        return DEVIATION_HIGH_POINTS, f"{category} spending is {dev:.0f}% above your normal monthly level"
    if dev >= 30:
        return DEVIATION_MED_POINTS, f"{category} spending is {dev:.0f}% above your normal monthly level"
    return 0, None


def _check_recent_purchases(analysis: dict) -> tuple[int, str | None]:
    actual = analysis["recent_similar_purchases_count"]
    if actual < 2:
        return 0, None

    window_days = analysis["recent_window_days"]
    expected = analysis["expected_recent_purchases"]
    ratio = (actual / expected) if expected > 0 else float(actual)
    category = _pretty_category(analysis["category"])
    reason = f"{actual} similar {category} purchases in the last {window_days} days"

    if ratio >= 2.5:
        return RECENT_HIGH_POINTS, reason + " - well above your usual pace"
    if ratio >= 1.5:
        return RECENT_MED_POINTS, reason + " - a bit more than usual"
    return 0, None


def _check_purchase_size(analysis: dict) -> tuple[int, str | None]:
    ratio = analysis["purchase_size_ratio"]
    if ratio is None:
        return 0, None
    category = _pretty_category(analysis["category"])
    if ratio >= 3:
        return SIZE_HIGH_POINTS, f"this is {ratio:.1f}x what you'd normally spend on {category}"
    if ratio >= 1.75:
        return SIZE_MED_POINTS, f"this is {ratio:.1f}x what you'd normally spend on {category}"
    return 0, None


CHECKS = [_check_budget, _check_deviation, _check_recent_purchases, _check_purchase_size]


def decide(analysis: dict) -> dict:
    """Run every check against the analyzer output and return a verdict + reasons.

    The returned dict deliberately mirrors the structure in the product
    spec so the UI and the AI explanation layer both have a single,
    predictable shape to read from.
    """
    score = 0
    reasons = []
    breakdown = []

    for check in CHECKS:
        points, reason = check(analysis)
        breakdown.append({"check": check.__name__.lstrip("_"), "points": points, "reason": reason})
        if points > 0 and reason:
            score += points
            reasons.append(reason)

    if score <= BUY_MAX:
        verdict = "BUY"
    elif score <= WAIT_MAX:
        verdict = "WAIT"
    else:
        verdict = "DONT_BUY"

    if not reasons:
        reasons.append("this fits comfortably within your normal spending pattern")

    return {
        "verdict": verdict,
        "score": score,
        "product_name": analysis["product_name"],
        "purchase_price": analysis["purchase_price"],
        "category": analysis["category"],
        "remaining_discretionary_budget": analysis["remaining_discretionary_budget"],
        "budget_percentage": analysis["budget_percentage"],
        "category_spending": analysis["category_spend_this_month"],
        "normal_category_spending": analysis["normal_category_spend"],
        "recent_similar_purchases": analysis["recent_similar_purchases_count"],
        "reasons": reasons,
        "score_breakdown": breakdown,
    }
