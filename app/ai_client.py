"""
Shared Anthropic API client and model configuration.

One place that knows how to read the API key and which model to use for
which job, so product_understanding.py (Phase 5) and the explanation
layer (Phase 6) don't each reinvent this.

Reads the key from the ANTHROPIC_API_KEY environment variable (the
standard name the anthropic SDK looks for). If it isn't set, the AI
features are simply unavailable and callers fall back to manual entry -
nothing else in the app depends on this being configured.
"""

import os

import anthropic

# Vision needs a strong model to read a messy checkout screenshot reliably.
VISION_MODEL = "claude-sonnet-5"
# Categorizing a short product name and writing the verdict commentary
# don't need heavy reasoning - fast and cheap is fine here.
TEXT_MODEL = "claude-haiku-4-5-20251001"


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)
