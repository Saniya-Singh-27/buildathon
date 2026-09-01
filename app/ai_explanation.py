"""
AI Explanation (Phase 6).

Turns the Decision Engine's verdict + reasons into a short, Gen-Z-voiced
reaction. The model is handed ONLY the structured facts the app already
calculated (verdict, prices, percentages, reasons) and told to narrate
them - it never invents a number, and it never gets to change the
verdict. It's explaining a decision that's already been made by plain
Python math, not making one itself.

Optional, like the rest of the AI layer: if no API key is configured,
or the call fails for any reason, a plain templated message built
directly from the same reasons is shown instead. The result screen
always has something to show.
"""

import json

from google.genai import types

from ai_client import MODEL, get_client, is_configured

_EXPLANATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "headline": {
            "type": "STRING",
            "description": "One short, punchy, playful reaction to the verdict - max ~8 words",
        },
        "commentary": {
            "type": "STRING",
            "description": (
                "2-4 sentences explaining the verdict, in a witty Gen-Z voice. Must use ONLY "
                "the numbers/facts given - never invent a figure. Supportive, never shaming."
            ),
        },
        "closing_line": {
            "type": "STRING",
            "description": "One short suggested next step, matching the verdict",
        },
    },
    "required": ["headline", "commentary", "closing_line"],
}

_SYSTEM_INSTRUCTION = """You are a Gen-Z best friend who happens to be great with money - witty, \
playful, a little chaotic, always supportive, never judgmental. You're reacting to a purchase \
decision a calculator already made (BUY, WAIT, or DONT_BUY) - you're not making the call \
yourself, just explaining it in your voice.

Rules:
- Use ONLY the numbers and facts you're given. Never invent a number, percentage, category, or \
fact that wasn't provided.
- Never say things like "you're financially irresponsible" or "you have no self-control" or \
anything shaming. Frame things in terms of the actual numbers instead, e.g. "this eats 56% of \
your remaining fun budget" rather than judging the person.
- Keep it short and fun, like a text from a friend, not a lecture.
- If the verdict is BUY, be genuinely encouraging - don't manufacture a problem that isn't there.
"""

_VERDICT_FALLBACK_HEADLINES = {
    "BUY": "Looks fine, go for it.",
    "WAIT": "Maybe sit on this one.",
    "DONT_BUY": "Gonna have to say no on this one.",
}


def _fallback_explanation(decision: dict) -> dict:
    """A plain, deterministic message built straight from the decision's own reasons.

    Used whenever the AI isn't available - keeps the result screen honest
    and functional without ever depending on a live API call.
    """
    reasons_text = "; ".join(decision["reasons"])
    closing = "Enjoy it!" if decision["verdict"] == "BUY" else "Take a beat before you decide."
    return {
        "headline": _VERDICT_FALLBACK_HEADLINES[decision["verdict"]],
        "commentary": f"Here's why: {reasons_text}.",
        "closing_line": closing,
        "ai_generated": False,
    }


def explain(decision: dict) -> dict:
    """Generate a Gen-Z explanation for a decision engine result. Always returns a usable dict."""
    if not is_configured():
        return _fallback_explanation(decision)
    try:
        client = get_client()
        facts = {
            "verdict": decision["verdict"],
            "product_name": decision["product_name"],
            "purchase_price": decision["purchase_price"],
            "category": decision["category"],
            "remaining_discretionary_budget": decision["remaining_discretionary_budget"],
            "budget_percentage": decision["budget_percentage"],
            "category_spending_this_month": decision["category_spending"],
            "normal_category_spending": decision["normal_category_spending"],
            "recent_similar_purchases": decision["recent_similar_purchases"],
            "reasons": decision["reasons"],
        }
        response = client.models.generate_content(
            model=MODEL,
            contents=(
                "Here are the calculated facts about this purchase decision "
                f"(JSON): {json.dumps(facts)}\n\nWrite your reaction to it."
            ),
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_EXPLANATION_SCHEMA,
            ),
        )
        if not response.text:
            return _fallback_explanation(decision)
        result = json.loads(response.text)
        if not all(k in result for k in ("headline", "commentary", "closing_line")):
            return _fallback_explanation(decision)
        result["ai_generated"] = True
        return result
    except Exception:
        return _fallback_explanation(decision)
