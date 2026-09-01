"""
Product Understanding (Phase 5).

Uses the Gemini API for the two spots where natural-language/vision
intelligence actually earns its place: reading a screenshot, and
guessing a spending category from a free-text product name. Both force
a strict JSON schema on the response so the model returns clean
structured fields instead of prose the app would have to parse. Neither
function invents a price - it always comes from what's visible in the
screenshot or what the user typed, never from the model's imagination.

Both are optional. If no API key is configured, or a call fails for any
reason (bad image, network error, low-confidence read), the function
returns None and the caller falls back to manual entry / a manual
category dropdown. The rest of the app must keep working either way.
"""

import json
import sys
from pathlib import Path

from google.genai import types

from ai_client import MODEL, get_client, is_configured

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
from config import CATEGORY_LIST  # noqa: E402

_EXTRACT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "product_name": {"type": "STRING", "description": "Short product name/title"},
        "price": {
            "type": "NUMBER",
            "description": (
                "The price actually being charged, as a plain number with no currency "
                "symbol or thousands separators. Use the final/discounted price if shown."
            ),
        },
        "currency": {"type": "STRING", "description": "3-letter currency code, e.g. INR, USD"},
        "category": {
            "type": "STRING",
            "enum": CATEGORY_LIST,
            "description": "Best-fit spending category for this product",
        },
        "discount_percentage": {
            "type": "NUMBER",
            "description": "Discount percentage shown on the page. Use 0 if none is shown.",
        },
        "confident": {
            "type": "BOOLEAN",
            "description": (
                "False if this doesn't look like a real product/checkout screenshot, or "
                "the product name/price aren't clearly legible."
            ),
        },
    },
    "required": ["product_name", "price", "currency", "category", "discount_percentage", "confident"],
}

_CATEGORY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "category": {"type": "STRING", "enum": CATEGORY_LIST},
    },
    "required": ["category"],
}


def extract_from_screenshot(
    image_bytes: bytes, media_type: str = "image/png"
) -> tuple[dict | None, str | None]:
    """Read a product/checkout screenshot.

    Returns (fields, error). Exactly one is ever set. The error string is
    surfaced straight to the user - swallowing it silently made a wrong
    model name, a rejected key and an unreadable image all look identical.
    """
    if not is_configured():
        return None, "No GEMINI_API_KEY set."
    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                "Read this product or checkout screenshot and record its details.",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_EXTRACT_SCHEMA,
            ),
        )
        result = _parse_json(response)
        if not result:
            return None, "Gemini returned an empty response."
        if not result.get("confident", True):
            return None, "Couldn't make out a product name and price in that image."
        return {
            "product_name": str(result["product_name"]).strip(),
            "price": float(result["price"]),
            "currency": result.get("currency") or "INR",
            "category": result.get("category") if result.get("category") in CATEGORY_LIST else None,
            "discount_percentage": float(result.get("discount_percentage") or 0),
        }, None
    except Exception as exc:
        return None, f"{type(exc).__name__} (model '{MODEL}'): {exc}"


def categorize_product(product_name: str) -> tuple[str | None, str | None]:
    """Guess a spending category for a manually-typed product name.

    Returns (category, error), same convention as extract_from_screenshot.
    """
    if not is_configured():
        return None, "No GEMINI_API_KEY set."
    if not product_name.strip():
        return None, "No product name given."
    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Classify this product into a spending category: {product_name}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_CATEGORY_SCHEMA,
            ),
        )
        result = _parse_json(response)
        category = result.get("category") if result else None
        if category not in CATEGORY_LIST:
            return None, "Gemini didn't return a usable category."
        return category, None
    except Exception as exc:
        return None, f"{type(exc).__name__} (model '{MODEL}'): {exc}"


def _parse_json(response) -> dict | None:
    if not response.text:
        return None
    return json.loads(response.text)
