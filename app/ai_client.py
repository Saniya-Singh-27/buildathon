"""
Shared Gemini API client and model configuration.

One place that knows how to read the API key and which model to use,
so product_understanding.py (Phase 5) and the explanation layer
(Phase 6) don't each reinvent this.

Reads the key from the GEMINI_API_KEY environment variable - either
already exported in the shell, or loaded here from a .env file in the
project root. If it isn't set, the AI features are simply unavailable
and callers fall back to manual entry - nothing else in the app depends
on this being configured.

Get a free key at https://aistudio.google.com/apikey (Google AI Studio
has a free tier, no card required).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# Flash is fast, cheap (free-tier friendly), and multimodal - plenty for
# reading a screenshot or picking a category. No need for a heavier model.
# Overridable via GEMINI_MODEL so a model being renamed/retired on
# Google's side is a one-line .env fix, not a code change.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def is_configured() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)
