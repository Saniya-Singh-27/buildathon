"""
Should I Buy This? - Streamlit app entrypoint.

Phase 6 scope: the result screen now shows a real verdict. Product
input (screenshot or manual, Phase 5) feeds the Spending Analyzer
(Phase 3), which feeds the Decision Engine (Phase 4) for a plain,
explainable BUY/WAIT/DONT_BUY - the AI (Phase 6) only narrates that
already-made decision in a Gen-Z voice, using nothing but the numbers
the app calculated. No persistence or payment flow yet (Phase 7/8).
"""

import sys
from pathlib import Path

import streamlit as st

from ai_client import is_configured
from ai_explanation import explain
from data_loader import load_transactions, summary
from decision_engine import decide
from product_understanding import categorize_product, extract_from_screenshot
from spending_analyzer import analyze_purchase
from styles import CUSTOM_CSS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
from config import (  # noqa: E402
    CATEGORY_LABELS,
    CATEGORY_LIST,
    DISCRETIONARY_BUDGET,
    ESSENTIAL_CATEGORIES,
    MONTHLY_BUDGET,
    RECENT_WINDOW_DAYS,
)

st.set_page_config(page_title="Should I Buy This?", page_icon="💸", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

CATEGORY_PLACEHOLDER = "-- pick one --"
CATEGORY_OPTIONS = [CATEGORY_PLACEHOLDER] + CATEGORY_LIST

DEFAULTS = {
    "page": "home",
    "product_name": "",
    "price": 0.0,
    "category": None,
    "discount_percentage": 0.0,
    "product_name_input": "",
    "price_input": 0.0,
    "category_input": CATEGORY_PLACEHOLDER,
    "discount_input": 0.0,
    "screenshot_message": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go_to_result():
    st.session_state.page = "result"


def go_home():
    st.session_state.page = "home"
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def _analyze_screenshot():
    uploaded = st.session_state.get("screenshot_upload")
    if uploaded is None:
        st.session_state.screenshot_message = ("warning", "Upload an image first.")
        return
    if not (uploaded.type or "").startswith("image/"):
        st.session_state.screenshot_message = ("warning", "That doesn't look like an image file.")
        return
    if not is_configured():
        st.session_state.screenshot_message = (
            "warning",
            "AI screenshot reading isn't configured (no GEMINI_API_KEY set) - enter the details manually below.",
        )
        return

    result = extract_from_screenshot(uploaded.getvalue(), uploaded.type or "image/png")
    if result is None:
        st.session_state.screenshot_message = (
            "warning",
            "Couldn't confidently read that screenshot - enter the details manually below.",
        )
        return

    st.session_state.product_name_input = result["product_name"]
    st.session_state.price_input = result["price"]
    if result["category"] in CATEGORY_LIST:
        st.session_state.category_input = result["category"]
    st.session_state.discount_input = result.get("discount_percentage") or 0.0
    st.session_state.screenshot_message = (
        "success",
        "Got it - filled in the details below from your screenshot. Double check them before judging.",
    )


def render_home():
    st.markdown('<div class="big-title">SHOULD I BUY THIS?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Your brutally honest, secretly supportive money friend.</div>',
        unsafe_allow_html=True,
    )

    try:
        df = load_transactions()
        stats = summary(df)
        st.caption(
            f"Data check: {stats['transaction_count']} transactions loaded • "
            f"Rs {stats['total_spent']:,.0f} total spend • "
            f"Rs {stats['current_month_spend']:,.0f} spent this month"
        )
    except FileNotFoundError:
        st.warning("No transaction data found. Run `python3 data/generate_data.py` first.")

    with st.container(border=True):
        st.markdown("**Upload what you're about to buy**")
        st.file_uploader(
            "Screenshot of the product or checkout page",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="screenshot_upload",
        )
        st.button("Analyze Screenshot", on_click=_analyze_screenshot)

        level, text = st.session_state.screenshot_message or (None, None)
        if level == "success":
            st.success(text)
        elif level == "warning":
            st.warning(text)
        st.caption("Uses Gemini's vision model - falls back to manual entry if no API key is set.")

    st.markdown('<div class="or-divider">OR</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Enter it yourself**")
        st.text_input("Product", placeholder="e.g. Black blazer", key="product_name_input")
        st.number_input("Price (INR)", min_value=0.0, step=50.0, format="%.2f", key="price_input")
        st.selectbox(
            "Category",
            CATEGORY_OPTIONS,
            key="category_input",
            format_func=lambda c: CATEGORY_LABELS.get(c, c) if c != CATEGORY_PLACEHOLDER else c,
        )
        st.number_input(
            "Discount % (optional)", min_value=0.0, max_value=100.0, step=5.0, key="discount_input"
        )

        judge_clicked = st.button("JUDGE ME", type="primary", use_container_width=True)

        if judge_clicked:
            product_name = st.session_state.product_name_input.strip()
            price = st.session_state.price_input
            category = st.session_state.category_input

            if not product_name:
                st.warning("Tell me what you're buying first.")
            elif price <= 0:
                st.warning("That price can't be real. Try again.")
            else:
                if category == CATEGORY_PLACEHOLDER:
                    guessed = categorize_product(product_name)
                    category = guessed

                if category not in CATEGORY_LIST:
                    st.warning("Couldn't guess a category automatically - please pick one from the list.")
                else:
                    st.session_state.product_name = product_name
                    st.session_state.price = price
                    st.session_state.category = category
                    st.session_state.discount_percentage = st.session_state.discount_input
                    go_to_result()
                    st.rerun()


_VERDICT_DISPLAY = {
    "BUY": ("verdict-buy", "🟢", "BUY"),
    "WAIT": ("verdict-wait", "🟡", "WAIT"),
    "DONT_BUY": ("verdict-dontbuy", "🔴", "DON'T BUY"),
}


def render_result():
    df = load_transactions()
    analysis = analyze_purchase(
        df,
        category=st.session_state.category,
        purchase_price=st.session_state.price,
        monthly_budget=MONTHLY_BUDGET,
        discretionary_budget=DISCRETIONARY_BUDGET,
        essential_categories=ESSENTIAL_CATEGORIES,
        recent_window_days=RECENT_WINDOW_DAYS,
        product_name=st.session_state.product_name,
    )
    decision = decide(analysis)
    explanation = explain(decision)

    banner_class, banner_icon, banner_label = _VERDICT_DISPLAY[decision["verdict"]]

    if not explanation.get("ai_generated"):
        st.caption("AI commentary is running on a plain fallback right now (not talking to Gemini).")

    st.markdown(
        f'<div class="verdict-banner {banner_class}">{banner_icon} {banner_label}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="price-tag">{st.session_state.product_name} — '
        f'₹{st.session_state.price:,.2f}</div>',
        unsafe_allow_html=True,
    )
    category_label = CATEGORY_LABELS.get(st.session_state.category, st.session_state.category)
    discount = st.session_state.discount_percentage
    discount_text = f" • {discount:.0f}% off" if discount else ""
    st.caption(f"Category: {category_label}{discount_text}")

    st.markdown(f'<div class="ai-headline">{explanation["headline"]}</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Why I'm saying this:**")
        for reason in decision["reasons"]:
            st.markdown(f'<div class="reason-item">• {reason}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="bestie-note">"{explanation["commentary"]}"<br><br>'
        f'<strong>My move:</strong> {explanation["closing_line"]}</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.button("WAIT 72 HOURS", use_container_width=True, disabled=True)
    with col2:
        st.button("BUY ANYWAY 💀", use_container_width=True, disabled=True)
    st.caption("These buttons are disabled for now - saving your decision arrives in a later phase.")

    st.button("← Judge something else", on_click=go_home)


if st.session_state.page == "home":
    render_home()
else:
    render_result()
