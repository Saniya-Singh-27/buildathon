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

BUDGET_EXHAUSTED_POINTS = 3
BUDGET_HIGH_PCT_POINTS = 2       # budget_percentage >= 50
BUDGET_MED_PCT_POINTS = 1        # budget_percentage >= 25

DEVIATION_HIGH_POINTS = 2        # category_deviation_pct >= 75
DEVIATION_MED_POINTS = 1         # category_deviation_pct >= 30

RECENT_HIGH_POINTS = 2           # recent purchases well above usual pace
RECENT_MED_POINTS = 1            # recent purchases somewhat above usual pace

SIZE_HIGH_POINTS = 2             # purchase_size_ratio >= 3
SIZE_MED_POINTS = 1              # purchase_size_ratio >= 1.75


def _pretty_category(category: str) -> str:
    return category.replace("_", " ")


def _check_budget(analysis: dict) -> tuple[int, str | None]:
    if analysis["budget_already_exhausted"]:
        over_by = abs(analysis["remaining_discretionary_budget"])
        return (
            BUDGET_EXHAUSTED_POINTS,
            f"you're already Rs {over_by:,.0f} over your discretionary budget this month",
        )

    bp = analysis["budget_percentage"]
    if bp is None:
        return 0, None
    if bp >= 50:
        return BUDGET_HIGH_PCT_POINTS, f"this purchase uses {bp:.0f}% of your remaining fun budget"
    if bp >= 25:
        return BUDGET_MED_PCT_POINTS, f"this purchase uses {bp:.0f}% of your remaining fun budget"
    return 0, None


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
