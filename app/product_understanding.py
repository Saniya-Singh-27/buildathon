"""
Product Understanding (Phase 5).

Uses the Anthropic API for the two spots where natural-language/vision
intelligence actually earns its place: reading a screenshot, and
guessing a spending category from a free-text product name. Both use
forced tool-use so the model returns clean structured fields instead of
prose the app would have to parse. Neither function invents a price -
it always comes from what's visible in the screenshot or what the user
typed, never from the model's imagination.

Both are optional. If no API key is configured, or a call fails for any
reason (bad image, network error, low-confidence read), the function
returns None and the caller falls back to manual entry / a manual
category dropdown. The rest of the app must keep working either way.
"""

import base64
import sys
from pathlib import Path

from ai_client import TEXT_MODEL, VISION_MODEL, get_client, is_configured

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
from config import CATEGORY_LIST  # noqa: E402

_EXTRACT_TOOL = {
    "name": "record_product",
    "description": "Record the product details read from a screenshot of a product or checkout page.",
    "input_schema": {
        "type": "object",
        "properties": {
            "product_name": {"type": "string", "description": "Short product name/title"},
            "price": {
                "type": "number",
                "description": (
                    "The price actually being charged, as a plain number with no currency "
                    "symbol or thousands separators. Use the final/discounted price if shown."
                ),
            },
            "currency": {"type": "string", "description": "3-letter currency code, e.g. INR, USD"},
            "category": {
                "type": "string",
                "enum": CATEGORY_LIST,
                "description": "Best-fit spending category for this product",
            },
            "discount_percentage": {
                "type": "number",
                "description": "Discount percentage shown on the page. Use 0 if none is shown.",
            },
            "confident": {
                "type": "boolean",
                "description": (
                    "False if this doesn't look like a real product/checkout screenshot, or "
                    "the product name/price aren't clearly legible."
                ),
            },
        },
        "required": ["product_name", "price", "currency", "category", "discount_percentage", "confident"],
    },
}

_CATEGORY_TOOL = {
    "name": "record_category",
    "description": "Classify a product into exactly one spending category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": CATEGORY_LIST},
        },
        "required": ["category"],
    },
}


def _first_tool_input(response) -> dict | None:
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return None


def extract_from_screenshot(image_bytes: bytes, media_type: str = "image/png") -> dict | None:
    """Read a product/checkout screenshot. Returns a dict of fields, or None if unusable."""
    if not is_configured():
        return None
    try:
        client = get_client()
        encoded = base64.standard_b64encode(image_bytes).decode("utf-8")
        response = client.messages.create(
            model=VISION_MODEL,
            max_tokens=500,
            tools=[_EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "record_product"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": encoded},
                        },
                        {
                            "type": "text",
                            "text": "Read this product or checkout screenshot and record its details.",
                        },
                    ],
                }
            ],
        )
        result = _first_tool_input(response)
        if not result or not result.get("confident", True):
            return None
        return {
            "product_name": str(result["product_name"]).strip(),
            "price": float(result["price"]),
            "currency": result.get("currency") or "INR",
            "category": result.get("category") if result.get("category") in CATEGORY_LIST else None,
            "discount_percentage": float(result.get("discount_percentage") or 0),
        }
    except Exception:
        return None


def categorize_product(product_name: str) -> str | None:
    """Guess a spending category for a manually-typed product name. Returns None if unavailable."""
    if not is_configured() or not product_name.strip():
        return None
    try:
        client = get_client()
        response = client.messages.create(
            model=TEXT_MODEL,
            max_tokens=100,
            tools=[_CATEGORY_TOOL],
            tool_choice={"type": "tool", "name": "record_category"},
            messages=[
                {"role": "user", "content": f"Classify this product into a spending category: {product_name}"}
            ],
        )
        result = _first_tool_input(response)
        category = result.get("category") if result else None
        return category if category in CATEGORY_LIST else None
    except Exception:
        return None
