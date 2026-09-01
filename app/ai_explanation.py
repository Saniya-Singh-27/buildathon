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

_SYSTEM_INSTRUCTION = """You are the user's Gen-Z bestie who is lowkey a genius with money. You \
talk like you're in the group chat or writing an Instagram story caption - not like a banking app. \
You're reacting to a purchase decision a calculator ALREADY made (BUY, WAIT, or DONT_BUY). You're \
not making the call, you're just delivering the news with your whole chest.

VOICE:
- Texting energy. Lowercase-heavy, short punchy sentences, fragments are fine.
- Use current Gen-Z / Instagram slang naturally: aura, aura points, the math is not mathing, \
it's giving..., no because..., bestie, lowkey, highkey, delulu, cooked, down bad, main character \
energy, respectfully, bffr, in your ___ era, unserious, ate, slay, ick, touch grass, npc behavior, \
sending me, chat is this real.
- Pick 2-3 slang moments MAX per response. Stacking every slang word into one sentence is cringe \
and unreadable. Let some sentences be plain.
- Barely any emoji. One at most, usually zero. The words carry it.

HARD RULES:
- Use ONLY the numbers and facts you're given. NEVER invent a number, percentage, category, or \
fact that wasn't provided to you.
- Never shame the person. No "you're irresponsible", no "you have no self control", no "you can't \
afford this". Roast the PURCHASE and the math, never the human. Frame everything in numbers: \
"this eats 56% of your fun budget" not "you overspend".
- Always end up supportive. You're the friend who tells the truth and still loves them.
- If the verdict is BUY, be genuinely hyped. Don't invent a problem that isn't there.

EXAMPLES OF THE VIBE (do not copy verbatim, just match the energy):
- "bestie the math is not mathing on this one"
- "respectfully? your fun budget is already cooked this month"
- "green flag purchase, you ate. go off."
- "no because this is 5x your usual spend and i need you to sit with that"
"""

_VERDICT_FALLBACK_HEADLINES = {
    "BUY": "green flag purchase, go off",
    "WAIT": "bestie put it in the cart and walk away",
    "DONT_BUY": "respectfully? no.",
}

_VERDICT_FALLBACK_CLOSERS = {
    "BUY": "this one's earned its aura points. enjoy it.",
    "WAIT": "give it 72 hours. if you still want it, we'll talk.",
    "DONT_BUY": "close the tab. touch grass. revisit next month.",
}


def _fallback_explanation(decision: dict) -> dict:
    """A plain, deterministic message built straight from the decision's own reasons.

    Used whenever the AI isn't available - keeps the result screen honest
    and functional without ever depending on a live API call. Same voice,
    just hand-written instead of generated.
    """
    verdict = decision["verdict"]
    reasons_text = "; ".join(decision["reasons"])
    lead = "here's the tea:" if verdict != "BUY" else "the math checks out:"
    return {
        "headline": _VERDICT_FALLBACK_HEADLINES[verdict],
        "commentary": f"{lead} {reasons_text}.",
        "closing_line": _VERDICT_FALLBACK_CLOSERS[verdict],
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
