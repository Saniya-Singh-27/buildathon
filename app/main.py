"""
Should I Buy This? - Streamlit app entrypoint.

Phase 7 scope: everything is now persisted in SQLite. Product input
(screenshot or manual, Phase 5) feeds the Spending Analyzer (Phase 3),
which feeds the Decision Engine (Phase 4) for a plain, explainable
BUY/WAIT/DONT_BUY - the AI (Phase 6) only narrates that already-made
decision, using nothing but the numbers the app calculated. Each
verdict and the user's response to it is written to the database and
survives a restart. Payment flow still to come (Phase 8).
"""

import sys
from pathlib import Path

import streamlit as st

import database
import payments
from ai_client import is_configured
from dashboard import render_dashboard
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
    USER_NAME,
)

st.set_page_config(page_title="Should I Buy This?", page_icon="💸", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

database.init_db(USER_NAME, MONTHLY_BUDGET, DISCRETIONARY_BUDGET)

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
    # Filled in once, when JUDGE ME is pressed - see judge_purchase().
    "decision": None,
    "explanation": None,
    "purchase_check_id": None,
    "user_decision": None,
    "checkout_order": None,
    "payment_result": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def judge_purchase(product_name: str, price: float, category: str, discount: float):
    """Run the full pipeline once and persist the verdict.

    Deliberately done here rather than in render_result(): Streamlit
    re-runs the whole script on every interaction, so analyzing and
    calling the AI from the render function meant a fresh Gemini call
    (and a duplicate database row) every time any button was clicked.
    """
    df = load_transactions()
    analysis = analyze_purchase(
        df,
        category=category,
        purchase_price=price,
        monthly_budget=MONTHLY_BUDGET,
        discretionary_budget=DISCRETIONARY_BUDGET,
        essential_categories=ESSENTIAL_CATEGORIES,
        recent_window_days=RECENT_WINDOW_DAYS,
        product_name=product_name,
    )
    decision = decide(analysis)

    st.session_state.product_name = product_name
    st.session_state.price = price
    st.session_state.category = category
    st.session_state.discount_percentage = discount
    st.session_state.decision = decision
    st.session_state.explanation = explain(decision)
    st.session_state.purchase_check_id = database.save_purchase_check(decision)
    st.session_state.user_decision = None
    st.session_state.page = "result"


def go_home():
    st.session_state.page = "home"
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def go_to_dashboard():
    st.session_state.page = "dashboard"


def render_nav():
    """Two-way nav between checking a purchase and the dashboard."""
    left, right = st.columns(2)
    on_dashboard = st.session_state.page == "dashboard"
    with left:
        st.button(
            "Should I buy this?",
            use_container_width=True,
            type="secondary" if on_dashboard else "primary",
            on_click=go_home,
        )
    with right:
        st.button(
            "My dashboard",
            use_container_width=True,
            type="primary" if on_dashboard else "secondary",
            on_click=go_to_dashboard,
        )


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

    result, error = extract_from_screenshot(uploaded.getvalue(), uploaded.type or "image/png")
    if result is None:
        st.session_state.screenshot_message = (
            "warning",
            f"Couldn't read that screenshot - enter the details manually below.\n\nReason: {error}",
        )
        return

    st.session_state.product_name_input = result["product_name"]
    st.session_state.price_input = result["price"]
    if result["category"] in CATEGORY_LIST:
        st.session_state.category_input = result["category"]
    st.session_state.discount_input = result.get("discount_percentage") or 0.0
    if result.get("confident", True):
        st.session_state.screenshot_message = (
            "success",
            "Got it - filled in the details below from your screenshot. "
            "Double check them before judging.",
        )
    else:
        st.session_state.screenshot_message = (
            "warning",
            "Read what I could from that screenshot, but it was a tricky one - "
            "please check the details below carefully before judging.",
        )


def render_home():
    st.markdown('<div class="big-title">SHOULD I BUY THIS?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Your brutally honest, secretly supportive money friend.</div>',
        unsafe_allow_html=True,
    )

    df = load_transactions()
    if df.empty:
        st.warning(
            "No transaction history in the database yet. "
            "Run `python3 data/generate_data.py` and restart the app to seed it."
        )
    else:
        stats = summary(df)
        checks_run = len(database.get_purchase_checks())
        st.caption(
            f"Data check: {stats['transaction_count']} transactions loaded • "
            f"Rs {stats['total_spent']:,.0f} total spend • "
            f"Rs {stats['current_month_spend']:,.0f} spent this month • "
            f"{checks_run} past verdicts saved"
        )

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
                category_error = None
                if category == CATEGORY_PLACEHOLDER:
                    category, category_error = categorize_product(product_name)

                if category not in CATEGORY_LIST:
                    st.warning(
                        "Couldn't guess a category automatically - please pick one from the list."
                        + (f"\n\nReason: {category_error}" if category_error else "")
                    )
                else:
                    with st.spinner("crunching your spending history..."):
                        judge_purchase(
                            product_name, price, category, st.session_state.discount_input
                        )
                    st.rerun()


_VERDICT_DISPLAY = {
    "BUY": ("verdict-buy", "🟢", "BUY"),
    "WAIT": ("verdict-wait", "🟡", "WAIT"),
    "DONT_BUY": ("verdict-dontbuy", "🔴", "DON'T BUY"),
}


def _record_decision(user_decision: str):
    """Persist what the user chose to do about the verdict."""
    if st.session_state.purchase_check_id is not None:
        database.record_user_decision(st.session_state.purchase_check_id, user_decision)
    st.session_state.user_decision = user_decision
    if user_decision == "bought_anyway":
        st.session_state.checkout_order = payments.create_order(
            st.session_state.price, receipt=f"check_{st.session_state.purchase_check_id}"
        )
        st.session_state.payment_result = None
    else:
        st.session_state.checkout_order = None
        st.session_state.payment_result = None


def _pay_with_test_card(card: payments.TestCard):
    """Run the simulated checkout and record the outcome, success or failure."""
    order = st.session_state.checkout_order
    if order is None:
        return
    result = payments.capture_payment(order, card)
    database.save_payment(
        purchase_check_id=st.session_state.purchase_check_id,
        amount=result["amount_rupees"],
        status=result["status"],
        reference=result["id"],
    )
    st.session_state.payment_result = result


def render_checkout():
    """The simulated Razorpay test checkout, shown after 'buy anyway'."""
    order = st.session_state.checkout_order
    result = st.session_state.payment_result

    with st.container(border=True):
        st.markdown(
            '<span class="test-badge">TEST MODE — SIMULATED, NO REAL MONEY MOVES</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"**Checkout — ₹{order['amount_rupees']:,.2f}**")
        st.caption(f"Order {order['id']} · {order['amount']} paise · {order['currency']}")

        if result is None:
            st.markdown("Pick a test card to simulate the outcome:")
            for card in payments.TEST_CARDS:
                cols = st.columns([3, 2])
                with cols[0]:
                    st.markdown(f"`{card.number}`")
                    st.caption(card.note)
                with cols[1]:
                    st.button(
                        f"Pay (TEST) — {card.label}",
                        key=f"pay_{card.outcome}",
                        use_container_width=True,
                        on_click=_pay_with_test_card,
                        args=(card,),
                    )
        elif result["status"] == "captured":
            st.success(
                f"Test payment captured — {result['id']} · card ending {result['card_last4']}. "
                "Simulated only, nothing was actually charged."
            )
            st.caption("Recorded against this purchase check in the payments table.")
        else:
            st.error(
                f"Test payment failed — {result['error_description']} "
                f"(reference {result['id']})."
            )
            st.button("Try a different test card", on_click=_reset_payment)


def _reset_payment():
    st.session_state.payment_result = None


def render_result():
    decision = st.session_state.decision
    explanation = st.session_state.explanation
    if decision is None or explanation is None:
        st.warning("Nothing to show yet - judge something first.")
        st.button("← Back", on_click=go_home)
        return

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
        st.button(
            "WAIT 72 HOURS",
            use_container_width=True,
            on_click=_record_decision,
            args=("waited",),
        )
    with col2:
        st.button(
            "BUY ANYWAY 💀",
            use_container_width=True,
            on_click=_record_decision,
            args=("bought_anyway",),
        )

    if st.session_state.user_decision == "waited":
        st.success("logged it. we'll see if you still want it in 72 hours.")
    elif st.session_state.user_decision == "bought_anyway":
        st.info("noted, no judgement. your money, your era.")

    if st.session_state.checkout_order is not None:
        render_checkout()

    st.caption(f"Saved to your history as check #{st.session_state.purchase_check_id}.")
    st.button("← Judge something else", on_click=go_home)


render_nav()

if st.session_state.page == "dashboard":
    render_dashboard(
        monthly_budget=MONTHLY_BUDGET,
        discretionary_budget=DISCRETIONARY_BUDGET,
        essential_categories=ESSENTIAL_CATEGORIES,
        category_labels=CATEGORY_LABELS,
    )
elif st.session_state.page == "home":
    render_home()
else:
    render_result()
